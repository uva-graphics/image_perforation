#!/usr/bin/python

"""
Connelly ga implementation

Use "python ga.py stop_motion ~/Desktop/test -training_images_directory ../stop_motion/input/" for when we are running the GA for stop_motion   
"""

import sys; sys.path += ['../visualize_results', '../solver', '../compiler']
from parse_args import parse_args
import random
import copy
import collections
import approx
import os
import visualize_results
import visualize_remotely
import shutil
import time
import pickle
import ntpath
from collect_pareto import get_pareto

inf = float('inf')
FINAL_GENERATION_INDEX = 100000
TABLET_IP = '172.27.99.135'
TABLET_INPUT_IMAGES_DIRECTORY = '/home/phablet/code/filter-approx/proj/visualize_results/input/'

def list_dir_abs(basepath):
    return map(lambda x: os.path.join(basepath, x), os.listdir(basepath))

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

curve_area_alpha = 0.5

sample_importance_more = True        # Sample importance sampling (and grid sampling) more often

if sample_importance_more:
    prob_sample_for = 0.2            # Lower probability for sampling For() loops -- we are exploring ForEach() primarily
else:
    prob_sample_for = 1.0

def usage():
    print >> sys.stderr, 'python ga.py program_name result_dir'
    print >> sys.stderr, '  [-population_size n] [-generations n]'
    print >> sys.stderr, '  [-frac_elitism f] [-frac_mutate f] [-tournament_size n]'
    print >> sys.stderr, '  [-prob_modify_consts p] [-finalize_only b] [-finalize_filter str]'
    print >> sys.stderr, '  [-loop_perf_only b] [-run_remotely_on_tablet b]'
    print >> sys.stderr, '  [-training_images_directory str] [-cross_validation_directory str]'
    print >> sys.stderr, '  [-resume_previous_search b]'
    print >> sys.stderr, '  [-sample_importance_only b] [-sample_grid_only b]'
    print >> sys.stderr, '  [-run_on_fir b]'
    print >> sys.stderr, '  [-init_pop code_in_hex] [-run_final_generation]'
    print >> sys.stderr, '  [-use_adaptive b] [-reconstruct_hints b] [-reduce_space b]'
    sys.exit(1)

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

Gene = collections.namedtuple('Gene', 'fmt loop params'.split())

class Genome(list):
    def __init__(self, L=[], error=None, time=None):
        list.__init__(self, L)
        self.error = error
        self.time = time

    def __str__(self):
        ans = ''
        for x in self:
            d = {'loop': x.loop}
            for i in range(len(x.params)):
                d['p%d'%i] = x.params[i].value
            ans += x.fmt % d + '\n'
        return ans.strip('\n')
    
    def __repr__(self):
        return 'Genome(%r, error=%r, time=%r)' % (list(self), self.error, self.time)

delta_frac = 0.1

class FloatParam:
    def __init__(self, min, max, value=None):
        self.min = min
        self.max = max
        self.value = value
        
    def mutate(self, loop, restart=False):
        if not hasattr(self, 'value') or restart or self.value is None:
            self.value = random.uniform(self.min, self.max)
        else:
            delta = (self.max-self.min)*delta_frac
            a = max(self.min, self.value-delta)
            b = min(self.max, self.value+delta)
            self.value = random.uniform(a, b)

    def __repr__(self):
        return 'FloatParam(%f, %f, %f)' % (self.min, self.max, self.value)
        
class DiscreteParam(list):
    def __init__(self, L, value=None):
        list.__init__(self, L)
        self.value = value
        
    def mutate(self, loop, restart=False):
        self.value = random.choice(self)

    def __repr__(self):
        return 'DiscreteParam(%r, %r)' % (list(self), self.value)
        
#valid_spacings = [1, 2, 3, 4]
valid_spacings = [1, 2, 4, 8]

class SpacingParam:
    def __init__(self, value=None):
        self.value = value
        
    def mutate(self, loop, restart=False):
        try:
            dims = loop.dimensions()
        except AttributeError:
            dims = 0
        if not hasattr(self, 'value') or restart or self.value is None:
            self.value = [random.choice(valid_spacings) for i in range(dims)]
        else:
            i = random.randrange(dims)
            self.value[i] = random.choice(valid_spacings)

    def __repr__(self):
        return 'SpacingParam(%r)' % self.value
        
frac_param                       = FloatParam(0.025, 0.95)
importance_arg_param             = FloatParam(1.0/150.0, 1.0/32.0)
channels_param                   = DiscreteParam([1] + [None]*3)
reconstruct_non_varying_param    = DiscreteParam(['reconstruct_gaussian', 'reconstruct_nearest'])
reconstruct_param                = DiscreteParam(['reconstruct_gaussian', 'reconstruct_gaussian_sv', 'reconstruct_nearest'])
sigma_param                      = FloatParam(0.25, 3.0)
adaptive_grid_size_param         = DiscreteParam([2] * 3 + [3, 4])

