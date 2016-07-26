#!/usr/bin/python

# Artistic blur application

import sys; sys.path += ['../compiler']
from approx import *
import os
import numpy

approx_loops = {'loop_blur':  'foreach',
                'loop_u':     'for',
                'loop_v':     'for'}

bounds_check = True

@makenames
def create_program(is_vectorize=True, approximation_file_name=''):
    if is_vectorize:
        kw = dict(sizes=(None, None, 4), vectorize=2)
    else:
        kw = dict(sizes=(None, None, 3))
    
    Real = Float(32)
    Image = Array(Real, 3, **kw)

    half_samples_u = 16#8#4
    half_samples_v = 8#4#2

    with Program() as program:

        with Function() as main_func:
            input = Argument(Image)
            output = Argument(Image)
            output.resize(input.sizes())
            output.clear()

            x = Var()
            y = Var()
            u = Var()
            v = Var()

            r_min = Var(Float(), output.width()/2*0.35)
            r_max = Var(Float(), sqrt((output.width()/2)**2 + (output.height()/2)**2))

            size0_u = Var(Float(), r_max*0.4)
            size0_v = Var(Float(), size0_u*0.5)

            with ForEach((y, x), output, input) as loop_blur:
                dx = Var(Int(), x-output.width()/2)
                dy = Var(Int(), y-output.height()/2)
                r = Var(Float(), sqrt(dx*dx+dy*dy))
                with If(r < r_min):
                    output[y, x] = input[y, x]
                with Else():
                    theta = Var(Float(), atan2(dy, dx))
                    dx_du = Var(Float(),  sin(theta))
                    dy_du = Var(Float(), -cos(theta))
                    dx_dv = Var(Float(), -dy_du)
                    dy_dv = Var(Float(),  dx_du)

                    size = Var(Float(), (r-r_min)/(r_max-r_min))
                    size_u = Var(Float(), size0_u*size)
                    size_v = Var(Float(), size0_v*size)

                    u0 = Var(Float(), sin(size*50.0)*size*1.0)
                    scale = Var(Float(), 1.0/(half_samples_u*2+1)/(half_samples_v*2+1))
                    with For(u, -half_samples_u, half_samples_u+1) as loop_u:
                        with For(v, -half_samples_v, half_samples_v+1) as loop_v:
                            src_x = Var(Float(), x+(u+u0)*dx_du*size_u/half_samples_u + v*dx_dv*size_v/half_samples_v)
                            src_y = Var(Float(), y+(u+u0)*dy_du*size_u/half_samples_u + v*dy_dv*size_v/half_samples_v)

                            src_xi = Var(Int(), src_x)
                            src_yi = Var(Int(), src_y)
                            src_xf = Var(Float(), src_x-src_xi)
                            src_yf = Var(Float(), src_y-src_yi)

                            with If(src_xi < 0):
                                Assign(src_xi, 0)
                                Assign(src_xf, 0.0)
                            with ElseIf(src_xi+1 >= input.width()):
                                Assign(src_xi, input.width()-2)
                                Assign(src_xf, 1.0)

                            with If(src_yi < 0):
                                Assign(src_yi, 0)
                                Assign(src_yf, 0.0)
                            with ElseIf(src_yi+1 >= input.height()):
                                Assign(src_yi, input.height()-2)
                                Assign(src_yf, 1.0)

                            Assign(output[y, x], output[y, x] + scale * (1-src_xf) * (1-src_yf) * input[src_yi,   src_xi])
                            Assign(output[y, x], output[y, x] + scale * (  src_xf) * (1-src_yf) * input[src_yi,   src_xi+1])
                            Assign(output[y, x], output[y, x] + scale * (1-src_xf) * (  src_yf) * input[src_yi+1, src_xi])
                            Assign(output[y, x], output[y, x] + scale * (  src_xf) * (  src_yf) * input[src_yi+1, src_xi+1])

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
