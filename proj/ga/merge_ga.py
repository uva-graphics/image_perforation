
'''

TODO:
    get functionality to start a ga with previously used data

'''
import sys; sys.path += ['../visualize_results']
import os
import sys
import subprocess
from ga import *

def get_containing_folder(path):
    head, tail = ntpath.split(path)
    return head

def makedirs_recursive(dirname):
    if not os.path.exists(dirname):
        makedirs_recursive(get_containing_folder(dirname))
        os.makedirs(dirname)

def get_pareto_values(variant_list):
    sorted_variant_list = sorted(variant_list,key=lambda x:x.error)
    ans = []
    for i in xrange(len(sorted_variant_list)):
        if len(ans) == 0:
            ans.append(sorted_variant_list[0])
        else:
            error_prev = ans[-1].error
            time_prev = ans[-1].time
            error_current = sorted_variant_list[i].error
            time_current = sorted_variant_list[i].time
            assert error_current >= error_prev
            if time_current < time_prev:
                ans.append(sorted_variant_list[i])
    return ans

if __name__ == '__main__':
    print 
    if len(sys.argv) < 5:
        print >> sys.stderr, 'python '+__file__+' program_name result_dir num_merges num_islands <ga.py_params>'
        print >> sys.stderr, ''
        print >> sys.stderr, 'Parameters for ga.py are described below:'
        print >> sys.stderr, ''
        usage() # this is the usage from ga.py
        sys.exit(1)
    
    program_name = sys.argv[1]
    result_dir = os.path.abspath(sys.argv[2])
    num_merges = int(sys.argv[3])
    num_islands = int(sys.argv[4])
    ga_args0 = []
    if len(sys.argv) > 5:
        ga_args0 += sys.argv[5:]
    ga_args0 = ' '.join(ga_args0)+' -resume_previous_search 1 -run_final_generation 1 '
    
    print '\n'
    print 'Parameters:'
    print '    program_name:', program_name
    print '    result_dir:', result_dir
    print '    num_merges:', num_merges
    print '    num_islands:', num_islands
    print '    ga_args0:', ga_args0
    print '\n\n'
    
    os.system('rm -rf '+result_dir)
    makedirs_recursive(result_dir)
    
    all_approximations = []
    for which_merge in xrange(num_merges):
        ga_args = ga_args0 + ' -init_pop '+str(get_pareto_values(all_approximations)).encode('hex')
        ga_command = "python ga.py "+program_name+" %s "+ga_args+" > %s 2>&1"
#        print ga_command % ('111','222')
        print "Starting Merge "+str(which_merge+1)+" out of "+str(num_merges)
        ga_subprocesses_data_list = []
        for which_island in xrange(num_islands): # launch GA subprocesses
            island_output_directory = os.path.join(result_dir,'merge_'+str(which_merge)+'_island_'+str(which_island))
            terminal_output_file = os.path.join(island_output_directory, "stdout.txt")
            makedirs_recursive(get_containing_folder(terminal_output_file))
            subprocess_command = ga_command % (island_output_directory, terminal_output_file)
            print "    Island "+str(which_island)+" command: \n        "+subprocess_command
            ga_subprocesses_data_list.append( (subprocess.Popen(subprocess_command,shell=True),island_output_directory) )
        completed_subprocesses = set()
        while len(completed_subprocesses) != num_islands: # check to see if all the GA subprocesses are done
            for i,(ga_subprocess,island_output_directory) in enumerate(ga_subprocesses_data_list): # check on GA subprocesses
                if i in completed_subprocesses:
                    continue
                if ga_subprocess.poll() != None: # i.e. it has completed
                    gen100000_dir = os.path.join(island_output_directory,'gen100000')
                    if os.path.exists(gen100000_dir): #check if gen100000 exists
                        completed_subprocesses.add(i)
                        s = open(os.path.join(island_output_directory, 'rank0.py'), 'rt').read()
                        exec s 
                        all_approximations += rank0
                        print "    Island "+str(i)+" for merge "+str(1+which_merge)+" has completed. "+str(len(completed_subprocesses))+" islands out of "+str(num_islands)+" complete so far."
                    else: # it doesn't exist and we need to resume it 
                        terminal_output_file = os.path.join(island_output_directory, "stdout.txt")
                        makedirs_recursive(terminal_output_file)
                        subprocess_command = ga_command % (island_output_directory, terminal_output_file)
                        ga_subprocesses_data_list[i] = (subprocess.Popen(subprocess_command,shell=True),island_output_directory) 
                        print "    Island "+str(i)+" restarted."
    # Save all variants
    all_approx_dir = os.path.abspath(os.path.join(result_dir, 'all_approximations'))
    makedirs_recursive(all_approx_dir)
    with open(os.path.join(all_approx_dir,'all.csv'), 'wt') as f_all_csv:
        f_all_csv.write('Approx File, Time, Mean Lab \n')
        for (i,indiv) in enumerate(all_approximations):
            filename = os.path.join(all_approx_dir, individual_filename(i))
            with open(filename, 'wt') as f_approx_file:
                f_approx_file.write(str(indiv))
            f_all_csv.write(individual_filename(i)+', '+str(indiv.time)+', '+str(indiv.error)+'\n')
    with open(os.path.join(all_approx_dir, 'all_approximations.py'), 'wt') as f:
        f.write('rank0 = ' + repr(all_approximations))
    # Save pareto variants
    pareto_approx_dir = os.path.abspath(os.path.join(result_dir, 'pareto_approximations'))
    makedirs_recursive(pareto_approx_dir)
    pareto_variants = get_pareto_values(all_approximations)
    with open(os.path.join(pareto_approx_dir,'pareto.csv'), 'wt') as f_pareto_csv:
        f_pareto_csv.write('Approx File, Time, Mean Lab \n')
        for (i,indiv) in enumerate(pareto_variants):
            filename = os.path.join(pareto_approx_dir, individual_filename(i))
            with open(filename, 'wt') as f_approx_file:
                f_approx_file.write(str(indiv))
            f_pareto_csv.write(individual_filename(i)+', '+str(indiv.time)+', '+str(indiv.error)+'\n')
    with open(os.path.join(pareto_approx_dir, 'pareto_approximations.py'), 'wt') as f:
        f.write('rank0 = ' + repr(pareto_variants))
    print 

