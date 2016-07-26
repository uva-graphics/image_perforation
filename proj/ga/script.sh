qsub -I -l mem=4gb

cd ~/Desktop/department_cluster/artistic_blur/filter-approx/proj/ga/

python ga.py unsharp_mask /if23/pn2yr/Desktop/department_cluster/ga_searches/unsharp_mask_ga -population_size 100 -generations 200 -tournament_size 2 -resume_previous_search 1 -run_on_fir 1 -run_final_generation 0 -loop_perf_only 0 -training_images_directory /home/pn2yr/code/filter-approx/proj/benchmark/training_images -use_adaptive 1 -reconstruct_hints 1

python ga.py img_abstraction /if23/pn2yr/Desktop/department_cluster/ga_searches/img_abstraction_ga -population_size 100 -generations 200 -tournament_size 2 -resume_previous_search 1 -run_on_fir 1 -run_final_generation 0 -loop_perf_only 0 -training_images_directory /home/pn2yr/code/filter-approx/proj/benchmark/training_images -use_adaptive 1 -reconstruct_hints 1

python ga.py blur /if23/pn2yr/Desktop/department_cluster/ga_searches/blur_ga -population_size 100 -generations 200 -tournament_size 2 -resume_previous_search 1 -run_on_fir 1 -run_final_generation 0 -loop_perf_only 0 -training_images_directory /home/pn2yr/code/filter-approx/proj/benchmark/training_images -use_adaptive 1 -reconstruct_hints 1

python ga.py artistic_blur /if23/pn2yr/Desktop/department_cluster/ga_searches/artistic_blur_ga -population_size 100 -generations 200 -tournament_size 2 -resume_previous_search 1 -run_on_fir 1 -run_final_generation 0 -loop_perf_only 0 -training_images_directory /home/pn2yr/code/filter-approx/proj/benchmark/training_images -use_adaptive 1 -reconstruct_hints 1

python ga.py bilateral_filter /if23/pn2yr/Desktop/department_cluster/ga_searches/bilateral_filter_ga -population_size 100 -generations 200 -tournament_size 2 -resume_previous_search 1 -run_on_fir 1 -run_final_generation 0 -loop_perf_only 0 -training_images_directory /home/pn2yr/code/filter-approx/proj/benchmark/training_images -use_adaptive 1 -reconstruct_hints 1

python ga.py bilateral_grid /if23/pn2yr/Desktop/department_cluster/ga_searches/bilateral_grid_ga -population_size 100 -generations 200 -tournament_size 2 -resume_previous_search 1 -run_on_fir 1 -run_final_generation 0 -loop_perf_only 0 -training_images_directory /home/pn2yr/code/filter-approx/proj/benchmark/training_images -use_adaptive 1 -reconstruct_hints 1

python ga.py bilateral_grid /if23/pn2yr/Desktop/department_cluster/ga_searches/bilateral_grid_ga -population_size 100 -generations 200 -tournament_size 2 -resume_previous_search 1 -run_on_fir 1 -run_final_generation 0 -loop_perf_only 0 -training_images_directory /home/pn2yr/code/filter-approx/proj/benchmark/training_images -use_adaptive 1 -reconstruct_hints 1

