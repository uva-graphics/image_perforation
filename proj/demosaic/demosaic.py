#!/usr/bin/python

# Trivial blur application

import sys; sys.path += ['../compiler']
from approx import *
import os
#import numpy

#import cv2
#import numpy as np


approx_loops = {'loop_gx':          'foreach',
                'inner_loop_gx':    'for',
                'loop_gout':        'foreach',
                'inner_loop_gout':  'for',
                'loop_bx':          'foreach',
                'inner_loop_bx':    'for',
                'loop_bout':        'foreach',
                'inner_loop_bout':  'for',
                'loop_rx':          'foreach',
                'inner_loop_rx':    'for',
                'loop_rout':        'foreach',
                'inner_loop_rout':  'for',
                'loop_combine':     'foreach'}

R_COORD = 0
G_COORD = 1
B_COORD = 2

bounds_check = False

@makenames
def create_program(is_vectorize=True, approximation_file_name=''):
    if is_vectorize:
        kw = dict(sizes=(None, None, 4), vectorize=2)
       
    else:
        kw = dict(sizes=(None, None, 3))
       
    Real = Float(32)
    Image = Array(Real, 3, **kw)
  

    h = 1
    #dxL = numpy.array([-1, 0, 1])

    with Program() as program:

        with Function() as main_func:
            input = Argument(Image)
            output = Argument(Image)
            #printf('input: %d x %d x %d\n', input.height(), input.width(), input.channels())

            output.resize(input.sizes())

            input_r = Var(Array(Real, 3, sizes=(None, None, 1)))
            input_r.resize([input.height(), input.width(), 1])
            input_g = Var(Array(Real, 3, sizes=(None, None, 1)))
            input_g.resize([input.height(), input.width(), 1])
            input_b = Var(Array(Real, 3, sizes=(None, None, 1)))
            input_b.resize([input.height(), input.width(), 1])

            temp_r = Var(Array(Real, 3, sizes=(None, None, 1)))
            temp_r.resize([input.height(), input.width(), 1])
            temp_g = Var(Array(Real, 3, sizes=(None, None, 1)))
            temp_g.resize([input.height(), input.width(), 1])
            temp_b = Var(Array(Real, 3, sizes=(None, None, 1)))
            temp_b.resize([input.height(), input.width(), 1])

            output_r = Var(Array(Real, 3, sizes=(None, None, 1)))
            output_r.resize([input.height(), input.width(), 1])
            output_g = Var(Array(Real, 3, sizes=(None, None, 1)))
            output_g.resize([input.height(), input.width(), 1])
            output_b = Var(Array(Real, 3, sizes=(None, None, 1)))
            output_b.resize([input.height(), input.width(), 1])

            temp = Var(Image)
            temp.resize(input.sizes())
            
            filter_stencil = Var(Array(Real, 2, **kw))
            filter_stencil.resize([1,3])

            # two interleaved 3-tap linear reconstrution filters [0.5 0.0 0.5] and [0.0 1.0 0.0]
            A = Var(Array(Real, 2, **kw))
            A.resize([1,6])
            A[0,0]=0.5
            A[0,1]=0.0
            A[0,2]=0.0
            A[0,3]=1.0
            A[0,4]=0.5
            A[0,5]=0.0

            x = Var()  # Var(Int())
            y = Var()
            
            CodeFragment("""static int is_init=0; if (!is_init) { is_init=1; temp.clear(); output.clear(); temp_r.clear(); temp_g.clear(); temp_b.clear(); output_r.clear(); output_g.clear(); output_b.clear(); }""")

            # Green channel
            with ForEach((y, x), temp_g, input_g, start=(1, 1), stop=(input.height()-1, input.width()-1)) as loop_gx:
                temp_g[y, x] = 0.0
                dx = Var();
                with For(dx, 0, 3) as inner_loop_gx:
                    weight = Var(Real, A[0,dx*2+((y+1+x+1)%2)])
                    temp_g[y, x] = temp_g[y, x] + weight*input[y, x+dx-1, G_COORD]

            with ForEach((y, x), output_g, temp_g, start=(2, 2), stop=(input.height()-2, input.width()-2)) as loop_gout:
                output_g[y, x] = 0.0
                dx = Var();
                with For(dx, 0, 3) as inner_loop_gout:
                    weight = Var(Real, A[0,dx*2+(y+1+x+1)%2])
                    output_g[y, x] = output_g[y, x] + weight*temp_g[y+dx-1, x]

            # Blue channel
            with ForEach((y, x), temp_b, input_b, start=(1, 1), stop=(input.height()-1, input.width()-1), step=(2,1)) as loop_bx:
                temp_b[y, x] = 0.0
                dx = Var();
                with For(dx, 0, 3) as inner_loop_bx:
                    weight = Var(Real, A[0,dx*2+(x%2)])
                    temp_b[y, x] = temp_b[y, x] + weight*input[y, x+dx-1, B_COORD]

            with ForEach((y, x), output_b, temp_b, start=(2, 2), stop=(input.height()-2, input.width()-2)) as loop_bout:
                dx = Var();
                output_b[y, x] = 0.0
                with For(dx, 0, 3) as inner_loop_bout:
                    weight = Var(Real, A[0,dx*2+(y%2)])
                    output_b[y, x] = output_b[y, x] + weight*temp_b[y+dx-1, x]

            # Red channel
            with ForEach((y, x), temp_r, input_r, start=(0, 1), stop=(input.height(), input.width()-1), step=(2,1)) as loop_rx:
                temp_r[y, x] = 0.0
                dx = Var();
                with For(dx, 0, 3) as inner_loop_rx:
                    weight = Var(Real, A[0,dx*2+((x+1)%2)])
                    temp_r[y, x] = temp_r[y, x] + weight*input[y, x+dx-1, R_COORD]

            with ForEach((y, x), output_r, temp_r, start=(2, 2), stop=(input.height()-2, input.width()-2)) as loop_rout:
#                    output[y, x] = 0.0
                output_r[y, x] = 0.0
                dx = Var();
                with For(dx, 0, 3) as inner_loop_rout:
                    weight = Var(Real, A[0,dx*2+((y+1)%2)])
                    output_r[y, x] = output_r[y, x] + weight*temp_r[y+dx-1, x]

            with ForEach((y, x), output, output_r) as loop_combine:
                output[y, x, R_COORD] = output_r[y, x]
                output[y, x, G_COORD] = output_g[y, x]
                output[y, x, B_COORD] = output_b[y, x]

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



