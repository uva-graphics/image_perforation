#!/usr/bin/python

import sys; sys.path += ['../compiler', '../solver']
import os
import shutil
from PIL import Image
import imdist
import json
import subprocess
import matplotlib
matplotlib.use('Agg')
import numpy
import matplotlib
import matplotlib.pyplot
import matplotlib.patches
import math
import traceback
import glob
import subprocess_timeout
import subprocess
import pickle
import time
import random
import platform
import getpass
import ntpath
from collect_pareto import get_pareto
import pdb

numpy.seterr(divide='ignore', invalid='ignore')

DEFAULT_INPUT_IMAGES_DIRECTORY=os.path.abspath('./input/')

NUM_PARALLEL_VARIANTS_TO_TEST_AT_ONCE = 8
NUM_VARIANTS_PER_JOB = NUM_PARALLEL_VARIANTS_TO_TEST_AT_ONCE*1
POLLING_TOLERANCE = 15

visualize_timeout = 60.0*1000000     # Subprocess is terminated if this timeout in seconds expires

verbose = False
normal_run_str = 'Normal Run'

inf = float('inf')

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

def get_containing_folder(path):
    head, tail = ntpath.split(path)
    return head

def list_dir_abs(directory):
    absoluate_path = os.path.abspath(directory)
    return map(lambda x:os.path.join(absoluate_path, x), os.listdir(directory))

def imwrite(I, filename):
    assert isinstance(I, numpy.ndarray)
    I = numpy.clip(I, 0.0, 1.0)
    I = I * 255
    I = numpy.asarray(I, 'uint8')
    I = Image.fromarray(I)
    I.save(filename)    

def imread(filename):
    return numpy.array(Image.open(filename), 'double')/255.0

def open_file(filename):
    try:
        os.startfile(filename)
    except AttributeError:
        if sys.platform == 'darwin':
            subprocess.Popen(['open', filename])
        else:
            subprocess.Popen(['xdg-open', filename])

def usage():
    print 
    print "usage: python visualize_results.py <directory_of_approx_files> <output_directory> <program_name>"
    print 
    sys.exit(1)

def run_subprocess(s, *args, **kw0):
    kw = dict(kw0)
    del kw['run_on_fir']
    debug_log_location = kw['debug_log_location']
    run_verbose = False
    arg_s = json.dumps((args, kw)).encode('hex')
    runner = ('_'+''.join(map(str,[kw['output_directory'],os.getpid(),time.time()])).replace('\\','').replace('/','')+(''.join([str(random.random()).replace('.','') for e in xrange(255)])))[0:230]+'.py'
    
    if kw0['run_on_fir']:
        copy_debug_file_code = ''
    else: 
        copy_debug_file_code = '''
f = open('debug-out.txt', 'wt')
f.write(repr(result))
f.close()
'''
        if debug_log_location is not None:
            debug_log_location = os.path.join(os.path.abspath(debug_log_location), 'debug-out.txt')
            copy_debug_file_code +='\n'+'shutil.copyfile(\'debug-out.txt\' , \''+debug_log_location+'\')'
    
    with open(runner, 'wt') as f:
        f.write( ("""

import json, sys, shutil
(args, kw) = json.loads(sys.argv[1].decode('hex'))
del kw['debug_log_location']
%s
"""+copy_debug_file_code+"""
print json.dumps(result).encode('hex')
""") % s )
    cmd ='''python %s %s''' % (runner, arg_s)
    
    if run_verbose:
        print 'run_subprocess Command:', cmd
    #pdb.set_trace()
    ans = {}
    try:
        out_s = subprocess_timeout.check_output(cmd, timeout=visualize_timeout) 
        if run_verbose:
            print 'run_subprocess Output:', out_s
        ans = json.loads(out_s.strip().split()[-1].decode('hex'))
        ans['_raw_out'] = out_s
    except Exception as err:
        ans['_raw_out']=str(err)
        for k in map(lambda x: unicode(x+'_time'), list_dir_abs(kw['input_directory'])):
            ans[k]=float('inf')
    try:
        os.remove(runner)
    except:
        pass
    return ans

def run_program(program_name, *args, **kw):
    return run_subprocess('''
import os
os.chdir('../%s')
import sys; sys.path += ['../%s']
import %s
result = %s.main(*args, **kw)''' % (program_name, program_name, program_name, program_name), *args, **kw) 

def plot(ax, x, y, labels):
    ax.scatter(x, y,zorder=10)
    for i in range(len(x)):
        ax.annotate(labels[i], (x[i], y[i]))

def visualize_results(approx_list, output_directory, program_name, open_html=False, run_args={}, dump_ans=True, run_normally=True, input_images_directory=DEFAULT_INPUT_IMAGES_DIRECTORY, use_relative_times_for_return_value=True, no_importance_sampling=False, no_grid_sampling=False,  debug_log_location=None, run_on_fir=False, no_approx_execution_result=None):
    """
    Given list of approx files visualize to given output directory and return list of dicts of
    same length with keys 'approx': approx_filename, 'time': time, 'error': error.
    """
    
    run_args['run_on_fir']=run_on_fir
    
    ans_absolute = []
    ans_relative = []
    
    user_name = getpass.getuser()
    
    new_approx_list = []
    for e in approx_list:
        if no_importance_sampling and 'sample_importance(' in open(e,'r').read():
            continue
        if no_grid_sampling and 'sample_grid(' in open(e,'r').read():
            continue
        new_approx_list.append(e)
    #approx_list = sorted(list(new_approx_list))
    approx_list = sorted(tuple(new_approx_list))
    
    label_names = sorted([os.path.split(filename)[1] for filename in approx_list])
    
    create_error_figure = False

    print '-'*72
    print 'Visualizing results'
    print '-'*72
    print
    sys.stdout.flush()
    
    input_images_directory = os.path.abspath(input_images_directory)
    
    input_images_list = sorted([ f for f in os.listdir(input_images_directory) if os.path.isfile(os.path.join(input_images_directory,f)) and f[-4:]=='.png'])
    
    output_directory = os.path.abspath(output_directory)
    
    if (not os.path.isdir(output_directory)): 
        os.makedirs(output_directory)
    
    
    # Run without approximations
    directory_for_no_approx = os.path.abspath(os.path.join(output_directory,'results-NO_APPROXIMATIONS/'))
    
    output_images_directory_for_no_approx = directory_for_no_approx
    if not os.path.exists(directory_for_no_approx):
        os.makedirs(directory_for_no_approx)
    if run_normally:
        #print no_approx_execution_result