foreach_lines = []
for_lines = []

def set_sample_lines(p):
    if p.reconstruct_hints:
        foreach_lines.extend([
            ('%(loop)s.sample_importance(frac=%(p0)f, importance_args=(%(p1)f,), channels=%(p2)r); %(loop)s.reconstruct_store(reconstruct_func=reconstruct_gaussian_sv, sigma=0.73)',
             [frac_param, importance_arg_param, channels_param]),

            ('%(loop)s.sample_grid(spacing=%(p0)r, channels=%(p1)r); %(loop)s.reconstruct_store(reconstruct_func=%(p2)s, sigma=0.3)',
             [SpacingParam(), channels_param, reconstruct_non_varying_param]),

            ('%(loop)s.sample_grid(spacing=%(p0)r, channels=%(p1)r); %(loop)s.reconstruct_compute()',
             [SpacingParam(), channels_param])])
    else:
        foreach_lines.extend([
            ('%(loop)s.sample_importance(frac=%(p0)f, importance_args=(%(p1)f,), channels=%(p2)r); %(loop)s.reconstruct_store(reconstruct_func=%(p3)s, sigma=%(p4)f)',
             [frac_param, importance_arg_param, channels_param, reconstruct_param, sigma_param]),

            ('%(loop)s.sample_grid(spacing=%(p0)r, channels=%(p1)r); %(loop)s.reconstruct_store(reconstruct_func=%(p2)s, sigma=%(p3)f)',
             [SpacingParam(), channels_param, reconstruct_param, sigma_param]),

            ('%(loop)s.sample_grid(spacing=%(p0)r, channels=%(p1)r); %(loop)s.reconstruct_compute()',
             [SpacingParam(), channels_param])])

    if p.use_adaptive:
        if p.reconstruct_hints:
            foreach_lines.append(('%(loop)s.sample_adaptive(frac=%(p0)f, adaptive_grid_size=%(p1)d); %(loop)s.reconstruct_store(reconstruct_func=reconstruct_gaussian_sv, sigma=0.9)',
                                  [frac_param, adaptive_grid_size_param]))
        else:
            foreach_lines.append(('%(loop)s.sample_adaptive(frac=%(p0)f, adaptive_grid_size=%(p1)d); %(loop)s.reconstruct_store(reconstruct_func=reconstruct_gaussian_sv, sigma=%(p2)f)',
                                  [frac_param, adaptive_grid_size_param, sigma_param]))

    for_lines.extend([
        ('%(loop)s.sample_contiguous(%(p0)f)', [FloatParam(-1.0, 1.0)]),
        ('%(loop)s.sample_step(%(p0)d)',       [DiscreteParam([1, 2, 3, 4, 8, 16])]),
        ('%(loop)s.sample_random(%(p0)f)',     [FloatParam(0.025, 0.95)])
         ])

    if sample_importance_more:
        foreach_lines.extend([
            # Expose sample_importance() variants with various numbers of parameters
            ('%(loop)s.sample_importance(frac=%(p0)f); %(loop)s.reconstruct_store(reconstruct_func=%(p1)s)',
             [frac_param, reconstruct_param]),

            ('%(loop)s.sample_importance(frac=%(p0)f); %(loop)s.reconstruct_store(reconstruct_func=%(p1)s, sigma=%(p2)f)',
             [frac_param, reconstruct_param, sigma_param])
        ])
    
def mutate(p, L):
    def random_gene_from_loop(loop_name):
        loop_obj = p.loops[loop_name]
        is_foreach = isinstance(loop_obj, approx.ForEach) and not p.loop_perf_only
        chosen = random.choice(foreach_lines if is_foreach else for_lines)
        ans = Gene(loop=loop_name, fmt=chosen[0], params=copy.deepcopy(chosen[1]))
        for x in ans.params:
            x.mutate(loop_obj, True)
        return ans
        
    L = copy.deepcopy(L)
    L.error = L.time = None
    if random.random() < p.prob_modify_consts and len(L) > 0:            # Modify consts
        i = random.randrange(len(L))
        j = random.randrange(len(L[i].params))
        L[i].params[j].mutate(p.loops[L[i].loop], False)
    else:
        mode = random.randrange(3)
        if len(L) == 0 or (mode == 0 and len(L) < len(p.loops)):         # Add
            while True:
                loop_name = random.choice(list(set(p.loops) - set([x.loop for x in L])))
                loop_obj = p.loops[loop_name]
                if isinstance(loop_obj, approx.ForEach):
                    break
                elif isinstance(loop_obj, approx.For) and random.random() < prob_sample_for:
                    break
            L.append(random_gene_from_loop(loop_name))
        elif mode == 1 and len(L) > 0:                                   # Remove
            i = random.randrange(len(L))
            del L[i]
        else:                                                            # Edit
            i = random.randrange(len(L))
            L[i] = random_gene_from_loop(L[i].loop)

    return L

