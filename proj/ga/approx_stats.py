
import sys
import os
import sys

search_words = { 'adaptive' : '.sample_adaptive(', 
                 'grid' : '.sample_grid(', 
                 'importance' : '.sample_importance(', 
                 'contiguous' : '.sample_contiguous(', 
                 'step' : '.sample_step(', 
                 'random' : '.sample_random(', 
                 'gaussian' : 'reconstruct_gaussian', 
                 'gaussian_sv' : 'reconstruct_gaussian_sv', 
                 'nearest_neighbor' : 'reconstruct_nearest', 
                 'store' : '.reconstruct_store(', 
                 'compute' : '.reconstruct_compute('
               }

def list_dir_abs(basepath):
    return map(lambda x: os.path.join(basepath, x), os.listdir(basepath))

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

def get_containing_folder(path):
    head, tail = ntpath.split(path)
    return head

def makedirs_recursive(dirname):
    if not os.path.exists(dirname):
        makedirs_recursive(get_containing_folder(dirname))
        os.makedirs(dirname)

def set_to_list(s):
    return sorted([a for a in s])

def flatten_list(l):
    return reduce(lambda x,y: x+y,l)

def usage():
    print >> sys.stderr, 'python '+__file__+' directory_to_analyze'
    print >> sys.stderr, ''
    sys.exit(1)

if __name__ == '__main__':
    print 
    if len(sys.argv) < 2:
        usage()
    
    approx_dir = os.path.abspath(sys.argv[1])
    
    loop_names = set_to_list(set(map(lambda e:e[:e.find('.')],flatten_list([open(f,'rt').readlines() for f in list_dir_abs(approx_dir) if '.approx' in f]))))
    
    approx_code_list = [open(f,'rt').read() for f in list_dir_abs(approx_dir) if '.approx' in f]
    
    approx_line_list = reduce(lambda a,b:a+b, map(lambda e:e.split('\n'),approx_code_list))
    
    def print_data(approx_technique):
        search_word = search_words[approx_technique]
        for loop in loop_names:
            lines_using_loop = filter(lambda e:loop in e,approx_line_list)
            if len(lines_using_loop) == 0:
                print "            0%"
                return
            lines_using_this_technique = filter(lambda e:search_word in e, lines_using_loop)
            print "            "+loop+": "+str( len(lines_using_this_technique) / float(len(lines_using_loop)) )
    
    os.system('clear')
    print loop_names
    print "Approximation Statistics:"
    print 
    print "In Terms Of Number Of Approximation Files Using Each Technique:"
    print 
    print "    Image Perforation:"
    print "        Adaptive:                   "
    print_data('adaptive')
    print "        Grid:                       "
    print_data('grid')
    print "        Importance:                 "
    print_data('importance')
    print 
    print "    Image Perforation:"
    print "        Contiguous:                 "
    print_data('contiguous')
    print "        Step:                       "
    print_data('step')
    print "        Random:                     "
    print_data('random')
    print 
    print "    Reconstruction:"
    print "        Gaussian:                   "
    print_data('gaussian')
    print "        Spatially Varying Gaussian: "
    print_data('gaussian_sv')
    print "        Nearest Neighbor:           "
    print_data('nearest_neighbor')
    print "        Store:                      "
    print_data('store')
    print "        Compute:                    "
    print_data('compute')
    print 
    
    print "In Terms Of Number Of Number Of Times Each Technique Is Used Total:"
    print 
    print "    Image Perforation:"
    print "        Adaptive:                   "+"%4d"%(len(filter(lambda e: '.sample_adaptive(' in e, approx_line_list)))+" out of "+"%4d"%(len(approx_line_list))+" total lines of .approx code."
    print "        Grid:                       "+"%4d"%(len(filter(lambda e: '.sample_grid(' in e, approx_line_list)))+" out of "+"%4d"%(len(approx_line_list))+" total lines of .approx code."
    print "        Importance:                 "+"%4d"%(len(filter(lambda e: '.sample_importance(' in e, approx_line_list)))+" out of "+"%4d"%(len(approx_line_list))+" total lines of .approx code."
    print 
    print "    Image Perforation:"
    print "        Contiguous:                 "+"%4d"%(len(filter(lambda e: '.sample_contiguous(' in e, approx_line_list)))+" out of "+"%4d"%(len(approx_line_list))+" total lines of .approx code."
    print "        Step:                       "+"%4d"%(len(filter(lambda e: '.sample_step(' in e, approx_line_list)))+" out of "+"%4d"%(len(approx_line_list))+" total lines of .approx code."
    print "        Random:                     "+"%4d"%(len(filter(lambda e: '.sample_random(' in e, approx_line_list)))+" out of "+"%4d"%(len(approx_line_list))+" total lines of .approx code."
    print 
    print "    Reconstruction:"
    print "        Gaussian:                   "+"%4d"%(len(filter(lambda e: 'reconstruct_gaussian' in e, approx_line_list)))+" out of "+"%4d"%(len(approx_line_list))+" total lines of .approx code."
    print "        Spatially Varying Gaussian: "+"%4d"%(len(filter(lambda e: 'reconstruct_gaussian_sv' in e, approx_line_list)))+" out of "+"%4d"%(len(approx_line_list))+" total lines of .approx code."
    print "        Nearest Neighbor:           "+"%4d"%(len(filter(lambda e: 'reconstruct_nearest' in e, approx_line_list)))+" out of "+"%4d"%(len(approx_line_list))+" total lines of .approx code."
    print "        Store:                      "+"%4d"%(len(filter(lambda e: '.reconstruct_store(' in e, approx_line_list)))+" out of "+"%4d"%(len(approx_line_list))+" total lines of .approx code."
    print "        Compute:                    "+"%4d"%(len(filter(lambda e: '.reconstruct_compute(' in e, approx_line_list)))+" out of "+"%4d"%(len(approx_line_list))+" total lines of .approx code."
    print 