#        if no_approx_execution_result != None:
#            program_execution_result = no_approx_execution_result
#        else:
#            program_execution_result = run_program(program_name, approx_file='', input_directory=input_images_directory, output_directory=output_images_directory_for_no_approx, debug_log_location=debug_log_location, **run_args)
        program_execution_result = run_program(program_name, approx_file='', input_directory=input_images_directory, output_directory=output_images_directory_for_no_approx, debug_log_location=debug_log_location, **run_args)
        #pdb.set_trace()
        #program_execution_result = {u'/home/pn2yr/code/filter-approx/proj/benchmark/training_images/natural.txt_0_image_820x614.png_time': 52.843651, u'/home/pn2yr/code/filter-approx/proj/benchmark/training_images/people.txt_0_image_256x192.png_time': 4.8935955, u'/home/pn2yr/code/filter-approx/proj/benchmark/training_images/man_made.txt_55_image_820x614.png_time': 39.844446500000004, u'/home/pn2yr/code/filter-approx/proj/benchmark/training_images/man_made.txt_1_image_256x192.png_time': 3.7784645, u'/home/pn2yr/code/filter-approx/proj/benchmark/training_images/natural.txt_29_image_256x192.png_time': 5.089096, '_raw_out': 'Times: etf: 0.260288, fdog: 0.391211, fbl: 4.112123\n\nETF:                             0.260288\nFDOG:                            0.391211\nFBL:                             4.112123\nTotal:                           4.776275\nTotal time: 4.776287\nTimes: etf: 0.259682, fdog: 0.233446, fbl: 3.277288\n\nETF:                             0.259682\nFDOG:                            0.233446\nFBL:                             3.277288\nTotal:                           3.781366\nTotal time: 3.781369\nTimes: etf: 0.259637, fdog: 0.228018, fbl: 3.276988\n\nETF:                             0.259637\nFDOG:                            0.228018\nFBL:                             3.276988\nTotal:                           3.775557\nTotal time: 3.775560\nTimes: etf: 0.262673, fdog: 0.392622, fbl: 4.836813\n\nETF:                             0.262673\nFDOG:                            0.392622\nFBL:                             4.836813\nTotal:                           5.504600\nTotal time: 5.504614\nTimes: etf: 0.261607, fdog: 0.295000, fbl: 4.329297\n\nETF:                             0.261607\nFDOG:                            0.295000\nFBL:                             4.329297\nTotal:                           4.896673\nTotal time: 4.896677\nTimes: etf: 0.261603, fdog: 0.294875, fbl: 4.323281\n\nETF:                             0.261603\nFDOG:                            0.294875\nFBL:                             4.323281\nTotal:                           4.890510\nTotal time: 4.890514\nTimes: etf: 0.262546, fdog: 0.394545, fbl: 5.530941\n\nETF:                             0.262546\nFDOG:                            0.394545\nFBL:                             5.530941\nTotal:                           6.201531\nTotal time: 6.201543\nTimes: etf: 0.261668, fdog: 0.296898, fbl: 4.516484\n\nETF:                             0.261668\nFDOG:                            0.296898\nFBL:                             4.516484\nTotal:                           5.086815\nTotal time: 5.086819\nTimes: etf: 0.261734, fdog: 0.296670, fbl: 4.521233\n\nETF:                             0.261734\nFDOG:                            0.296670\nFBL:                             4.521233\nTotal:                           5.091370\nTotal time: 5.091373\nTimes: etf: 2.703892, fdog: 4.024923, fbl: 60.422282\n\nETF:                             2.703892\nFDOG:                            4.024923\nFBL:                             60.422282\nTotal:                           67.273171\nTotal time: 67.273192\nTimes: etf: 2.693463, fdog: 3.055960, fbl: 46.962183\n\nETF:                             2.693463\nFDOG:                            3.055960\nFBL:                             46.962183\nTotal:                           52.822354\nTotal time: 52.822363\nTimes: etf: 2.692951, fdog: 3.057230, fbl: 47.004033\n\nETF:                             2.692951\nFDOG:                            3.057230\nFBL:                             47.004033\nTotal:                           52.864930\nTotal time: 52.864939\nCompiling out5355if23pn2yrDesktopdepartmentclustergasearchesimgabstractiongaloopperfonlygen000098visualize.cpp => out5355if23pn2yrDesktopdepartmentclustergasearchesimgabstractiongaloopperfonlygen000098visualize\n  (19488 bytes)\necho "if test ../solver/array.cpp -nt array.o; then g++ -c -O3 -fopenmp -funroll-loops -fmax-errors=3 -std=c++0x -fabi-version=6 -DBUILD_DEBUG=0 -I /opt/X11/include ../solver/array.cpp -o array.o; fi; " | bash ; echo "if test ../solver/pfm.cpp -nt pfm.o; then g++ -c -O3 -fopenmp -funroll-loops -fmax-errors=3 -std=c++0x -fabi-version=6 -DBUILD_DEBUG=0 -I /opt/X11/include ../solver/pfm.cpp -o pfm.o; fi; " | bash ; echo "if test ../solver/params.cpp -nt params.o; then g++ -c -O3 -fopenmp -funroll-loops -fmax-errors=3 -std=c++0x -fabi-version=6 -DBUILD_DEBUG=0 -I /opt/X11/include ../solver/params.cpp -o params.o; fi; " | bash ; echo "if test ../solver/timer.cpp -nt timer.o; then g++ -c -O3 -fopenmp -funroll-loops -fmax-errors=3 -std=c++0x -fabi-version=6 -DBUILD_DEBUG=0 -I /opt/X11/include ../solver/timer.cpp -o timer.o; fi; " | bash ; echo "if test ../solver/util.cpp -nt util.o; then g++ -c -O3 -fopenmp -funroll-loops -fmax-errors=3 -std=c++0x -fabi-version=6 -DBUILD_DEBUG=0 -I /opt/X11/include ../solver/util.cpp -o util.o; fi; " | bash ; g++ array.o pfm.o params.o timer.o util.o -o out5355if23pn2yrDesktopdepartmentclustergasearchesimgabstractiongaloopperfonlygen000098visualize -O3 -fopenmp -funroll-loops -fmax-errors=3 -std=c++0x -fabi-version=6 -DBUILD_DEBUG=0 -I /opt/X11/include out5355if23pn2yrDesktopdepartmentclustergasearchesimgabstractiongaloopperfonlygen000098visualize.cpp       -L /opt/X11/lib -lpthread -lpng -ldl -fno-tree-pre\nResult: 0\n"/net/if23/pn2yr/Desktop/department_cluster/filter-approx/proj/img_abstraction/out5355if23pn2yrDesktopdepartmentclustergasearchesimgabstractiongaloopperfonlygen000098visualize" /home/pn2yr/code/filter-approx/proj/benchmark/training_images/man_made.txt_1_image_256x192.png /if23/pn2yr/Desktop/department_cluster/ga_searches/img_abstraction_ga_loop_perf_only/gen000098/visualize/results-NO_APPROXIMATIONS/man_made.txt_1_image_256x192-out.png 2>&1 | tee out5355if23pn2yrDesktopdepartmentclustergasearchesimgabstractiongaloopperfonlygen000098visualize-time.txt\n"/net/if23/pn2yr/Desktop/department_cluster/filter-approx/proj/img_abstraction/out5355if23pn2yrDesktopdepartmentclustergasearchesimgabstractiongaloopperfonlygen000098visualize" /home/pn2yr/code/filter-approx/proj/benchmark/training_images/people.txt_0_image_256x192.png /if23/pn2yr/Desktop/department_cluster/ga_searches/img_abstraction_ga_loop_perf_only/gen000098/visualize/results-NO_APPROXIMATIONS/people.txt_0_image_256x192-out.png 2>&1 | tee out5355if23pn2yrDesktopdepartmentclustergasearchesimgabstractiongaloopperfonlygen000098visualize-time.txt\n"/net/if23/pn2yr/Desktop/department_cluster/filter-approx/proj/img_abstraction/out5355if23pn2yrDesktopdepartmentclustergasearchesimgabstractiongaloopperfonlygen000098visualize" /home/pn2yr/code/filter-approx/proj/benchmark/training_images/natural.txt_29_image_256x192.png /if23/pn2yr/Desktop/department_cluster/ga_searches/img_abstraction_ga_loop_perf_only/gen000098/visualize/results-NO_APPROXIMATIONS/natural.txt_29_image_256x192-out.png 2>&1 | tee out5355if23pn2yrDesktopdepartmentclustergasearchesimgabstractiongaloopperfonlygen000098visualize-time.txt\n"/net/if23/pn2yr/Desktop/department_cluster/filter-approx/proj/img_abstraction/out5355if23pn2yrDesktopdepartmentclustergasearchesimgabstractiongaloopperfonlygen000098visualize" /home/pn2yr/code/filter-approx/proj/benchmark/training_images/natural.txt_0_image_820x614.png /if23/pn2yr/Desktop/department_cluster/ga_searches/img_abstraction_ga_loop_perf_only/gen000098/visualize/results-NO_APPROXIMATIONS/natural.txt_0_image_820x614-out.png 2>&1 | tee out5355if23pn2yrDesktopdepartmentclustergasearchesimgabstractiongaloopperfonlygen000098visualize-time.txt\n"/net/if23/pn2yr/Desktop/department_cluster/filter-approx/proj/img_abstraction/out5355if23pn2yrDesktopdepartmentclustergasearchesimgabstractiongaloopperfonlygen000098visualize" /hTimes: etf: 2.751453, fdog: 3.980434, fbl: 47.298049\n\nETF:                             2.751453\nFDOG:                            3.980434\nFBL:                             47.298049\nTotal:                           54.166576\nTotal time: 54.166599\nTimes: etf: 2.740605, fdog: 2.406849, fbl: 34.536041\n\nETF:                             2.740605\nFDOG:                            2.406849\nFBL:                             34.536041\nTotal:                           39.809136\nTotal time: 39.809145\nTimes: etf: 2.740201, fdog: 2.406259, fbl: 34.607684\n\nETF:                             2.740201\nFDOG:                            2.406259\nFBL:                             34.607684\nTotal:                           39.879739\nTotal time: 39.879748\nTimes: etf: 2.748423, fdog: 4.090329, fbl: 60.899280\n\nETF:                             2.748423\nFDOG:                            4.090329\nFBL:                             60.899280\nTotal:                           67.867324\nTotal time: 67.867347\nTimes: etf: 2.737819, fdog: 3.088423, fbl: 47.208431\n\nETF:                             2.737819\nFDOG:                            3.088423\nFBL:                             47.208431\nTotal:                           53.153037\nTotal time: 53.153046\nTimes: etf: 2.737496, fdog: 3.082107, fbl: 47.209149\n\nETF:                             2.737496\nFDOG:                            3.082107\nFBL:                             47.209149\nTotal:                           53.147100\nTotal time: 53.147109\nome/pn2yr/code/filter-approx/proj/benchmark/training_images/man_made.txt_55_image_820x614.png /if23/pn2yr/Desktop/department_cluster/ga_searches/img_abstraction_ga_loop_perf_only/gen000098/visualize/results-NO_APPROXIMATIONS/man_made.txt_55_image_820x614-out.png 2>&1 | tee out5355if23pn2yrDesktopdepartmentclustergasearchesimgabstractiongaloopperfonlygen000098visualize-time.txt\n"/net/if23/pn2yr/Desktop/department_cluster/filter-approx/proj/img_abstraction/out5355if23pn2yrDesktopdepartmentclustergasearchesimgabstractiongaloopperfonlygen000098visualize" /home/pn2yr/code/filter-approx/proj/benchmark/training_images/people.txt_56_image_820x614.png /if23/pn2yr/Desktop/department_cluster/ga_searches/img_abstraction_ga_loop_perf_only/gen000098/visualize/results-NO_APPROXIMATIONS/people.txt_56_image_820x614-out.png 2>&1 | tee out5355if23pn2yrDesktopdepartmentclustergasearchesimgabstractiongaloopperfonlygen000098visualize-time.txt\n7b222f686f6d652f706e3279722f636f64652f66696c7465722d617070726f782f70726f6a2f62656e63686d61726b2f747261696e696e675f696d616765732f6e61747572616c2e7478745f305f696d6167655f383230783631342e706e675f74696d65223a2035322e3834333635312c20222f686f6d652f706e3279722f636f64652f66696c7465722d617070726f782f70726f6a2f62656e63686d61726b2f747261696e696e675f696d616765732f70656f706c652e7478745f305f696d6167655f323536783139322e706e675f74696d65223a20342e383933353935352c20222f686f6d652f706e3279722f636f64652f66696c7465722d617070726f782f70726f6a2f62656e63686d61726b2f747261696e696e675f696d616765732f6d616e5f6d6164652e7478745f35355f696d6167655f383230783631342e706e675f74696d65223a2033392e3834343434363530303030303030342c20222f686f6d652f706e3279722f636f64652f66696c7465722d617070726f782f70726f6a2f62656e63686d61726b2f747261696e696e675f696d616765732f6d616e5f6d6164652e7478745f315f696d6167655f323536783139322e706e675f74696d65223a20332e373738343634352c20222f686f6d652f706e3279722f636f64652f66696c7465722d617070726f782f70726f6a2f62656e63686d61726b2f747261696e696e675f696d616765732f6e61747572616c2e7478745f32395f696d6167655f323536783139322e706e675f74696d65223a20352e3038393039362c20222f686f6d652f706e3279722f636f64652f66696c7465722d617070726f782f70726f6a2f62656e63686d61726b2f747261696e696e675f696d616765732f70656f706c652e7478745f35365f696d6167655f383230783631342e706e675f74696d65223a2035332e313530303737357d\n', u'/home/pn2yr/code/filter-approx/proj/benchmark/training_images/people.txt_56_image_820x614.png_time': 53.1500775}