def crossover(p, a, b):
    """Two-point crossover of two genomes."""
    if random.random() < 0.5:
        (a, b) = (b, a)

    keys = p.loops
    ib_lo = random.randrange(len(keys))
    ib_hi = random.randrange(ib_lo, len(keys))
    if ib_lo == 0 and ib_hi == len(keys)-1:
        ib_lo += 1

    ans = Genome()

    def get_gene_by_name(indiv, key):
        for gene in indiv:
            if gene.loop == key:
                return copy.deepcopy(gene)
        raise KeyError
        
    for (i, key) in enumerate(keys):
        try:
            ans.append(get_gene_by_name(b if (i >= ib_lo and i <= ib_hi) else a, key))
        except KeyError:
            pass
    return ans
        
def initial_population(p):
    """A population consists of genomes which are lists of Gene. Get an initial population."""
#    ans = []
    ans = p.all_rank0
    while len(ans) < p.population_size:
        current = mutate(p, Genome())
        if str(current) not in p.seen:
            ans.append(current)
            p.seen.add(str(current))
    return ans

def get_pareto_rank(pop):
    idx_pop = [(i, pop[i]) for i in range(len(pop))]
    rank = [None for x in range(len(pop))]

    current_rank = 0    
    while len(idx_pop):
        errorL = [x[1].error for x in idx_pop]
        timeL = [x[1].time for x in idx_pop]
        pareto_i = get_pareto(errorL, timeL)
        
        for i in pareto_i:
            rank[idx_pop[i][0]] = current_rank
        current_rank += 1
        pareto_i = set(pareto_i)
        idx_pop = [x for (i, x) in enumerate(idx_pop) if i not in pareto_i]
    
    assert all([isinstance(x, int) for x in rank])
    return rank
    
def next_generation(p, pop):
    ans = []
    rank = get_pareto_rank(pop)
    i_sorted = sorted([i for i in range(len(pop))], key=lambda i: rank[i])
#    print 'sorted by rank:', [rank[i] for i in i_sorted]
    
    def tournament_select():
        subL = random.sample(range(len(pop)), min(p.tournament_size, len(pop)))
        min_i = subL[0]
        for idx in subL:
            if rank[idx] < rank[min_i]:
                min_i = idx
        return pop[min_i]
        
    def add_if_valid(f):
        current = f()
        if str(current) not in p.seen:
            p.seen.add(str(current))
            ans.append(current)

    for i in range(int(p.population_size*p.frac_elitism)):    # Elitism
        ans.append(pop[i_sorted[i]])

    count= 0
    while len(ans) < int(p.population_size*(p.frac_elitism+p.frac_mutate)):    # Mutate
#        print '  next_generation: mutate %d' % len(ans)
        sys.stdout.flush()
        add_if_valid(lambda: mutate(p, tournament_select()))
        count += 1
        if count > p.population_size*50:
            add_if_valid(lambda: mutate(p, Genome()))

    count = 0
    while len(ans) < p.population_size:                       # Crossover
#        print '  next_generation: crossover %d' % len(ans)
        sys.stdout.flush()
        add_if_valid(lambda: crossover(p, tournament_select(), tournament_select()))
        count += 1
        if count > p.population_size*50:
            # If crossover fails try mutated crossover or mutate
            if random.random() < 0.5:
                add_if_valid(lambda: mutate(p, crossover(p, tournament_select(), tournament_select())))
            else:
                add_if_valid(lambda: mutate(p, Genome()))
        
    return ans
    
def makedirs(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)

def individual_filename(i):
    return 'indiv%03d.approx' % i
    
