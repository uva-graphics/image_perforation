#!/usr/bin/python

"""
TODO:
    redo approx_loops variable
"""

# Unsharp Mask

import sys; sys.path += ['../compiler']
from approx import *
import os
import numpy

approx_loops = {'loop_temp':   'foreach', 
                'loop_output': 'foreach', 
                'mask_combination_loop': 'foreach' }

bounds_check = False

@makenames
def create_program(is_vectorize=True, approximation_file_name=''):
    if is_vectorize:
        kw = dict(sizes=(None, None, 4), vectorize=2)
    else:
        kw = dict(sizes=(None, None, 3))
    
    Real = Float(32)
    Image = Array(Real, 3, **kw)

    sigma = 4.0
    h = 8
    dxL = range(-h, h+1)
    A = numpy.array([numpy.exp(-(dx*dx)/(2.0*sigma**2)) for dx in dxL])
    A = A / numpy.sum(A.flatten())

    with Program() as program:

        with Function() as main_func:
            input = Argument(Image)
            output = Argument(Image)
            output.resize(input.sizes())
            temp = Var(Image)
            temp.resize(input.sizes())
            
            mask = Var(Image)
            mask.resize(input.sizes())
            
            x = Var()
            y = Var()
            color = Var()
            
            if bounds_check:
                with ForEach((y, x), temp, input) as loop_temp:
                    with If(And(x-h >= 0, x+h < input.width())):
                        temp[y, x] = sum([A[dx+h]*input[y, x+dx] for dx in dxL])
                    with Else():
                        temp[y, x] = 0.0
                
                with ForEach((y, x), output, temp) as loop_output:
                    with If(And(And(y-h >= 0, y+h < input.height()),And(x-h >= 0, x+h < input.width()))):
                        output[y, x] = 2*input[y, x] - sum([A[dy+h]*temp[y+dy, x] for dy in dxL])
                    with Else():
                        output[y, x] = 0.0
                
            else:
                CodeFragment("""static int is_init=0; if (!is_init) { is_init=1; temp.clear(); output.clear(); }""")
                
                with ForEach((y, x), temp, input, start=(h, h), stop=(input.height()-h, input.width()-h)) as loop_temp:
                    temp[y, x] = sum([A[dx+h]*input[y, x+dx] for dx in dxL])
                
                with ForEach((y, x), mask, temp, start=(h, h), stop=(input.height()-h, input.width()-h)) as loop_output:
                    mask[y, x] = sum([A[dy+h]*temp[y+dy, x] for dy in dxL])
                
                with ForEach((y,x,color), output, mask) as mask_combination_loop:
                    sharpness_coefficient = 3.0
                    output[y, x,color] = sharpness_coefficient*input[y, x,color] + (1-sharpness_coefficient)*mask[y, x,color]
            
            
    apply_approximations_from_file(globals(), locals(), approximation_file_name)
    
    return (program, locals())

def main(approx_file="", output_directory=os.path.abspath('./output/'), input_directory=os.path.abspath('../images/train/'), parallel=False, is_vectorize=False, kw0={}):
    
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    kw = dict(parallel=parallel, is_vectorize=is_vectorize, debug=False, **kw0)
    (program, locals_d) = create_program(is_vectorize=kw['is_vectorize'], approximation_file_name=approx_file)
    
    return compile_and_run_on_several_images(approx_file=approx_file, input_directory=input_directory, output_directory=output_directory, kw0=kw, program=program)

if __name__ == '__main__':
    parallel = '-parallel' in sys.argv
    is_vectorize = '-is_vectorize' in sys.argv
    main(parallel=parallel, is_vectorize=is_vectorize, **parse_app_commandline(sys.argv))

