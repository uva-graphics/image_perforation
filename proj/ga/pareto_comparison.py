#!/usr/bin/python

import os
import sys
import time
import hashlib
import ntpath
import shutil

BACK_UP_PATH = os.path.abspath('./backups')
SAVE_BACKUPS = False
OUTPUT_SCRIPT_NAME = 'script.gnuplot'
POINTS_ONLY = False

hash_table = {}
paul_hash_bias = 1

def paul_hash(string):
    global paul_hash_bias
    return_value = -1
    print hash_table
    if string not in hash_table.keys():
        return_value = paul_hash_bias
        hash_table[string] = return_value
        paul_hash_bias += 1
        return return_value
    else:
        return hash_table[string]

def list_dir_abs(basepath):
    return map(lambda x: os.path.join(basepath, x), os.listdir(basepath))

def get_file_name_without_extension(file_name):
    return os.path.splitext(file_name)[0]

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

def sort_csv(file_name):
    if SAVE_BACKUPS:
        if not os.path.isdir(BACK_UP_PATH):
            os.mkdir(BACK_UP_PATH)
        back_up_name = path_leaf(get_file_name_without_extension(file_name))+(str(time.strftime("(%d-%m-%Y):%H:%M:%S")))+'.csv'
        print os.path.join(BACK_UP_PATH, back_up_name)
        with open(os.path.join(BACK_UP_PATH, back_up_name), 'w') as f:
            f.write(open(file_name,'r').read())
    lines = open(file_name, 'r').readlines()
    data_lines = map(lambda x:','.join(x), sorted(map(lambda x: x.split(','), lines[1:]), key = lambda x:float(x[1])))
    final_text = lines[0]+''.join(data_lines)
    with open(file_name, 'w') as f:
        f.write(final_text)
        

def main(list_of_csv_files):
    list_of_csv_files = sorted(list_of_csv_files)
    commands = '''
set datafile separator ","
set title "'''+TITLE+'''"
set ylabel "'''+Y_AXIS_LABEL+'''"
set xlabel "'''+X_AXIS_LABEL+'''"
set ytic '''+Y_TIC+'''
set xtic '''+X_TIC+'''
set xr ['''+X_MIN+''':'''+X_MAX+''']
set yr ['''+Y_MIN+''':'''+Y_MAX+''']

set terminal png size 1200,900
set output "'''+OUTPUT_FILE_NAME+'''"
'''
    plotting_commands = 'plot '
    
    for i, e in enumerate(list_of_csv_files):
        sort_csv(e)
        if POINTS_ONLY:
            plotting_commands += '"'+e+'" using 3:2 with points title "'+e+'" pointtype '+str(paul_hash(e)%16)
        else:
            plotting_commands += '"'+e+'" using 3:2 with linespoints title "'+e+'" linetype '+str(paul_hash(e)%16)
        if (i != len(list_of_csv_files)-1):
            plotting_commands += ', '
        else:
            plotting_commands += '\n'
    
    commands = commands + plotting_commands
    
    print '-'*88
    print commands
    print '-'*88
    
    with open('./'+OUTPUT_SCRIPT_NAME, 'w') as f:
        f.write(commands)
        
    os.system('cat '+OUTPUT_SCRIPT_NAME+' | gnuplot')
    os.system('rm -f '+OUTPUT_SCRIPT_NAME+' > /dev/null 2>&1')

def make_graph_for_each_file(list_of_csv_files):
    list_of_csv_files = sorted(list_of_csv_files)
    commands = '''
set datafile separator ","
set title "'''+TITLE+'''"
set ylabel "'''+Y_AXIS_LABEL+'''"
set xlabel "'''+X_AXIS_LABEL+'''"
#set ytic '''+Y_TIC+'''
#set xtic '''+X_TIC+'''
set xr ['''+X_MIN+''':'''+X_MAX+''']
set yr ['''+Y_MIN+''':'''+Y_MAX+''']

set terminal png size 500,500
set output "'''+OUTPUT_FILE_NAME+'''"
'''
    plotting_commands = ''
    if MAKE_GRAPH_FOR_EACH_FILE:
        for i, e in enumerate(list_of_csv_files):
            plotting_commands += 'set output "'+get_file_name_without_extension(e)+'.png" \n'
            if POINTS_ONLY:
                plotting_commands += 'plot "'+e+'" using 3:2 with points title "'+e+'" pointtype '+str(paul_hash(e)%16)+'\n'
            else:
                plotting_commands += 'plot "'+e+'" using 3:2 with linespoints title "'+e+'" linetype '+str(paul_hash(e)%16)+'\n'
    
    print '-'*88
    print commands
    print '-'*88
    
    with open('./'+OUTPUT_SCRIPT_NAME, 'w') as f:
        f.write(commands)
        
    os.system('cat '+OUTPUT_SCRIPT_NAME+' | gnuplot')
    os.system('rm -f '+OUTPUT_SCRIPT_NAME+' > /dev/null 2>&1')

if __name__ == '__main__':
    if '-points_only' in sys.argv:
        POINTS_ONLY = True
    X_MIN = '0'
    X_MAX = '*'
    Y_MIN = '0'
    Y_MAX = '*'
    
    Y_TIC = '.2'
    X_TIC = '1'
    
    TITLE = ''
    Y_AXIS_LABEL = 'Time'
    X_AXIS_LABEL = 'Mean LAB Error'
    OUTPUT_FILE_NAME = 'out_1.png'
    main([ f for f in list_dir_abs('./') if '.csv' in f])