def get_time_error(p, pop, generation, skip_measured=True):
    dirname = os.path.join(p.result_dir, 'gen%06d' % generation)
    makedirs(dirname)
    vis_dirname = os.path.join(dirname, 'visualize')
    makedirs(vis_dirname)
    
    approx_list = []
    indiv_list = []
    
    for (i, indiv) in enumerate(pop):
        filename = os.path.join(dirname, individual_filename(i))
        if not (skip_measured and indiv.time is not None):
            approx_list.append(filename)
            indiv_list.append(indiv)
        with open(filename, 'wt') as f:
            f.write(str(indiv))
    
    # store the current generation in current_gen.py before we get the time and error (in case an exception takes place while we are getting the time and error)
    with open(os.path.join(dirname, 'current_gen.py'), 'wt') as f:
        f.write('current_gen = ' + repr(indiv_list))
    
    if generation == FINAL_GENERATION_INDEX:
        images_to_train_on = p['cross_validation_directory']
    else:
        images_to_train_on = p['training_images_directory']
    
    if (p['run_remotely_on_tablet']):
        vis = visualize_remotely.visualize_remotely(dirname,approx_list,p.program_name,'./', TABLET_IP)
    else:
        vis = visualize_results.visualize_results(approx_list, vis_dirname, p.program_name, open_html=False, dump_ans=False, input_images_directory=images_to_train_on, debug_log_location=dirname, run_on_fir=p['run_on_fir'])
    
    assert len(vis) == len(approx_list), '\n'+('-'*65)+"\nvis\n"+str(vis)+'\n'+('-'*65)+"\napprox_list\n"+str(approx_list)+'\n'+('-'*65)
    
#    print '*'*88    
#    print vis
#    print '*'*88
    
    for i in range(len(vis)):
        indiv_list[i].error = vis[i]['error']
        indiv_list[i].time = 0
        for key in vis[i].keys():
            if '_time' in key:
                indiv_list[i].time += float(vis[i][key])
    
    # store the current generation in current_gen.py once we have values for the time and error
    with open(os.path.join(dirname, 'current_gen.py'), 'wt') as f:
        f.write('current_gen = ' + repr(indiv_list))

def reduce_space_generation(p, pop, generation):
    dirname = os.path.join(p.result_dir, 'gen%06d' % generation)

    for (root, dirnames, filenames) in os.walk(dirname):
        for filename in filenames:
            full_filename = os.path.join(root, filename)
            if os.path.splitext(full_filename)[1].lower() == '.png':
                os.remove(full_filename)


def print_population(pop):
    print '-'*72
    print 'Population:'
    print '-'*72
    print

    rank = get_pareto_rank(pop)

    for i in range(len(pop)):
        print '%-20s Time=%6.2f (sec),  Error=%6.2f,  Rank=%-4d' % (individual_filename(i), pop[i].time, pop[i].error, rank[i])

    print
    
def track_rank0(p, pop):
    #rank = get_pareto_rank(pop)
    for i in range(len(pop)):
        #if rank[i] == 0:
        p.all_rank0.append(pop[i])
    with open(os.path.join(p.result_dir, 'rank0.py'), 'wt') as f:
        f.write('rank0 = ' + repr(p.all_rank0))

def profile_loops(program_name):
    loops = get_loops(program_name)
    lines = visualize_results.run_program(program_name, kw0={'profile_time': True, 'num_iters': 1})['_raw_out']
    ans = {}
    for loop in loops:
        ans[loop] = 0.0
        
    for line in lines.split('\n'):
        if 'loop time:' in line:
            try:
                (loop_name, _, _, time) = line.split()
                ok = True
            except:
                ok = False
            if ok and loop_name in ans:
                ans[loop_name] += float(time)
    return ans
            
def get_loops(program_name):
    exec """
import sys; sys.path += ['../%s']
import %s
ans = %s.approx_loops
(program, locals_d) = %s.create_program()
    """ % ((program_name,)*4) in locals(), locals()
    
    for key in ans:
        ans[key] = locals_d[key]
    return ans

def print_generation(generation, msg=''):
    print '='*80
    print 'Generation %d%s' % (generation, msg)
    print '='*80
    print

def load_past_run(p):
    d = {}
    s = open(os.path.join(p.result_dir, 'rank0.py'), 'rt').read()
    exec s in globals(), d
    d['rank0'] = [indiv for indiv in d['rank0'] if p.finalize_filter in str(indiv)]
    p.all_rank0 = d['rank0']

