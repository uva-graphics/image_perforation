#!/usr/bin/python

import os
import sys
import approx_stats

def makedirs(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)

def join_paths(l):
    return reduce(os.path.join,l)

def usage():
    print >> sys.stderr, 'python '+__file__+' ga_dir output_directory'
    sys.exit(1)

def main():
    if len(sys.argv) < 3:
        usage()
    
    ga_dir = os.path.abspath(sys.argv[1])
    output_dir = os.path.abspath(sys.argv[2])
    makedirs(output_dir)
    
    gen_dirs = [ d for d in os.listdir(ga_dir) if d[:3]=='gen' and len(d)==9 and d[3:].isdigit() ]
    gen_dirs = sorted(gen_dirs, key = lambda e: int(e[3:]))
    gen_dirs.pop(-1)
    
    for gen_dir in gen_dirs:
        os.system('cp '+join_paths([ga_dir, gen_dir, 'pareto_over_all_approximations_so_far', 'pareto.csv'])+' '+join_paths([output_dir,gen_dir+'.csv'])+' &> /dev/null')
    
    os.system('cp ./pareto_comparison.py '+output_dir+' > /dev/null 2>&1')
    os.system('(cd '+output_dir+' && python pareto_comparison.py && mv out_1.png progress.png) > /dev/null 2>&1')
    
    print "Done!"

if __name__ == '__main__':
    main()

