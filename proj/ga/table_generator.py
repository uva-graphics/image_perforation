#!/usr/bin/python

import sys; sys.path += ['../visualize_results', '../solver', '../compiler']
import os
import ntpath
import pdb

ERROR_CUT_OFF = 10.0

#applications = ['artistic_blur', 'bilateral_filter', 'bilateral_grid', 'blur', 'unsharp_mask']

#application_output_locations = { 'artistic_blur'    : '/if23/pn2yr/Desktop/department_cluster/ga_searches/artistic_blur_ga/gen000199/pareto_over_all_approximations_so_far/', 
#                                 'bilateral_filter' : '/if23/pn2yr/Desktop/department_cluster/ga_searches/bilateral_filter_ga_adaptive/gen000199/pareto_over_all_approximations_so_far/', 
#                                 'bilateral_grid'   : '/if23/pn2yr/Desktop/department_cluster/ga_searches/bilateral_grid_ga_final_variants', 
#                                 'blur'             : '/if23/pn2yr/Desktop/department_cluster/ga_searches/blur_ga/gen000199/pareto_over_all_approximations_so_far/', 
#                                 'unsharp_mask'     : '/if23/pn2yr/Desktop/department_cluster/ga_searches/unsharp_mask_quick_run_cluster/gen000068/pareto_over_all_approximations_so_far', 
#                               }

applications = ['demosaic']

application_output_locations = {'demosaic': '/home/liming/Document/filter-approx/proj/ga/result_demosaic_full/gen100000/'}

def list_dir_abs(basepath):
    return map(lambda x: os.path.join(basepath, x), os.listdir(basepath))

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

def get_approx_loops(program_name):
    sys.path.append('../'+program_name)
    exec ('from '+program_name+' import approx_loops')
    return approx_loops

def main():
    os.system('clear')
    print 
    print '%18s | %18s | %18s | %18s | %18s | %18s |' % ('','Adaptive','Importance','Grid','None', 'Total')
    print '-'*125
    
    for program_name in applications:
        approx_dir = application_output_locations[program_name]
        
        approx_loops = get_approx_loops(program_name)
        
        time_error_data = {}
        for e in os.listdir(approx_dir):
            time_error_data[e] = (0,0)
        try:
            time_error_list = map(lambda x:(x[0],float(x[1]),float(x[2]) ), map(lambda e:e.replace('\n','').split(', '),open(os.path.join(approx_dir,'pareto.csv'),'rt').readlines()[1:]) ) 
            for (name, time, error) in time_error_list:
                time_error_data[name] = (time, error)
        except: 
            pass
        
        approx_code_list = ['\n'+open(f,'rt').read()+'\n' for f in list_dir_abs(approx_dir) if '.approx' in f and time_error_data[path_leaf(f)][1] < ERROR_CUT_OFF]
        
        for_each_loop_names = [ k for k,v in approx_loops.items() if v == 'foreach' ]
        
        template = {'adaptive':0, 'importance':0, 'grid':0, 'none':0, 'total':0}
        data_dict = {}
        for name in for_each_loop_names:
            data_dict[name] = dict(template)
        
        for code in approx_code_list:
            #print 'beginning statistics for code:'
            #print code
            #print
            lines = [l for l in code.split('\n') if len(l)>0]
            for name in for_each_loop_names:
                #print 'finding statistics for loop %s' % name
                data_dict[name]['total']+=1
                found = False
                for i,line in enumerate(lines):
                    if line.startswith(name+'.sample'):
                        #print 'name.sample found'
                        if 'sample_adaptive' in line:
                            data_dict[name]['adaptive']+=1
                            found = True
                            break
                        elif 'sample_importance' in line:
                            data_dict[name]['importance']+=1
                            found = True
                            break
                        elif 'sample_grid' in line:
                            data_dict[name]['grid']+=1
                            found = True
                            break
                    if i == len(lines)-1:
                        data_dict[name]['none']+=1
                        found = True
                
                #if not found:
                #    print code, name
                #    print data_dict
                #    assert False
        
        total_overall = 0
        adaptive_overall = 0
        importance_overall = 0
        grid_overall = 0
        none_overall = 0
        
        #print data_dict

        for name in for_each_loop_names:
            total_overall += float(data_dict[name]['total'])
            adaptive_overall += data_dict[name]['adaptive']
            importance_overall += data_dict[name]['importance']
            grid_overall += data_dict[name]['grid']
            none_overall += data_dict[name]['none']
       
        adaptive_percent = 100*adaptive_overall / float(total_overall)
        importance_percent = 100*importance_overall / float(total_overall)
        grid_percent = 100*grid_overall / float(total_overall)
        none_percent = 100*none_overall / float(total_overall)
        
        print '%-18s | %16.2f %% | %16.2f %% | %16.2f %% | %16.2f %% | %16.2f %% |' % (program_name, adaptive_percent, importance_percent, grid_percent, none_percent, adaptive_percent+importance_percent+grid_percent+none_percent)
        #print program_name
        #print '    Adaptive:   %10d / %-10d = %10.2f%%' % (adaptive_overall, total_overall, adaptive_percent)
        #print '    Importance: %10d / %-10d = %10.2f%%' % (importance_overall, total_overall, importance_percent)
        #print '    Grid:       %10d / %-10d = %10.2f%%' % (grid_overall, total_overall, grid_percent)
        #print '    None:       %10d / %-10d = %10.2f%%' % (none_overall, total_overall, none_percent)
        #print '    Total:      %10d / %-10d = %10.2f%%' % (adaptive_overall+importance_overall+grid_overall+none_overall, total_overall, adaptive_percent+importance_percent+grid_percent+none_percent)
        #print
    print '-'*125
    print  

if __name__ == '__main__':
    main()