#        print repr(program_execution_result); exit()
        #no_approx_execution_result = program_execution_result
        total_run_time_absolute_normal_dict = {}
        for key in program_execution_result.keys():
            if 'time' in key:
                total_run_time_absolute_normal_dict[key] = program_execution_result[key]
        
        if ('error' in program_execution_result.keys()):
            create_error_figure = True
            error_normal = program_execution_result['error']
    else:
        total_run_time_absolute_normal_dict = {}
        for input_image_name in [ os.path.abspath(os.path.join(input_images_directory,f)) for f in os.listdir(input_images_directory) if os.path.isfile(os.path.join(input_images_directory,f)) and f[-4:]=='.png']:
            total_run_time_absolute_normal_dict[input_image_name+'_time'] = inf
        create_error_figure = False
        error_normal = inf
    average_total_run_time_absolute_normal = sum(total_run_time_absolute_normal_dict.values())/float(len(total_run_time_absolute_normal_dict.values()))
#    for key in total_run_time_absolute_normal_dict.keys():
#        total_run_time_relative_normal_dict[key] =  1.0
    
    assert len(os.listdir(input_images_directory))>0, "input_images_directory is empty"
    image_to_be_displayed_prefix = sorted(filter(lambda x: x[-4:]=='.png', os.listdir(input_images_directory)))[0][:-4]
    normal_run_output_image_location = os.path.join(output_images_directory_for_no_approx, image_to_be_displayed_prefix+'-out.png')
    normal_run_cropped_output_image_location = os.path.join(output_images_directory_for_no_approx, image_to_be_displayed_prefix[:-8]+'-cropped.png')
    
    html_code = program_name+'''
<BR><a href="visualization_data_absolute.csv">Raw Data (absolute timing)</a><BR>
<BR><a href="visualization_data_relative.csv">Raw Data (relative timing)</a><BR>
<BR><a href="visualization_data_mean_lab_pareto_absolute.csv">Raw Pareto Frontier Data (absolute timing, Mean LAB Distance)</a><BR>
<BR><a href="visualization_data_mean_lab_pareto_relative.csv">Raw Pareto Frontier Data (relative timing, Mean LAB Distance)</a><BR>
<BR><a href="visualization_data_psnr_lab_pareto_absolute.csv">Raw Pareto Frontier Data (absolute timing, Inverse PSNR LAB Distance)</a><BR>
<BR><a href="visualization_data_psnr_lab_pareto_relative.csv">Raw Pareto Frontier Data (relative timing, Inverse PSNR LAB Distance)</a><BR>
<BR><a href="visualization_data_absolute_sample_grid_only.csv">Raw Data (absolute timing, grid sampling approximations only)</a><BR>
<BR><a href="visualization_data_relative_sample_grid_only.csv">Raw Data (relative timing, grid sampling approximations only)</a><BR>
<BR><a href="visualization_data_absolute_sample_importance_only.csv">Raw Data (absolute timing, importance sampling approximations only)</a><BR>
<BR><a href="visualization_data_relative_sample_importance_only.csv">Raw Data (relative timing, importance sampling approximations only)</a><BR>
<BR><BR>


'''
    html_code += ("""
<style type="text/css">
img{
    max-width:600px;
}
</style>
mean_lab_absolute.png
<BR>
<img src="mean_lab_absolute.png">
<BR>
<BRu
<BR>
mean_lab_relative.png
<BR>
<img src="mean_lab_relative.png">
<BR>
<BR>
<BR>
psnr_lab_absolute.png
<BR>
<img src="psnr_lab_absolute.png">
<BR>
<BR>
<BR>
psnr_lab_relative.png
<BR>
<img src="psnr_lab_relative.png">
<BR>
<BR>
<BR>
""")
    if (create_error_figure):
        html_code += ("""
error_absolute.png
<BR>
<img src="error_absolute.png">
<BR>
<BR>
<BR>
error_relative.png
<BR>
<img src="error_relative.png">
<BR>
<BR>
<BR>
""")
    html_code += ("""
mean_lab_pareto_absolute.png
<BR>
<img src="./mean_lab_pareto_absolute.png">
<BR>
<BR>
<BR>
mean_lab_pareto_relative.png
<BR>
<img src="./mean_lab_pareto_relative.png">
<BR>
<BR>
<BR>
psnr_lab_pareto_absolute.png
<BR>
<img src="./psnr_lab_pareto_absolute.png">
<BR>
<BR>
<BR>
psnr_lab_pareto_relative.png
<BR>
<img src="./psnr_lab_pareto_relative.png">
<BR>
<BR>
<BR>
""")
    try:
         current_output_image = Image.open(os.path.join(output_images_directory_for_no_approx, normal_run_output_image_location))
    except Exception as err:
         current_output_image = Image.open(os.path.join(directory_for_no_approx, path_leaf(normal_run_output_image_location)))