def main():
    (args, kw) = parse_args('population_size generations frac_elitism frac_mutate prob_modify_consts tournament_size finalize_only finalize_filter loop_perf_only run_remotely_on_tablet training_images_directory cross_validation_directory resume_previous_search sample_importance_only sample_grid_only run_on_fir init_pop run_final_generation use_adaptive reconstruct_hints reduce_space'.split(), usage)
    if len(args) < 2:
        usage()
    
    program_name = args[0]
    result_dir = args[1]
    makedirs(result_dir)
    
    start_gen_index = 0
    
    d = {}
    exec "init_pop = "+kw.get('init_pop', '[]'.encode('hex')).decode('hex') in globals(), d
    init_pop = d['init_pop']
    pop_size0 = int(kw.get('population_size', '30'))
    if len(init_pop) > pop_size0: 
        random.shuffle(init_pop)
        init_pop = init_pop[:pop_size0]
    
    p = AttrDict(population_size=pop_size0,
                 generations=int(kw.get('generations', '25')),
                 frac_elitism=float(kw.get('frac_elitism', '0.3')),
                 frac_mutate=float(kw.get('frac_mutate', '0.3')),
                 tournament_size=int(kw.get('tournament_size', '8')),
                 loops=get_loops(program_name),
                 program_name=program_name,
                 result_dir=os.path.abspath(result_dir),
                 prob_modify_consts=0.3,
                 seen=set(),
                 all_rank0=init_pop,
                 finalize_only=int(kw.get('finalize_only', '0')),
                 finalize_filter=kw.get('finalize_filter', ''),
                 loop_perf_only=int(kw.get('loop_perf_only', '0')),
                 run_remotely_on_tablet=int(kw.get('run_remotely_on_tablet', '0')),
                 training_images_directory=kw.get('training_images_directory', os.path.abspath('./training_images/')),
                 cross_validation_directory=kw.get('cross_validation_directory', os.path.abspath('./training_images/')),
                 resume_previous_search=int(kw.get('resume_previous_search', '0')),
                 sample_importance_only=int(kw.get('sample_importance_only', '0')),
                 sample_grid_only=int(kw.get('sample_grid_only', '0')), 
                 run_on_fir=int(kw.get('run_on_fir', '0')), 
                 run_final_generation=int(kw.get('run_final_generation', '0')),
                 use_adaptive=int(kw.get('use_adaptive', '1')),
                 reconstruct_hints=int(kw.get('reconstruct_hints', '0')),
                 reduce_space=int(kw.get('reduce_space', '1')))

    set_sample_lines(p)

    print '\n\n'
    print 'Parameters:'
    print '    population_size:', p['population_size']
    print '    generations:', p['generations']
    print '    frac_elitism:', p['frac_elitism']
    print '    frac_mutate:', p['frac_mutate']
    print '    tournament_size:', p['tournament_size']
#    print '    loops:', p['loops']
    print '    program_name:', p['program_name']
    print '    result_dir:', p['result_dir']
    print '    prob_modify_consts:', p['prob_modify_consts']
    print '    seen:', p['seen']
    print '    finalize_only:', p['finalize_only']
    print '    finalize_filter:', p['finalize_filter']
    print '    loop_perf_only:', p['loop_perf_only']
    print '    run_remotely_on_tablet:', p['run_remotely_on_tablet']
    print '    training_images_directory:', p['training_images_directory']
    print '    cross_validation_directory:', p['cross_validation_directory']
    print '    resume_previous_search:', p['resume_previous_search']
    print '    sample_importance_only:', p['sample_importance_only']
    print '    sample_grid_only:', p['sample_grid_only']
    print '    run_on_fir:', p['run_on_fir']
    print '    run_final_generation:', p['run_final_generation']
    print '    use_adaptive:', p['use_adaptive']
    print '    reconstruct_hints:', p['reconstruct_hints']
    print '    reduce_space:', p['reduce_space']
    print '\n\n'
    
    if p['sample_importance_only'] and p['sample_grid_only']:
        print >> sys.stderr, 'Cannot have both sample_importance_only and sample_grid_only be true.'
        sys.exit(1)
    
    global foreach_lines
    if p['sample_importance_only']:
        new_foreach_lines = []
        for e in foreach_lines:
            if 'importance' in e[0]:
                new_foreach_lines.append(e)
        foreach_lines = new_foreach_lines
    
    if p['sample_grid_only']:
        new_foreach_lines = []
        for e in foreach_lines:
            if 'sample_grid(' in e[0]:
                new_foreach_lines.append(e)
        foreach_lines = new_foreach_lines
        
    if p['resume_previous_search']:
        gen_name_list = [ int(e[3:]) for e in os.listdir(result_dir) if 'gen' in e ]
        if 100000 in gen_name_list:
            print >> sys.stderr, 'Cannot resume previous search since previous search completed. Utilize the -finalize_only option instead.'
            sys.exit(1)
        start_gen_index = max(gen_name_list) if len(gen_name_list)>0 else 0
    
    if p['run_remotely_on_tablet']:
        print "Running timings remotely on the tablet."
        os.system("ssh phablet@"+TABLET_IP+" '(rm -rf "+TABLET_INPUT_IMAGES_DIRECTORY+")'")
        os.system("ssh phablet@"+TABLET_IP+" '(mkdir "+TABLET_INPUT_IMAGES_DIRECTORY+")'")
        os.system('scp '+p['training_images_directory']+'/*.png phablet@'+TABLET_IP+':'+TABLET_INPUT_IMAGES_DIRECTORY)
    
    curve_area_list = []
    
    if not p.finalize_only:
        if os.path.exists(result_dir) and not os.path.samefile(result_dir, '.') and not p['resume_previous_search']:
            shutil.rmtree(result_dir, ignore_errors=True)
        for generation in xrange(start_gen_index, p.generations):
            T0 = time.time()
            
            if generation == 0:
                pop = initial_population(p)
            elif generation == start_gen_index:
                # Update current generation
                gen_dirname = os.path.join(p.result_dir, 'gen%06d' % generation)
                d = {}
                s = open(os.path.join(gen_dirname, 'current_gen.py'), 'rt').read()
                exec s in globals(), d
                pop = d['current_gen']
                
