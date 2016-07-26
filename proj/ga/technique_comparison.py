#!/usr/bin/python

import os
import sys
import approx_stats

def list_dir_abs(basepath):
    return map(lambda x: os.path.join(basepath, x), os.listdir(basepath))

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

def makedirs(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)

def usage():
    print >> sys.stderr, 'python '+__file__+' pareto_over_all_approximations_so_far_dir output_directory'
    sys.exit(1)

def main():
    if len(sys.argv) < 3:
        usage()
    
    approx_dir = os.path.abspath(sys.argv[1])
    output_dir = os.path.abspath(sys.argv[2])
    makedirs(output_dir)
    
    lines = open(os.path.join(approx_dir,'pareto.csv'),'rt').readlines()
    title_line = lines.pop(0)
    
    file_adaptive = open(os.path.join(output_dir,'adaptive.csv'),'wt')
    file_importance = open(os.path.join(output_dir,'importance.csv'),'wt')
    file_grid = open(os.path.join(output_dir,'grid.csv'),'wt')
    
    file_adaptive.write(title_line)
    file_importance.write(title_line)
    file_grid.write(title_line)
    
    for line in lines:
        approx_name = line.split(',')[0].strip()
        approx_code = open(os.path.join(approx_dir, approx_name),'rt').read()
        if '.sample_adaptive(' in approx_code:
            file_adaptive.write(line)
        if '.sample_importance(' in approx_code:
            file_importance.write(line)
        if '.sample_grid(' in approx_code:
            file_grid.write(line)
    file_adaptive.close()
    file_importance.close()
    file_grid.close()
    
    os.system('cp ./pareto_comparison.py '+output_dir)
    os.system('(cd '+output_dir+' && python pareto_comparison.py) &> /dev/null')
    os.system('(mv '+os.path.join(output_dir,'out_1.png')+' '+os.path.join(output_dir,'lines.png')+') &> /dev/null')
    os.system('(cd '+output_dir+' && python pareto_comparison.py -points_only) &> /dev/null')
    os.system('(mv '+os.path.join(output_dir,'out_1.png')+' '+os.path.join(output_dir,'points.png')+') &> /dev/null')
    #os.system('clear')
    print "Done!"

if __name__ == '__main__':
    main()