#    if not run_on_fir:
    if True:
        width, height = current_output_image.size
        cropped_image = current_output_image.crop((int(width*0.45),int(height*0.45),int(width*0.55),int(height*0.55)))
        cropped_image.load()
        cropped_image.save(normal_run_cropped_output_image_location)
        mean_lab_fig_absolute, mean_lab_subplot_absolute = matplotlib.pyplot.subplots()
        psnr_lab_fig_absolute, psnr_lab_subplot_absolute = matplotlib.pyplot.subplots()
        mean_lab_fig_relative, mean_lab_subplot_relative = matplotlib.pyplot.subplots()
        psnr_lab_fig_relative, psnr_lab_subplot_relative = matplotlib.pyplot.subplots()
    
    total_time_absolute_x = numpy.array([])
    total_time_relative_x = numpy.array([])
    mean_lab_y = numpy.array([])
    psnr_lab_y = numpy.array([])
    
    if (create_error_figure):
        error_fig_absolute, error_subplot_absolute = matplotlib.pyplot.subplots()
        error_fig_relative, error_subplot_relative = matplotlib.pyplot.subplots()
        error_y = numpy.array([])
    
    if (create_error_figure):
        html_code += ("""
error_pareto_absolute.png
<BR>
<img src="./error_pareto_absolute.png">
<BR>
<BR>
<BR>
error_pareto_relative.png
<BR>
<img src="./error_pareto_relative.png">
<BR>
<BR>
<BR>
""")
    html_code += ("""
Normal Run
<BR>
Average Absolute Total Run Time: """+str(average_total_run_time_absolute_normal)+""" sec
Average Relative Total Run Time: 1.0 sec
<BR>
<BR>"""+os.path.relpath(normal_run_output_image_location,output_directory)+"""
<BR><img src=\""""+os.path.relpath(normal_run_output_image_location,output_directory)+"""\">
<BR>
<BR>
<BR>
"""+os.path.relpath(normal_run_cropped_output_image_location,output_directory)+"""
<BR>
<img src=\""""+os.path.relpath(normal_run_cropped_output_image_location,output_directory)+"""\">
<BR>
<BR>
<BR>
<BR>
<BR>
""")
    
    mean_lab_absolute_all_images_matrix = []
    psnr_lab_absolute_all_images_matrix = []
    mean_lab_relative_all_images_matrix = []
    psnr_lab_relative_all_images_matrix = []
    
    program_execution_result_list = []
    
    if run_on_fir:
        qsub_data = []
        runner_list = []
        for (i, full_name) in enumerate(approx_list):
            directory_for_this_approx = os.path.abspath(os.path.join(output_directory, 'results-'+label_names[i]+'/'))
            output_images_directory_for_this_approx = directory_for_this_approx
            if not os.path.exists(directory_for_this_approx):
                os.makedirs(directory_for_this_approx)
            if not os.path.exists(output_images_directory_for_this_approx):
                os.makedirs(output_images_directory_for_this_approx)
            #program_execution_result_list.append( run_program(program_name, approx_file=full_name, input_directory=input_images_directory, output_directory=output_images_directory_for_this_approx, debug_log_location=debug_log_location, **run_args) )
            s = '''
import os
os.chdir('../%s')
import sys; sys.path += ['../%s']
import %s
result = %s.main(*args, **kw)''' % (program_name, program_name, program_name, program_name)
            args = ()
            kw = dict(run_args)
            del kw['run_on_fir']
            kw['output_directory']=output_images_directory_for_this_approx
            kw['approx_file']=full_name
            kw['input_directory']=input_images_directory
            kw['output_directory']=output_images_directory_for_this_approx
            kw['debug_log_location']=debug_log_location
            arg_s = json.dumps((args, kw)).encode('hex')
            runner = ('_'+''.join(map(str,[kw['output_directory'],os.getpid(),time.time()])).replace('\\','').replace('/','')+str(random.random()*time.time()).replace('.',''))+'.py'
            #runner = os.path.abspath(os.path.join(os.getcwd(),runner))
            useful_log_file_name = os.path.join('/if23/pn2yr/Desktop/department_cluster/filter-approx/proj/temp_cluster_files',runner[:-2].replace('.','_')+'_use.txt')
            with open(runner, 'wt') as f:
                f.write( ("""
import json, sys, shutil
sys.stdout = open('"""+useful_log_file_name+"""','wt')
(args, kw) = json.loads(sys.argv[1].decode('hex'))
del kw['debug_log_location']
%s
print json.dumps(result).encode('hex')

""") % s )
            cmd ='''python %s %s''' % (runner, arg_s)
            runner_list.append( (runner, cmd, full_name, useful_log_file_name) )
        batch_index = 0
        for index,(runner,cmd, full_approx_name, useful_log_file_name) in enumerate(runner_list):
            if index % NUM_VARIANTS_PER_JOB == 0:
                approx_list_for_this_batch = []
                qsub_script_name = runner[:-2]+'sh'
                qsub_log_file_name = os.path.join('/if23/pn2yr/Desktop/department_cluster/filter-approx/proj/temp_cluster_files',runner[:-2]+'_log.txt')
                useful_log_file_list = []
                qsub_script_text = """
#!/bin/sh 
#PBS -l nodes=1:ppn="""+str(NUM_PARALLEL_VARIANTS_TO_TEST_AT_ONCE)+"""
#PBS -l mem=64gb
#PBS -l walltime=00:25:00
#PBS -o """+qsub_log_file_name+"""
#PBS -j oe 
#PBS -m n 
#PBS -M paulnguyencomputerscience@gmail.com 

cd """+os.path.abspath(os.getcwd())+"""

"""
            qsub_script_text += "("+cmd+") "
            if (index+1)%NUM_PARALLEL_VARIANTS_TO_TEST_AT_ONCE == 0:
                qsub_script_text += ' & \n   \n\nwait;\n\n'
            else:
                qsub_script_text += ' & \n'
            useful_log_file_list.append(useful_log_file_name)
            approx_list_for_this_batch.append(full_approx_name)
            
            if ((index+1) % NUM_VARIANTS_PER_JOB == 0) or index == len(runner_list)-1:
                
                qsub_script_text += '\n\nwait\n\n'
                
                with open(qsub_script_name, 'wt') as f:
                    f.write(qsub_script_text)
                batch_index += 1
                print "Submitting job for batch "+str(batch_index)
                #pdb.set_trace()
                qsub_sumission_command = 'qsub '+qsub_script_name
                qsub_bash_output = subprocess.check_output(qsub_sumission_command, shell=True)
                job_identifier =  qsub_bash_output[:qsub_bash_output.find('.centur')]
                print "Job identifier for batch "+str(batch_index)+": "+str(job_identifier)
                print 
                qsub_data.append( (qsub_script_name,job_identifier,qsub_log_file_name,runner, useful_log_file_list, approx_list_for_this_batch) )
        print
        #pdb.set_trace()
        assert len(approx_list) == len(reduce(lambda a,b:a+b,map(lambda e:e[4],qsub_data)))
        
        for index,(script_name, job_id, qsub_log_file_name,runner, useful_log_file_list, approx_list_for_this_batch) in enumerate(qsub_data):
            batch_index = index+1
            try:
                #qstat_text = subprocess.check_output('qstat -a | grep '+user_name, shell=True)
                qstat_text0 = subprocess.check_output('qstat -a', shell=True)
            except subprocess.CalledProcessError:
                qstat_text0 = 'AA'
            while job_id in qstat_text0:
                #print qstat_text0
                try:
                    #qstat_text = subprocess.check_output('qstat -a | grep '+user_name, shell=True)
                    qstat_text0 = subprocess.check_output('qstat -a', shell=True)
                except subprocess.CalledProcessError:
                    qstat_text0 = 'ff'
            qstat_text = '\n'.join(filter(lambda e:user_name in e,qstat_text0.split('\n')))
            print 
            print "Collecting data for batch "+str(index)+' out of '+str(len(qsub_data))
            for useful_log_file_name in useful_log_file_list:
                ans = dict()
                for count in xrange(1,1+POLLING_TOLERANCE):
                    ans = dict()
                    out_s = ''
                    try:
                        out_s = open(useful_log_file_name,'rt').read()
                        ans = json.loads(out_s.strip().split()[-1].decode('hex'))
                        ans['_raw_out'] = out_s
                        print "Success!"#, useful_log_file_name
                        break
                    except Exception as err:
                        if count < POLLING_TOLERANCE and 'Result: 256' not in out_s:
                            time.sleep(1)
                        else:
                            if index == POLLING_TOLERANCE:
                                print "Failure...................................."+" Could not find "+useful_log_file_name
                            else:
                                print "Success!" #, useful_log_file_name, repr(err)
                                #if 'Result: 256' not in out_s:
                                    #pdb.set_trace()
                                #assert 'Result: 256' in out_s, repr(out_s)+' '+str(os.path.exists(useful_log_file_name))+' '+runner+' '+script_name+' '+useful_log_file_name
                            ans['_raw_out']=str(err)
                            for k in map(lambda x: unicode(x+'_time'), list_dir_abs(kw['input_directory'])):
                                ans[k]=float('inf')
                            break
                program_execution_result_list.append( ans )
                try:
                    os.remove(useful_log_file_name)
                except:
                    pass
            try:
                os.remove(script_name)
            except:
                pass
            try:
                os.remove(runner)
            except:
                pass
            try:
                os.remove(qsub_log_file_name)
            except:
                pass
            #'''
        #print program_execution_result_list
        #print len(program_execution_result_list)
    else:
        for (i, full_name) in enumerate(approx_list):
            directory_for_this_approx = os.path.abspath(os.path.join(output_directory, 'results-'+label_names[i]+'/'))
