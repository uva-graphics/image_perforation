
import ntpath
import os
import sys

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

def list_dir_abs(dirname):
    return [os.path.join(os.path.abspath(dirname),f) for f in os.listdir(dirname)]

def usage():
    print >> sys.stderr, 'python '+__file__+' ga_results_directory'
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        usage()
    
    ga_results_directory = os.path.abspath(sys.argv[1])
    
    area_list = []
    
    for i,e in enumerate(sorted([ x for x in list_dir_abs(ga_results_directory) if 'gen0' in x ])[:-1]):
        pareto_csv_file = os.path.join(e,'pareto_over_all_approximations_so_far/pareto.csv')
        TIME_INDEX = 0
        ERROR_INDEX = 1 
        CONVERGENCE_MEASURE_TIME_LOWER_BOUND = 0.6
        CONVERGENCE_MEASURE_TIME_UPPER_BOUND = 1.0
        pareto_values_for_area = map(lambda x: tuple(map(lambda y:float(y.strip()), x.split(',')[1:])), open(pareto_csv_file,'rt').readlines()[1:] if os.path.isfile(pareto_csv_file) else "")
        # pareto.csv files contain relative times
        pareto_values_for_area = sorted(pareto_values_for_area,key=lambda x:-x[1])
        orig_time = float(pareto_values_for_area[-1][0])
        for index in xrange(len(pareto_values_for_area)):
            pareto_values_for_area[index] = (pareto_values_for_area[index][0]/orig_time,pareto_values_for_area[index][1])
        area_under_pareto_frontier = 0
        if CONVERGENCE_MEASURE_TIME_LOWER_BOUND < pareto_values_for_area[0][TIME_INDEX]:
            area_under_pareto_frontier = float('inf')
            area_under_pareto_frontier = (CONVERGENCE_MEASURE_TIME_LOWER_BOUND, pareto_values_for_area[0][TIME_INDEX])
        else:
           while CONVERGENCE_MEASURE_TIME_UPPER_BOUND <= pareto_values_for_area[-1][TIME_INDEX]:
               pareto_values_for_area.pop(-1)
           while CONVERGENCE_MEASURE_TIME_LOWER_BOUND >= pareto_values_for_area[1][TIME_INDEX]:
                pareto_values_for_area.pop(0)
           first_point = pareto_values_for_area[0]
           second_point = pareto_values_for_area[1]
           frac = (CONVERGENCE_MEASURE_TIME_LOWER_BOUND-first_point[TIME_INDEX])/(second_point[TIME_INDEX]-first_point[TIME_INDEX])
           new_first_point = (first_point[TIME_INDEX]+frac*(second_point[TIME_INDEX]-first_point[TIME_INDEX]),first_point[ERROR_INDEX]+frac*(second_point[ERROR_INDEX]-first_point[ERROR_INDEX]))
           pareto_values_for_area[0] = new_first_point
           for i in xrange(len(pareto_values_for_area)-1):
               point_a = pareto_values_for_area[i]
               point_b = pareto_values_for_area[i+1]
               area = 0.5*(point_a[ERROR_INDEX]+point_b[ERROR_INDEX])*(point_b[TIME_INDEX]-point_a[TIME_INDEX])
               area_under_pareto_frontier += area
        area_list.append( (path_leaf(e), area_under_pareto_frontier) )
    print '\n'.join( map(str,area_list) )

if __name__ == '__main__':
    main()

