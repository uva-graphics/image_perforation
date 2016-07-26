
import os

base_script = '''
#!/bin/sh 
#PBS -l select=1:ncpusize=X5550
#PBS -l walltime=12:00:00
#PBS -o /home/pn2yr/code/filter-approx/proj/fir/%s_pop%d_gen%d_tourny%d%s_error.txt
#PBS -j oe 
#PBS -m bea 
#PBS -M paulnguyencomputerscience@gmail.com 

APPLICATION=%s
POPULATION_SIZE=%d
NUM_GENERATIONS=%d
TOURNY_SIZE=%d

OUTPUT_DIRECTORY=/bigtmp/pn2yr/$APPLICATION\_pop$POPULATION_SIZE\_gen$NUM_GENERATIONS\_tourny$TOURNY_SIZE%s
TRAINING_IMAGES_DIRECTORY=$PWD/code/filter-approx/proj/benchmark/training_images

mkdir $OUTPUT_DIRECTORY

cd  ./code/filter-approx/proj/ga

GA_COMMAND="python ga.py $APPLICATION $OUTPUT_DIRECTORY -population_size $POPULATION_SIZE -generations $NUM_GENERATIONS -training_images_directory $TRAINING_IMAGES_DIRECTORY -tournament_size $TOURNY_SIZE -resume_previous_search 1 -loop_perf_only %d -run_on_fir 1"

while true; do
    echo $GA_COMMAND;
    echo $GA_COMMAND | bash;
done;

''' 

if __name__ == '__main__':
    output_directory = os.path.abspath('./fir_scripts')
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    for app_name in ['blur','bilateral_grid','img_abstraction','unsharp_mask_with_bilateral_grid']:
        for pop in xrange(25,251,25):
            #for gen in xrange(10,250,10):
            gen = 999
            for tourny in [2<<x for x in xrange(5)]:
                file_name = "%s_pop%d_gen%d_tourny%d.sh" % (app_name, pop, gen, tourny)
                with open(os.path.join(output_directory,file_name), 'wt') as f:
                    f.write(base_script % (app_name, pop, gen, tourny, '', app_name, pop, gen, tourny, '', 0) )
                file_name = "%s_pop%d_gen%d_tourny%d_loop_perf.sh" % (app_name, pop, gen, tourny)
                with open(os.path.join(output_directory,file_name), 'wt') as f:
                    f.write(base_script % (app_name, pop, gen, tourny, '_loop_perf_only', app_name, pop, gen, tourny, '_loop_perf_only', 1) )
    print "for e in *.sh; do qsub $e; done"