#            output_images_directory_for_this_approx = os.path.join(directory_for_this_approx, 'output/')
            output_images_directory_for_this_approx = directory_for_this_approx
            if not os.path.exists(directory_for_this_approx):
                os.makedirs(directory_for_this_approx)
            if not os.path.exists(output_images_directory_for_this_approx):
                os.makedirs(output_images_directory_for_this_approx)
            print "Recording data for variant "+str(i)
            program_execution_result_list.append( run_program(program_name, approx_file=full_name, input_directory=input_images_directory, output_directory=output_images_directory_for_this_approx, debug_log_location=debug_log_location, **run_args) )
            print "Data for variant "+str(i)+" recorded."
            print 
    
    for (i, full_name) in enumerate(approx_list):
        file_name = label_names[i]
        print "Applying approximations for "+label_names[i]
        sys.stdout.flush()
        
        directory_for_this_approx = os.path.abspath(os.path.join(output_directory, 'results-'+label_names[i]+'/'))
#        if run_on_fir:
#            output_images_directory_for_this_approx = directory_for_this_approx
#        else: # cuts down on creating one more directory
#            output_images_directory_for_this_approx = os.path.join(directory_for_this_approx, 'output/')
        output_images_directory_for_this_approx = directory_for_this_approx
        
        if not run_on_fir:
            shutil.copy(full_name, directory_for_this_approx)
        
        display_out_image_prefix = os.path.join(output_images_directory_for_this_approx, image_to_be_displayed_prefix)
        display_output_image_name = display_out_image_prefix+'-out.png'
        display_cropped_filename = display_out_image_prefix+'-cropped.png'
        display_difference_filename = display_out_image_prefix+'-difference.png'
        display_cropped_difference_filename = display_out_image_prefix+'-cropped-difference.png'
        
        error_runner = ('_error_runner_'+''.join(map(str,[output_directory,os.getpid(),time.time()])).replace('\\','').replace('/',''))+'.py'
       
        program_execution_result = program_execution_result_list[i]
        
        try:
            mean_lab_absolute_all_images_matrix_to_append_val = []
            psnr_lab_absolute_all_images_matrix_to_append_val = []
            mean_lab_relative_all_images_matrix_to_append_val = []
            psnr_lab_relative_all_images_matrix_to_append_val = []
            
            mean_lab_absolute_all_images_matrix_to_append_val.append(file_name)
            psnr_lab_absolute_all_images_matrix_to_append_val.append(file_name)
            mean_lab_relative_all_images_matrix_to_append_val.append(file_name)
            psnr_lab_relative_all_images_matrix_to_append_val.append(file_name)
             
            total_run_time_absolute_dict = {}
            total_run_time_relative_dict = {}
            for key in program_execution_result.keys():
               if 'time' in key:
                   total_run_time_absolute_dict[key] = program_execution_result[key]

            for key in total_run_time_absolute_normal_dict.keys():
                total_run_time_relative_dict[key] = \
                                                      total_run_time_absolute_dict[key] / \
                                                      total_run_time_absolute_normal_dict[key]
            
            total_mean_lab_error_dict = {}
            total_psnr_error_dict = {}
            
            mean_lab = 0
            psnr_lab = 0
            
            for index_2, (e,e2) in enumerate(zip(map(lambda x: x[:-4]+'-out.png',input_images_list), map(lambda x: os.path.join(input_images_directory,x),input_images_list))):
                for count in xrange(POLLING_TOLERANCE):
                    try:
                         current_mean_lab = imdist.get_distance('mean','lab', os.path.join(os.path.abspath(output_images_directory_for_this_approx), e), os.path.join(os.path.abspath(output_images_directory_for_no_approx), e))
                         current_psnr_lab = imdist.get_distance('psnr','lab', os.path.join(os.path.abspath(output_images_directory_for_this_approx), e), os.path.join(os.path.abspath(output_images_directory_for_no_approx), e))
                         print "Success!"
                         break
                    except IOError as err:
                         if count == POLLING_TOLERANCE-1 and index_2 == 0:
                             print "Image not found."
                             raise 
                         time.sleep(1)
                         pass
	        
                total_mean_lab_error_dict[e2+'_mean_lab_error'] = current_mean_lab
                total_psnr_error_dict[e2+'_psnr_lab_error'] = current_psnr_lab
                
                mean_lab += current_mean_lab
                psnr_lab += current_psnr_lab
                error_txt_file = open(os.path.join(output_images_directory_for_this_approx, e[:-4]+'-error.txt'), 'w')
                error_txt_file.write("Mean LAB: "+str(current_mean_lab)+'\n')
                error_txt_file.write("PSNR LAB: "+str(current_psnr_lab))
                error_txt_file.close()
                
                mean_lab_absolute_all_images_matrix_to_append_val.append(total_run_time_absolute_dict[e2+'_time'])
                psnr_lab_absolute_all_images_matrix_to_append_val.append(total_run_time_absolute_dict[e2+'_time'])
                mean_lab_relative_all_images_matrix_to_append_val.append(total_run_time_relative_dict[e2+'_time'])
                psnr_lab_relative_all_images_matrix_to_append_val.append(total_run_time_relative_dict[e2+'_time'])
                
                mean_lab_absolute_all_images_matrix_to_append_val.append(total_mean_lab_error_dict[e2+'_mean_lab_error'])
                psnr_lab_absolute_all_images_matrix_to_append_val.append(total_psnr_error_dict[e2+'_psnr_lab_error'])
                mean_lab_relative_all_images_matrix_to_append_val.append(total_mean_lab_error_dict[e2+'_mean_lab_error'])
                psnr_lab_relative_all_images_matrix_to_append_val.append(total_psnr_error_dict[e2+'_psnr_lab_error'])
            
            mean_lab /= len(input_images_list)
            psnr_lab /= len(input_images_list)
            
            current_ans_absolute = dict(total_run_time_absolute_dict)
            current_ans_absolute['approx'] = file_name
            current_ans_absolute['error'] = error_dist if create_error_figure else mean_lab
           
            current_ans_relative = dict(total_run_time_relative_dict)
            current_ans_relative['approx'] = file_name
            current_ans_relative['error'] = error_dist if create_error_figure else mean_lab
            
            if (create_error_figure):
                error_dist = program_execution_result['error']
            
            for input_image in input_images_list:
                out_image_prefix = os.path.join(output_images_directory_for_this_approx, input_image[:-4])
                output_image_name = out_image_prefix+'-out.png'
                
                cropped_filename = out_image_prefix+'-cropped.png'
                difference_filename = out_image_prefix+'-difference.png'
                cropped_difference_filename = out_image_prefix+'-cropped-difference.png'
                
                # Save cropped image
                current_output_image = Image.open(output_image_name)
                width, height = current_output_image.size
                cropped_image = current_output_image.crop((int(width*0.45),int(height*0.45),int(width*0.55),int(height*0.55)))
                cropped_image.load()
                cropped_image.save(cropped_filename)
                #calculate difference images
                difference_image_array = imread(os.path.join(output_images_directory_for_no_approx,input_image[:-4]+'-out.png')) # difference image is initially the normal unapprox image
                current_output_image_array = imread(output_image_name)
                
                difference_image = numpy.sqrt(numpy.mean((difference_image_array-current_output_image_array)**2,2)) # L2 difference
                difference_image = difference_image/numpy.max(difference_image.flatten())
                imwrite(difference_image, difference_filename)
                difference_image = Image.open(difference_filename)
                
                cropped_difference_image = difference_image.crop((int(width*0.45),int(height*0.45),int(width*0.55),int(height*0.55)))
                cropped_difference_image.save(cropped_difference_filename)
            html_addon = ''
        except Exception, err:
            print err 
            print 'Problem applying approximations in '+file_name
            for key in total_run_time_absolute_normal_dict.keys():
                total_run_time_absolute_dict[key] = inf
                total_run_time_relative_dict[key] = inf
            
            current_ans_absolute = dict(total_run_time_absolute_dict)
            current_ans_absolute['approx'] = file_name
            current_ans_absolute['error'] = inf
            
            current_ans_relative = dict(total_run_time_relative_dict)
            current_ans_relative['approx'] = file_name
            current_ans_relative['error'] = inf
            
            if debug_log_location is not None:
                traceback_directory = os.path.join(os.path.abspath(debug_log_location),'traceback_log_files')
                if not os.path.exists(traceback_directory):
                    os.makedirs(traceback_directory)
                with open(os.path.join(traceback_directory, file_name.replace('.','_')+'_traceback.txt'), 'wt') as f:
                    traceback.print_exc(file=f)
            if verbose:
                traceback.print_exc()
                print
            if (create_error_figure):
                error_dist = float('inf')
            mean_lab = float('inf')
            psnr_lab = 0
            html_addon = ("""
Approximations for """+file_name+"""\n<BR>')
ERROR!!!
<BR>
<BR>
""")
        
        html_code += html_addon
        
        mean_lab_absolute_all_images_matrix.append(mean_lab_absolute_all_images_matrix_to_append_val)
        psnr_lab_absolute_all_images_matrix.append(psnr_lab_absolute_all_images_matrix_to_append_val)
        mean_lab_relative_all_images_matrix.append(mean_lab_relative_all_images_matrix_to_append_val)
        psnr_lab_relative_all_images_matrix.append(psnr_lab_relative_all_images_matrix_to_append_val)
        
        ans_absolute.append(current_ans_absolute)
        ans_relative.append(current_ans_relative)
        
        average_total_run_time_absolute = 0
        average_total_run_time_relative = 0
        count = 0
        for key in total_run_time_absolute_normal_dict.keys():
            if key not in ['error','approx']:
                average_total_run_time_absolute += total_run_time_absolute_dict[key]
                average_total_run_time_relative += total_run_time_relative_dict[key]
                count += 1
        average_total_run_time_absolute /= float(count)
        average_total_run_time_relative /= float(count)
        
        total_time_absolute_x = numpy.append(total_time_absolute_x, [average_total_run_time_absolute])
        total_time_relative_x = numpy.append(total_time_relative_x, [average_total_run_time_relative])
        mean_lab_y = numpy.append(mean_lab_y, [mean_lab])
        psnr_lab_y = numpy.append(psnr_lab_y, [psnr_lab])
        
        if (create_error_figure):
            error_subplot_absolute.annotate(file_name, (average_total_run_time_absolute, error_dist))
            error_subplot_relative.annotate(file_name, (average_total_run_time_relative, error_dist))
            error_y = numpy.append(error_y, [error_dist])
        
        error_dist_str = ''
        if create_error_figure:
            error_dist_str = 'Error: ' + str(error_dist) + '<br>'
        
        html_code += ("""
<hr size=2>
Approximations for """+file_name+"""
<BR>
<pre>""" + open(full_name, 'rt').read() + """</pre>
Average Total Absolute Run Time: """+str(average_total_run_time_absolute)+""" sec
<BR>
Average Total Relative Run Time: """+str(average_total_run_time_relative)+""" (relative)
<BR>
Average Mean LAB Distance: """+str(mean_lab)+"""
<BR>
Average PSNR LAB Distance: """+str(psnr_lab)+"""
<BR><BR>
"""+error_dist_str+os.path.relpath(display_output_image_name,output_directory)+'''
<BR>
<img src="'''+os.path.relpath(display_output_image_name,output_directory)+'''">
<BR>
<BR>
'''+os.path.relpath(display_cropped_filename,output_directory)+'''
<BR>
<img src="'''+os.path.relpath(display_cropped_filename,output_directory)+'''">
<BR>
<BR>
'''+os.path.relpath(display_difference_filename,output_directory)+'''
<BR>
<img src="'''+os.path.relpath(display_difference_filename,output_directory)+'''">
<BR>
<BR>
'''+os.path.relpath(display_cropped_difference_filename,output_directory)+'''
<BR>
<img src="'''+os.path.relpath(display_cropped_difference_filename,output_directory)+'''">
<BR>
<BR>
<BR>
<BR>
''')
#    if not run_on_fir:
    if True:
        for matrix, rel_csv_location in [ (mean_lab_absolute_all_images_matrix,'visualization_data_mean_lab_absolute_all_images.csv'),
                                          (psnr_lab_absolute_all_images_matrix,'visualization_data_psnr_lab_absolute_all_images.csv'),
                                          (mean_lab_relative_all_images_matrix,'visualization_data_mean_lab_relative_all_images.csv'),
                                          (psnr_lab_relative_all_images_matrix,'visualization_data_psnr_lab_relative_all_images.csv') ]:
            with open(os.path.join(output_directory,rel_csv_location), 'wt') as f:
                f.write( 'Approx File' )
                for time_label in sorted(total_run_time_absolute_normal_dict.keys()):
                    f.write( ', ' )
                    f.write( time_label )
                    f.write( ', ' )
                    if 'psnr_lab' in rel_csv_location:
                        f.write( time_label.replace('_time','_psnr_lab_error') )
                    elif 'mean_lab' in rel_csv_location:
                        f.write( time_label.replace('_time','_mean_lab_error') )
                f.write( '\n' )
                for e in matrix:
                    f.write(', '.join(map(str,e))+'\n')
    
        visualization_data_text_file = open(os.path.join(output_directory,'visualization_data.html'),'w')
        visualization_data_text_file.write(html_code)
        visualization_data_text_file.close()
        
        plot(mean_lab_subplot_absolute, list(total_time_absolute_x) + [average_total_run_time_absolute_normal], list(mean_lab_y) + [0.0], label_names + [normal_run_str])
        plot(mean_lab_subplot_relative, list(total_time_relative_x) + [1.0], list(mean_lab_y) + [0.0], label_names + [normal_run_str])
        plot(psnr_lab_subplot_absolute, total_time_absolute_x, psnr_lab_y, label_names)
        plot(psnr_lab_subplot_relative, total_time_relative_x, psnr_lab_y, label_names)
        
        mean_lab_subplot_absolute.set_xlim(left=0)
        mean_lab_subplot_absolute.set_ylim(bottom=0)
        
        mean_lab_subplot_relative.set_xlim(left=0)
        mean_lab_subplot_relative.set_ylim(bottom=0)
        
        psnr_lab_subplot_absolute.set_xlim(left=0)
        psnr_lab_subplot_relative.set_xlim(left=0)
        
        mean_lab_subplot_absolute.set_xlabel('Time (fraction of running time of exact and unapproximated program)')
        psnr_lab_subplot_relative.set_xlabel('Time (fraction of running time of exact and unapproximated program)')
        
        mean_lab_subplot_absolute.set_xlabel('Time (seconds)')
        psnr_lab_subplot_relative.set_xlabel('Time (relative)')
        
        mean_lab_subplot_absolute.set_title('Accuracy (Mean LAB Distance) and Performance of Approximations')
        psnr_lab_subplot_absolute.set_title('Accuracy (PSNR LAB Distance) and Performance of Approximations')
        mean_lab_subplot_absolute.set_ylabel('Mean LAB Distance')
        psnr_lab_subplot_absolute.set_ylabel('PSNR LAB Distance')
        
        mean_lab_subplot_relative.set_title('Accuracy (Mean LAB Distance) and Performance of Approximations')
        psnr_lab_subplot_relative.set_title('Accuracy (PSNR LAB Distance) and Performance of Approximations')
        mean_lab_subplot_relative.set_ylabel('Mean LAB Distance')
        psnr_lab_subplot_relative.set_ylabel('PSNR LAB Distance')
        
        mean_lab_fig_absolute.savefig(os.path.abspath(os.path.join(output_directory,'mean_lab_absolute.png')))
        mean_lab_fig_relative.savefig(os.path.abspath(os.path.join(output_directory,'mean_lab_relative.png')))
        
        psnr_lab_fig_absolute.savefig(os.path.abspath(os.path.join(output_directory,'psnr_lab_absolute.png')))
        psnr_lab_fig_relative.savefig(os.path.abspath(os.path.join(output_directory,'psnr_lab_relative.png')))
        
        with open(os.path.join(output_directory,'visualization_data_absolute.csv'), 'wt') as f:
            f.write('Approx File, Time, Mean Lab, PSNR Lab' + (', Error' if create_error_figure else '') + '\n')
            f.write('Normal, %f, 0, 0' % average_total_run_time_absolute_normal + (', %f'%error_normal if create_error_figure else '') + '\n')
            for i in range(len(total_time_absolute_x)):
                f.write('%s, %f, %f, %f' % (label_names[i], total_time_absolute_x[i], mean_lab_y[i], psnr_lab_y[i]))
                if create_error_figure:
                    f.write(', %f' % error_y[i])
                f.write('\n')
        
        with open(os.path.join(output_directory,'visualization_data_relative.csv'), 'wt') as f:
            f.write('Approx File, Time, Mean Lab, PSNR Lab' + (', Error' if create_error_figure else '') + '\n')
            f.write('Normal, %f, 0, 0' % 1.0 + (', %f'%error_normal if create_error_figure else '') + '\n')
            for i in range(len(total_time_relative_x)):
                f.write('%s, %f, %f, %f' % (label_names[i], total_time_relative_x[i], mean_lab_y[i], psnr_lab_y[i]))
                if create_error_figure:
                    f.write(', %f' % error_y[i])
                f.write('\n')
        
        with open(os.path.join(output_directory,'visualization_data_absolute_sample_importance_only.csv'), 'wt') as f:
            f.write('Approx File, Time, Mean Lab, PSNR Lab' + (', Error' if create_error_figure else '') + '\n')
            f.write('Normal, %f, 0, 0' % average_total_run_time_absolute_normal + (', %f'%error_normal if create_error_figure else '') + '\n')
            for i in range(len(total_time_absolute_x)):
                approx_code = open(approx_list[i],'r').read()
                if 'sample_importance' in approx_code and not 'sample_grid' in approx_code:
                    f.write('%s, %f, %f, %f' % (label_names[i], total_time_absolute_x[i], mean_lab_y[i], psnr_lab_y[i]))
                    if create_error_figure:
                        f.write(', %f' % error_y[i])
                    f.write('\n')
        
        with open(os.path.join(output_directory,'visualization_data_relative_sample_importance_only.csv'), 'wt') as f:
            f.write('Approx File, Time, Mean Lab, PSNR Lab' + (', Error' if create_error_figure else '') + '\n')
            f.write('Normal, %f, 0, 0' % average_total_run_time_absolute_normal + (', %f'%error_normal if create_error_figure else '') + '\n')
            for i in range(len(total_time_relative_x)):
                approx_code = open(approx_list[i],'r').read()
                if 'sample_importance' in approx_code and not 'sample_grid' in approx_code:
                    f.write('%s, %f, %f, %f' % (label_names[i], total_time_relative_x[i], mean_lab_y[i], psnr_lab_y[i]))
                    if create_error_figure:
                        f.write(', %f' % error_y[i])
                    f.write('\n')
        
        with open(os.path.join(output_directory,'visualization_data_absolute_sample_grid_only.csv'), 'wt') as f:
            f.write('Approx File, Time, Mean Lab, PSNR Lab' + (', Error' if create_error_figure else '') + '\n')
            f.write('Normal, %f, 0, 0' % average_total_run_time_absolute_normal + (', %f'%error_normal if create_error_figure else '') + '\n')
            for i in range(len(total_time_absolute_x)):
                approx_code = open(approx_list[i],'r').read()
                if 'sample_grid' in approx_code and not 'sample_importance' in approx_code:
                    f.write('%s, %f, %f, %f' % (label_names[i], total_time_absolute_x[i], mean_lab_y[i], psnr_lab_y[i]))
                    if create_error_figure:
                        f.write(', %f' % error_y[i])
                    f.write('\n')
        
        with open(os.path.join(output_directory,'visualization_data_relative_sample_grid_only.csv'), 'wt') as f:
            f.write('Approx File, Time, Mean Lab, PSNR Lab' + (', Error' if create_error_figure else '') + '\n')
            f.write('Normal, %f, 0, 0' % average_total_run_time_absolute_normal + (', %f'%error_normal if create_error_figure else '') + '\n')
            for i in range(len(total_time_relative_x)):
                approx_code = open(approx_list[i],'r').read()
                if 'sample_grid' in approx_code and not 'sample_importance' in approx_code:
                    f.write('%s, %f, %f, %f' % (label_names[i], total_time_relative_x[i], mean_lab_y[i], psnr_lab_y[i]))
                    if create_error_figure:
                        f.write(', %f' % error_y[i])
                    f.write('\n')
        
        mean_lab_pareto_fig_absolute, mean_lab_pareto_subplot_absolute = matplotlib.pyplot.subplots()
        psnr_lab_pareto_fig_absolute, psnr_lab_pareto_subplot_absolute = matplotlib.pyplot.subplots()
        mean_lab_pareto_fig_relative, mean_lab_pareto_subplot_relative = matplotlib.pyplot.subplots()
        psnr_lab_pareto_fig_relative, psnr_lab_pareto_subplot_relative = matplotlib.pyplot.subplots()
        
        mean_lab_pareto_indices = get_pareto(mean_lab_y, total_time_absolute_x)
        psnr_lab_pareto_indices = get_pareto(1/psnr_lab_y, total_time_absolute_x)

        with open(os.path.join(output_directory,'visualization_data_mean_lab_pareto_absolute.csv'), 'wt') as f:
            f.write('Approx File, Time, Mean Lab, PSNR Lab' + (', Error' if create_error_figure else '') + '\n')
            f.write('Normal, %f, 0, 0' % average_total_run_time_absolute_normal + (', %f'%error_normal if create_error_figure else '') + '\n')
            for i in mean_lab_pareto_indices:
                f.write('%s, %f, %f, %f' % (label_names[i], total_time_absolute_x[i], mean_lab_y[i], psnr_lab_y[i]))
                if create_error_figure:
                    f.write(', %f' % error_y[i])
                f.write('\n')
            
        with open(os.path.join(output_directory,'visualization_data_mean_lab_pareto_relative.csv'), 'wt') as f:
            f.write('Approx File, Time, Mean Lab, PSNR Lab' + (', Error' if create_error_figure else '') + '\n')
            f.write('Normal, %f, 0, 0' % 1.0 + (', %f'%error_normal if create_error_figure else '') + '\n')
            for i in mean_lab_pareto_indices:
                f.write('%s, %f, %f, %f' % (label_names[i], total_time_relative_x[i], mean_lab_y[i], psnr_lab_y[i]))
                if create_error_figure:
                    f.write(', %f' % error_y[i])
                f.write('\n')

        with open(os.path.join(output_directory,'visualization_data_psnr_lab_pareto_absolute.csv'), 'wt') as f:
            f.write('Approx File, Time, Mean Lab, PSNR Lab' + (', Error' if create_error_figure else '') + '\n')
            f.write('Normal, %f, 0, 0' % average_total_run_time_absolute_normal + (', %f'%error_normal if create_error_figure else '') + '\n')
            for i in psnr_lab_pareto_indices:
                f.write('%s, %f, %f, %f' % (label_names[i], total_time_absolute_x[i], mean_lab_y[i], psnr_lab_y[i]))
                if create_error_figure:
                    f.write(', %f' % error_y[i])
                f.write('\n')
        
        with open(os.path.join(output_directory,'visualization_data_psnr_lab_pareto_relative.csv'), 'wt') as f:
            f.write('Approx File, Time, Mean Lab, PSNR Lab' + (', Error' if create_error_figure else '') + '\n')
            f.write('Normal, %f, 0, 0' % 1.0 + (', %f'%error_normal if create_error_figure else '') + '\n')
            for i in psnr_lab_pareto_indices:
                f.write('%s, %f, %f, %f' % (label_names[i], total_time_relative_x[i], mean_lab_y[i], psnr_lab_y[i]))
                if create_error_figure:
                    f.write(', %f' % error_y[i])
                f.write('\n')
        
        plot(mean_lab_pareto_subplot_absolute, list(total_time_absolute_x[mean_lab_pareto_indices]) + [average_total_run_time_absolute_normal], list(mean_lab_y[mean_lab_pareto_indices]) + [0.0], list(numpy.array(label_names)[mean_lab_pareto_indices]) + [normal_run_str])
        plot(mean_lab_pareto_subplot_relative, list(total_time_relative_x[mean_lab_pareto_indices]) + [1.0], list(mean_lab_y[mean_lab_pareto_indices]) + [0.0], list(numpy.array(label_names)[mean_lab_pareto_indices]) + [normal_run_str])
        
        plot(psnr_lab_pareto_subplot_absolute, total_time_absolute_x[psnr_lab_pareto_indices], psnr_lab_y[psnr_lab_pareto_indices], numpy.array(label_names)[psnr_lab_pareto_indices])
        plot(psnr_lab_pareto_subplot_relative, total_time_relative_x[psnr_lab_pareto_indices], psnr_lab_y[psnr_lab_pareto_indices], numpy.array(label_names)[psnr_lab_pareto_indices])
        
        mean_lab_pareto_subplot_absolute.set_title('Pareto Frontier of Approximation Accuracy (Mean LAB Distance) and Approximation Performance (Average Running Time)')
        mean_lab_pareto_subplot_absolute.set_xlabel('Time (seconds)')
        mean_lab_pareto_subplot_absolute.set_ylabel('Mean LAB Distance')
        psnr_lab_pareto_subplot_absolute.set_title('Pareto Frontier of Approximation Accuracy (PSNR LAB Distance) and Approximation Performance (Average Running Time)')
        psnr_lab_pareto_subplot_absolute.set_xlabel('Time (seconds)')
        psnr_lab_pareto_subplot_absolute.set_ylabel('PSNR LAB Distance')
        
        mean_lab_pareto_subplot_relative.set_title('Pareto Frontier of Approximation Accuracy (Mean LAB Distance) and Approximation Performance (Average Running Time)')
        mean_lab_pareto_subplot_relative.set_xlabel('Time (relative)')
        mean_lab_pareto_subplot_relative.set_ylabel('Mean LAB Distance')
        psnr_lab_pareto_subplot_relative.set_title('Pareto Frontier of Approximation Accuracy (PSNR LAB Distance) and Approximation Performance (Average Running Time)')
        psnr_lab_pareto_subplot_relative.set_xlabel('Time (relative)')
        psnr_lab_pareto_subplot_relative.set_ylabel('PSNR LAB Distance')
        
        if (create_error_figure):
            error_subplot.scatter(total_time_x, error_y)
            error_fig.savefig(output_directory+'error.png')
            error_pareto_fig, error_pareto_subplot = matplotlib.pyplot.subplots()
            error_pareto_indices = get_pareto(error_y, total_time_x)
            for i in error_pareto_indices:
                error_pareto_subplot_absolute.annotate(label_names[i], (total_time_absolute_x[i],error_y[i]))
                error_pareto_subplot_relative.annotate(label_names[i], (total_time_relative_x[i],error_y[i]))
            error_pareto_subplot_absolute.scatter(total_time_x[error_pareto_indices], error_y[error_pareto_indices])
            error_pareto_fig_absolute.savefig(os.path.join(output_directory,'error_pareto_absolute.png'))
            error_pareto_subplot_relative.scatter(total_time_x[error_pareto_indices], error_y[error_pareto_indices])
            error_pareto_fig_relative.savefig(os.path.join(output_directory,'error_pareto_relative.png'))
        
        mean_lab_pareto_fig_absolute.savefig(os.path.join(output_directory,'mean_lab_pareto_absolute.png'))
        psnr_lab_pareto_fig_absolute.savefig(os.path.join(output_directory,'psnr_lab_pareto_absolute.png'))
        mean_lab_pareto_fig_relative.savefig(os.path.join(output_directory,'mean_lab_pareto_relative.png'))
        psnr_lab_pareto_fig_relative.savefig(os.path.join(output_directory,'psnr_lab_pareto_relative.png'))
        
        if open_html:
            open_file(output_directory+'visualization_data.html')
    
    print "Visualization Complete."
    print
    
    ans = ans_relative if use_relative_times_for_return_value else ans_absolute
    
    if dump_ans:
        pickle.dump( ans, open( os.path.join(output_directory,"visualize_results_ans_dump.p"), "wb" ) )
    
    matplotlib.pyplot.close('all')
    
    return ans #, no_approx_execution_result
    