#                if not p['run_on_fir']:
                if True:
                    # Make sure curve_area_list is updated
                    list_of_dirs_with_convergence_values = sorted([ f for f in list_dir_abs(p.result_dir) if 'gen' in path_leaf(f)], key=lambda x: int(path_leaf(x)[3:]))[:-1]
                    
                    for i,e in enumerate(list_of_dirs_with_convergence_values):        
                        curve_area_list.append( (i,float(open(os.path.join(e, 'pareto_over_all_approximations_so_far/area_under_pareto_frontier.txt'),'r').read())) )
                        
                        # Recalculate area_under_pareto_frontier_for_all_generations_so_far.csv for each generation in case we decided to change curve_area_alpha
                        current_generation_dirname = os.path.join(p.result_dir, 'gen%06d' % i)
                        current_generation_pareto_dirname = os.path.join(current_generation_dirname, 'pareto_over_all_approximations_so_far')
                        area_under_pareto_frontier_for_all_generations_so_far_csv_location = os.path.join(current_generation_pareto_dirname, 'area_under_pareto_frontier_for_all_generations_so_far.csv')
                        with open(area_under_pareto_frontier_for_all_generations_so_far_csv_location, 'wt') as f:
                            smoothed_curve_area_list = [ curve_area_list[0][1] ]
                            if len(curve_area_list)>1:
                                for i_0 in xrange(len(curve_area_list[1:])):
                                    i = i_0+1
                                    smoothed_curve_area_list.append( curve_area_alpha*curve_area_list[i][1] + (1-curve_area_alpha)*smoothed_curve_area_list[i-1] )
                            f.write('Generation, Area Under Curve, Smoothed Area Under Curve (alpha='+str(curve_area_alpha)+') \n')
                            for i,e in enumerate(curve_area_list):
                                f.write(str(e[0])+', '+str(e[1])+', '+str(smoothed_curve_area_list[i])+'\n')
                        # Graph area_under_pareto_frontier_for_all_generations_so_far.csv data for Area Under Curve and Smoothed Area Under Curve
                        commands = '''
set datafile separator ","
set title "Area Under Pareto Curve as Generations Pass"
set ylabel "Area Under Curve"
set xlabel "Generation"
#set ytic 0.1
#set xtic 1
set xr [0:*]
set yr [0:*]

set terminal png size 1200,900
'''
                        plot_command_area_under_curve = '"'+area_under_pareto_frontier_for_all_generations_so_far_csv_location+'" using 1:2 with linespoints title "Area Under Curve" '
                        plot_command_smoothed_area_under_curve = '"'+area_under_pareto_frontier_for_all_generations_so_far_csv_location+'" using 1:3 with linespoints title "Smoothed Area Under Curve" '
                        gnuplot_script_location = os.path.join(current_generation_pareto_dirname, 'script.gnuplot')
                        with open(gnuplot_script_location, 'wt') as f:
                            f.write( commands + '\nset output "area_under_curve.png" \n' + '\nplot '+ plot_command_area_under_curve + '\n')
                        os.system("(cd "+current_generation_pareto_dirname+" && cat "+gnuplot_script_location+" | gnuplot)")
                        with open(gnuplot_script_location, 'wt') as f:
                            f.write( commands + '\nset output "area_under_curve_smoothed.png" \n' + '\nplot '+ plot_command_smoothed_area_under_curve + '\n')
                        os.system("(cd "+current_generation_pareto_dirname+" && cat "+gnuplot_script_location+" | gnuplot)")
                        with open(gnuplot_script_location, 'wt') as f:
                            f.write( commands + '\nset output "area_under_curve_both.png" \n' + '\nplot '+ plot_command_area_under_curve + ', ' +plot_command_smoothed_area_under_curve + '\n')
                        os.system("(cd "+current_generation_pareto_dirname+" && cat "+gnuplot_script_location+" | gnuplot)")
                    assert len(curve_area_list) == start_gen_index, "Did not recompute curve_area_list correctly from .txt files"
                
                # Update p.all_rank0
                load_past_run(p)
            else:
                pop = next_generation(p, pop)
            
            print_generation(generation)
            print 'Generated new population'
            sys.stdout.flush()
            
            get_time_error(p, pop, generation)
            print_population(pop)
            track_rank0(p, pop)
            
            # Save Pareto frontier over all the approximations we've explored so far
            dirname = os.path.join(p.result_dir, 'gen%06d' % generation)
            makedirs(dirname)
            pareto_dirname = os.path.join(dirname, 'pareto_over_all_approximations_so_far')
            makedirs(pareto_dirname)
            pareto_frontier = [ p.all_rank0[i] for (i,rank) in enumerate(get_pareto_rank(p.all_rank0)) if rank==0 ] 
            pareto_values = []
            #if not p['run_on_fir']:
            f_pareto_csv = open(os.path.join(pareto_dirname,'pareto.csv'), 'wt')
            f_pareto_csv.write('Approx File, Time, Mean Lab \n')
            for (i,indiv) in enumerate(pareto_frontier):
                filename = os.path.join(pareto_dirname, individual_filename(i))
