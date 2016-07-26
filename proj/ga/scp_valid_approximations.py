#!/usr/bin/python

import os
import sys

def list_dir_abs(basepath):
    return map(lambda x: os.path.join(basepath, x), os.listdir(basepath))

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

def usage():
    print >> sys.stderr, 'python '+__file__+' pareto_over_all_approximations_so_far_dir program_name'
    sys.exit(1)

def main():
    if len(sys.argv) < 3:
        usage()
    
    approx_dir = sys.argv[1]
    program_name = sys.argv[2]
    os.system('clear')
    os.system('clear')
    print '\n'.join( map(lambda e:'scp pn2yr@power6.cs.virginia.edu:'+os.path.join(approx_dir,e.split(',')[0])+' .',filter(lambda e:float(e.split(',')[1])<1.0, open(os.path.join(approx_dir,'pareto.csv'),'rt').readlines()[1:])) )

if __name__ == '__main__':
    main()

