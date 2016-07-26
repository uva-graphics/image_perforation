
import sys
import os, os.path
from ga import *

def main():
    args = sys.argv[1:]
    if len(args) < 1:
        print >> sys.stderr, 'summarize_status.py outdir'
        print >> sys.stderr, 'Writes current_status.csv with current Pareto frontier'
    
    result_dir = args[0]
    d = {}
    s = open(os.path.join(result_dir, 'rank0.py'), 'rt').read()
    exec s in globals(), d
    all_rank0 = d['rank0']
    rank = get_pareto_rank(all_rank0)

    all_rank0 = sorted([all_rank0[i] for i in range(len(all_rank0)) if rank[i] == 0], key=lambda x: x.error)

    with open(os.path.join(result_dir, 'current_status.csv'), 'wt') as f:
        print >> f, 'Index, Time, Error'

        for (i, indiv) in enumerate(all_rank0):
            print >> f, '%d, %f, %f' % (i, indiv.time, indiv.error)

if __name__ == '__main__':
    main()
    