
import os
import random

NUM_IMPORTANCE_APPROXIMATIONS_TO_GENERATE = 200
NUM_GRID_STORE_APPROXIMATIONS_TO_GENERATE = 200
#NUM_GRID_COMPUTE_APPROXIMATIONS_TO_GENERATE = 50

LOOP_NAME_LIST = ['Ce_loop']

def main():
    frac_max_min = (0.025, 0.95)
    importance_max_min = (1.0/150.0, 1.0/32.0)
    channels_max_min = (1,1)
    reconstruction_methods = ['reconstruct_gaussian', 'reconstruct_gaussian_sv', 'reconstruct_nearest']
    spacing_values = [1<<i for i in xrange(4)]
    sigma_max_min = (0.25, 3.0)
    
    output_directory = os.path.abspath('./importance_vs_grid_approx/')
    
    if (not os.path.isdir(output_directory)): 
        os.makedirs(output_directory)
    
    for i in xrange(NUM_IMPORTANCE_APPROXIMATIONS_TO_GENERATE):
        approx_name = 'importance%03d.approx' % i
        with open(os.path.join(output_directory,approx_name), 'wt') as f:
            frac_value = random.uniform(frac_max_min[0],frac_max_min[1])
            importance_value = random.uniform(importance_max_min[0],importance_max_min[1])
            reconstruction_func_value = random.choice(reconstruction_methods)
            sigma_value = random.uniform(sigma_max_min[0],sigma_max_min[1])
            loop_name = random.choice(LOOP_NAME_LIST)
            approx_file_contents = '%s.sample_importance(frac=%f, importance_args=(%f,), channels=1); %s.reconstruct_store(reconstruct_func=%s, sigma=%f)\n' % (loop_name, frac_value, importance_value, loop_name, reconstruction_func_value, sigma_value)
            f.write(approx_file_contents);
            print "Creating Approx: "+approx_name
            print approx_name+" contents: "+approx_file_contents
            print 
    
    for i in xrange(NUM_GRID_STORE_APPROXIMATIONS_TO_GENERATE):
        approx_name = 'grid_store%03d.approx' % i
        with open(os.path.join(output_directory,approx_name), 'wt') as f:
            spacing_value_1 = random.choice(spacing_values)
            spacing_value_2 = random.choice(spacing_values)
            reconstruction_func_value = random.choice(reconstruction_methods)
            sigma_value = random.uniform(sigma_max_min[0],sigma_max_min[1])
            loop_name = random.choice(LOOP_NAME_LIST)
            approx_file_contents = '%s.sample_grid(spacing=[%d,%d], channels=1); %s.reconstruct_store(reconstruct_func=%s, sigma=%f)\n' % (loop_name, spacing_value_1, spacing_value_2, loop_name, reconstruction_func_value, sigma_value)
            f.write(approx_file_contents);
            print "Creating Approx: "+approx_name
            print approx_name+" contents: "+approx_file_contents
            print 
    
#    for i in xrange(NUM_GRID_COMPUTE_APPROXIMATIONS_TO_GENERATE):
#        approx_name = 'grid_compute%03d.approx' % i
#        with open(os.path.join(output_directory,approx_name), 'wt') as f:
#            spacing_value = random.choice(spacing_values)
#            reconstruction_func_value = random.choice(reconstruction_methods)
#            sigma_value = random.uniform(sigma_max_min[0],sigma_max_min[1])
#            approx_file_contents = '%s.sample_grid(spacing=[%d,%d], channels=1); %s.reconstruct_compute()' % (LOOP_NAME, spacing_value, spacing_value, LOOP_NAME)
#            f.write(approx_file_contents);
#            print "Creating Approx: "+approx_name
#            print approx_name+" contents: "+approx_file_contents
#            print 

if __name__ == '__main__':
    main()