def main():
    if (len(sys.argv) < 4):
        usage()
    
    approx_directory = sys.argv[1]
    output_directory = sys.argv[2]
    program_name = sys.argv[3]
    
    if (not os.path.isdir(approx_directory)):
        print "Problem with approx_directory ("+approx_directory+")."
        sys.exit(1)
    
    approx_list = [os.path.abspath(filename) for filename in glob.glob(os.path.join(approx_directory, '*.approx'))]
    
    input_folder=DEFAULT_INPUT_IMAGES_DIRECTORY
    forbid_importance_sampling = False
    forbid_grid_sampling = False
    
    if '-input_folder' in sys.argv and sys.argv.index('-input_folder')+1 < len(sys.argv):
        input_folder = os.path.abspath(sys.argv[sys.argv.index('-input_folder')+1])
    if '-no_importance_sampling' in sys.argv and sys.argv.index('-no_importance_sampling')+1 < len(sys.argv):
        forbid_importance_sampling = '1'==(sys.argv[sys.argv.index('-no_importance_sampling')+1])
    if '-no_grid_sampling' in sys.argv and sys.argv.index('-no_grid_sampling')+1 < len(sys.argv):
        forbid_grid_sampling = '1'==(sys.argv[sys.argv.index('-no_grid_sampling')+1])
    
    visualize_results(approx_list, output_directory, program_name, input_images_directory=input_folder, no_importance_sampling=forbid_importance_sampling, no_grid_sampling=forbid_grid_sampling,run_on_fir=('hermes' in platform.node()))
    
if __name__ == '__main__':
    main()