#                if not p['run_on_fir']:
                f_pareto_csv.write(individual_filename(i)+', '+str(indiv.time)+', '+str(indiv.error)+'\n')
                pareto_values.append((indiv.time,indiv.error))
                with open(filename, 'wt') as f_approx_file:
                    f_approx_file.write(str(indiv)) 
            with open(os.path.join(pareto_dirname,'pareto_so_far.py'), 'wt') as f:
                f.write('pareto_so_far = ' + repr(pareto_frontier))
#            if not p['run_on_fir']:
            f_pareto_csv.close()
#            if not p['run_on_fir']:
            if True:
                # Record current convergence
                CONVERGENCE_MEASURE_TIME_LOWER_BOUND = 0.6
                CONVERGENCE_MEASURE_TIME_UPPER_BOUND = 1.0
                TIME_INDEX = 0
                ERROR_INDEX = 1
                pareto_values_for_area = sorted(pareto_values, key=lambda x:x[TIME_INDEX])
                area_under_pareto_frontier = 0
                if CONVERGENCE_MEASURE_TIME_LOWER_BOUND < pareto_values_for_area[0][TIME_INDEX]:
                    area_under_pareto_frontier = float('inf')
                else:
                    # Clip the right hand side
                    while CONVERGENCE_MEASURE_TIME_UPPER_BOUND <= pareto_values_for_area[-1][TIME_INDEX]:
                        pareto_values_for_area.pop(-1)
                    pareto_values_for_area.append( (1.0,0.0) )
                    # Clip the left hand side
                    while CONVERGENCE_MEASURE_TIME_LOWER_BOUND >= pareto_values_for_area[1][TIME_INDEX]:
                        pareto_values_for_area.pop(0)
                    first_point = pareto_values_for_area[0]
                    second_point = pareto_values_for_area[1]
                    frac = (CONVERGENCE_MEASURE_TIME_LOWER_BOUND-first_point[TIME_INDEX])/(second_point[TIME_INDEX]-first_point[TIME_INDEX])
                    new_first_point = (first_point[TIME_INDEX]+frac*(second_point[TIME_INDEX]-first_point[TIME_INDEX]),first_point[ERROR_INDEX]+frac*(second_point[ERROR_INDEX]-first_point[ERROR_INDEX]))
                    pareto_values_for_area[0] = new_first_point
                    # Calculate area under curve
                    for i in xrange(len(pareto_values_for_area)-1):
                        point_a = pareto_values_for_area[i]
                        point_b = pareto_values_for_area[i+1]
                        area = 0.5*(point_a[ERROR_INDEX]+point_b[ERROR_INDEX])*(point_b[TIME_INDEX]-point_a[TIME_INDEX])
                        area_under_pareto_frontier += area
                print 'Area Under Pareto Frontier:', area_under_pareto_frontier, '\n'
                # Write pareto area into .txt file
                with open(os.path.join(pareto_dirname, 'area_under_pareto_frontier.txt'), 'wt') as f:
                    f.write(str(area_under_pareto_frontier))
                curve_area_list.append( (generation,area_under_pareto_frontier) )
                # Add pareto area into area_under_pareto_frontier_for_all_generations_so_far.csv
                area_under_pareto_frontier_for_all_generations_so_far_csv_location = os.path.join(pareto_dirname, 'area_under_pareto_frontier_for_all_generations_so_far.csv')
                with open(area_under_pareto_frontier_for_all_generations_so_far_csv_location, 'wt') as f:
                    smoothed_curve_area_list = [ curve_area_list[0][1] ]
                    if len(curve_area_list)>1:
                        for i_0 in xrange(len(curve_area_list[1:])):
                            i = i_0+1
                            smoothed_curve_area_list.append( curve_area_alpha*curve_area_list[i][1] + (1-curve_area_alpha)*smoothed_curve_area_list[i-1] )
                    f.write('Generation, Area Under Curve, Smoothed Area Under Curve (alpha='+str(curve_area_alpha)+') \n')
                    for i,e in enumerate(curve_area_list):
                        f.write(str(e[0])+', '+str(e[1])+', '+str(smoothed_curve_area_list[i])+'\n')
