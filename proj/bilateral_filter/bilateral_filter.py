#!/usr/bin/python

# Bilateral filter application

import sys; sys.path += ['../compiler']
from approx import *
import os
import numpy

approx_loops = {'loop_pixels': 'foreach', 
                'loop_kernel': 'foreach' }

R_COORD = 0
G_COORD = 1
B_COORD = 2

RUN_PARALLEL = False

@makenames
def create_program(is_vectorize=True, approximation_file_name=''):
    if is_vectorize:
        kw = dict(sizes=(None, None, 4), vectorize=2)
    else:
        kw = dict(sizes=(None, None, 3))
    
    Real = Float(32)
    Image = Array(Real, 3, **kw)

    sigma_spatial = 4.0
    spatial_kernel_width = 9
    half_spatial_kernel_width = int(spatial_kernel_width)/2
    sigma_range = 0.08

    with Program() as program:
        
        with Function(Real) as G1D:
            g_x = Argument(Real)
            g_sigma = Argument(Real)
            Return(exp(-(g_x*g_x)/(2*g_sigma*g_sigma))/(g_sigma*sqrt(2*math.pi)))

        with Function(Real) as G2D:
            g_x = Argument(Real)
            g_y = Argument(Real)
            g_sigma = Argument(Real)
            Return(exp(-(g_y*g_y+g_x*g_x)/(2*g_sigma*g_sigma)) / (2*math.pi*g_sigma*g_sigma))
        
        with Function() as main_func:
            input = Argument(Image)
            output = Argument(Image)
            output.resize(input.sizes())
            output.clear()
            
            gaussian_spatial_kernel = Var(Array(Real, 2, **kw))
            gaussian_spatial_kernel.resize([spatial_kernel_width,spatial_kernel_width])
            
            x = Var()
            y = Var()
            
            with ForEach((y, x), gaussian_spatial_kernel, gaussian_spatial_kernel, parallel=RUN_PARALLEL):
                gaussian_spatial_kernel[y,x] = G2D(y,x,sigma_spatial)
            
            with ForEach((y, x), output, input, parallel=RUN_PARALLEL) as loop_pixels:
                total_weight = Var(Real, 0.0)
                
                r0 = Var()
                c0 = Var()
                with ForEach((r0, c0), gaussian_spatial_kernel, gaussian_spatial_kernel) as loop_kernel:
                    r = Var(Int(), r0-half_spatial_kernel_width)
                    c = Var(Int(), c0-half_spatial_kernel_width)
                    with If(And(And(x+c>=0,x+c<input.width()),And(y+r>=0,y+r<input.height()))):
                        weight = Var(Real, gaussian_spatial_kernel[r0,c0] * G1D((input[y,x,R_COORD]-input[y+r,x+c,R_COORD])*0.299+(input[y,x,G_COORD]-input[y+r,x+c,G_COORD])*0.587+(input[y,x,B_COORD]-input[y+r,x+c,B_COORD])*0.114,sigma_range))
                        Assign(total_weight, total_weight + weight)
                        
                        output[y,x,R_COORD] = output[y,x,R_COORD] + weight*input[y+r,x+c,R_COORD]
                        output[y,x,G_COORD] = output[y,x,G_COORD] + weight*input[y+r,x+c,G_COORD]
                        output[y,x,B_COORD] = output[y,x,B_COORD] + weight*input[y+r,x+c,B_COORD]
                
                output[y,x,R_COORD] = output[y,x,R_COORD] / (total_weight)
                output[y,x,G_COORD] = output[y,x,G_COORD] / (total_weight)
                output[y,x,B_COORD] = output[y,x,B_COORD] / (total_weight)
                
    
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

