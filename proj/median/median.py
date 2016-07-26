#!/usr/bin/python

# Median filter application

import sys; sys.path += ['../compiler']
from approx import *
import os
import numpy

approx_loops = {'loop_pixels': 'foreach', 
                'median_y_loop': 'for',
                'median_x_loop': 'for' }

RUN_PARALLEL = False

R_COORD = 0
G_COORD = 1
B_COORD = 2

@makenames
def create_program(is_vectorize=True, approximation_file_name=''):
    if is_vectorize:
        kw = dict(sizes=(None, None, 4), vectorize=2)
    else:
        kw = dict(sizes=(None, None, 3))
    Real = Float(32)
    
    Image = Array(Real, 3, **kw)

    kernel_width = 9
    half_kernel_width = int(kernel_width/2)
    
    with Program() as program:
        
        CodeFragment('''
float median(vector<float> vec) {
    std::sort(vec.begin(), vec.end());
    int median_index = vec.size()/2;
    return vec[median_index];
}
''')
        
        with Function() as main_func:
            input = Argument(Image)
            output = Argument(Image)
            output.resize(input.sizes())
            output.clear()
            
            x = Var()
            y = Var()
            
            with ForEach((y, x), output, input, parallel=RUN_PARALLEL) as loop_pixels:
                
                r = Var()
                c = Var()
                CodeFragment('''
std::vector<float> red_values = std::vector<float>();
std::vector<float> green_values = std::vector<float>();
std::vector<float> blue_values = std::vector<float>();
//std::cout << "|||red_values.size(): " << red_values.size() << std::endl;
''')
                with For(r, -half_kernel_width, half_kernel_width+1, allow_random=False) as median_y_loop:
                    with For(c, -half_kernel_width, half_kernel_width+1, allow_random=False) as median_x_loop:
                        
                        red = Var(Float(32))
                        green = Var(Float(32))
                        blue = Var(Float(32))
                        
                        with If(And(And(x+c>=0,x+c<input.width()),And(y+r>=0,y+r<input.height()))):
                            Assign(red, input[y+r,x+c,R_COORD])
                            Assign(green, input[y+r,x+c,G_COORD])
                            Assign(blue, input[y+r,x+c,B_COORD])
                            
                            CodeFragment('''
red_values.push_back(red);
green_values.push_back(green);
blue_values.push_back(blue);
    ''')
                median_red = Var(Float(32))
                median_green = Var(Float(32))
                median_blue = Var(Float(32))
                
                CodeFragment('''
median_red = median(red_values);
median_green = median(green_values);
median_blue = median(blue_values);
''')
                output[y,x,R_COORD] = median_red
                output[y,x,G_COORD] = median_green
                output[y,x,B_COORD] = median_blue
                
    apply_approximations_from_file(globals(), locals(), approximation_file_name)
    
    return (program, locals())

def main(approx_file="", output_directory=os.path.abspath('./output/'), input_directory=os.path.abspath('./input/'), parallel=False, is_vectorize=False, kw0={}):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    kw = dict(parallel=parallel, is_vectorize=is_vectorize, debug=False, **kw0)
    (program, locals_d) = create_program(is_vectorize=kw['is_vectorize'], approximation_file_name=approx_file)
    return compile_and_run_on_several_images(approx_file=approx_file, input_directory=input_directory, output_directory=output_directory, kw0=kw, program=program)

if __name__ == '__main__':
    parallel = '-parallel' in sys.argv
    is_vectorize = '-is_vectorize' in sys.argv
    main(parallel=parallel, is_vectorize=is_vectorize, **parse_app_commandline(sys.argv))