#            if not p['run_on_fir']: 
            if True:
                # Graph area_under_pareto_frontier_for_all_generations_so_far.csv data for Area Under Curve and Smoothed Area Under Curve
                commands = '''
set datafile separator ","
set title "Area Under Pareto Curve as Generations Pass"
set ylabel "Area Under Curve"
set xlabel "Generation"
#set ytic 0.1
#set xtic 1
set xr [0:*]
set yr [0:*]

set terminal png size 1200,900
'''
                plot_command_area_under_curve = '"'+area_under_pareto_frontier_for_all_generations_so_far_csv_location+'" using 1:2 with linespoints title "Area Under Curve" '
                plot_command_smoothed_area_under_curve = '"'+area_under_pareto_frontier_for_all_generations_so_far_csv_location+'" using 1:3 with linespoints title "Smoothed Area Under Curve" '
                gnuplot_script_location = os.path.join(pareto_dirname, 'script.gnuplot')
                with open(gnuplot_script_location, 'wt') as f:
                    f.write( commands + '\nset output "area_under_curve.png" \n' + '\nplot '+ plot_command_area_under_curve + '\n')
                os.system("(cd "+pareto_dirname+" && cat "+gnuplot_script_location+" | gnuplot)")
                with open(gnuplot_script_location, 'wt') as f:
                    f.write( commands + '\nset output "area_under_curve_smoothed.png" \n' + '\nplot '+ plot_command_smoothed_area_under_curve + '\n')
                os.system("(cd "+pareto_dirname+" && cat "+gnuplot_script_location+" | gnuplot)")
                with open(gnuplot_script_location, 'wt') as f:
                    f.write( commands + '\nset output "area_under_curve_both.png" \n' + '\nplot '+ plot_command_area_under_curve + ', ' +plot_command_smoothed_area_under_curve + '\n')
                os.system("(cd "+pareto_dirname+" && cat "+gnuplot_script_location+" | gnuplot)")
                
                # Copy rank0.py for each generation
                shutil.copyfile( os.path.join(p.result_dir, 'rank0.py') , os.path.join(dirname, 'rank0_gen%06d.py' % generation) )
            if p['reduce_space']:
                reduce_space_generation(p, pop, generation)

            print 'Tuning time for generation %d: %f secs' % (generation, time.time()-T0)
            print
            sys.stdout.flush()
    else:
        load_past_run(p)
    
    if p['run_final_generation']:
        generation = FINAL_GENERATION_INDEX
        print '='*80
        print 'Computing Time and Error on Cross Validation Images'
        print '='*80
        if (p['run_remotely_on_tablet']):
            os.system("ssh phablet@"+TABLET_IP+" '(rm -rf "+TABLET_INPUT_IMAGES_DIRECTORY+")'")
            os.system("ssh phablet@"+TABLET_IP+" '(mkdir "+TABLET_INPUT_IMAGES_DIRECTORY+")'")
            os.system('scp '+p['cross_validation_directory']+'/*.png phablet@'+TABLET_IP+':'+TABLET_INPUT_IMAGES_DIRECTORY)
    #    get_time_error(p, p.all_rank0, FINAL_GENERATION_INDEX, False) # uncomment this line if we want our GA to get the pareto frontier of all approximations explored by our search using our testing/cross validation images
        rank = get_pareto_rank(p.all_rank0)
        p.all_rank0 = [x for (i, x) in enumerate(p.all_rank0) if rank[i] == 0]
        p.all_rank0 = sorted(p.all_rank0, key=lambda x: x.error)
        print_generation(generation, ' (Pareto frontier over all generations, size is %d)' % len(p.all_rank0))
        get_time_error(p, p.all_rank0, FINAL_GENERATION_INDEX, False)
    print "\n\nGA complete."

if __name__ == '__main__':
    main()

