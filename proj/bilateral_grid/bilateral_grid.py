#!/usr/bin/python

#./bilateral_grid.py ../visualize_results/approximations/bilateral_grid/populate-downsample.approx 

import sys; sys.path += ['../compiler']
from approx import *
import os

R_COORD = 0
G_COORD = 1
B_COORD = 2
WEIGHT_COORD = 3

DEFAULT_SIGMA_RANGE   = 0.14/1.4

use_yuv = True                  # Process in YUV color space (allows for luminance only approximations)

approx_loops = {'populate_b_grid_loop':  'foreach', 
                'blur_y_loop':           'foreach',
                'blur_x_loop':           'foreach',
                'blur_z_loop':           'foreach',
                'trilerp_loop':          'foreach'}

@makenames
def create_program(is_vectorize=True, approximation_file_name=""):
    if is_vectorize:
        kw = dict(sizes=(None, None, 4), vectorize=2)
    else:
        kw = dict(sizes=(None, None, 3))
    
    Real = Float(32)
    Image = Array(Real, 3, sizes=(None, None, 3))
    Image_grayscale = Array(Real, 2, sizes=(None, None))
    
    with Program() as program:
        
        with Function(Real) as G:
            g_x = Argument(Real)
            g_sigma = Argument(Real)
            Return(exp(-(g_x*g_x)/(2*g_sigma*g_sigma))/(g_sigma*sqrt(2*math.pi)))
        
        with Function(Real) as lerp:
            a = Argument(Real)
            b = Argument(Real)
            x = Argument(Real)
            Return(a*(1.0-x)+b*x)
            
        with Function(Real) as trilerp:
            # c_yxz
            c_000 = Argument(Real)
            c_001 = Argument(Real)
            c_010 = Argument(Real)
            c_011 = Argument(Real)
            c_100 = Argument(Real)
            c_101 = Argument(Real)
            c_110 = Argument(Real)
            c_111 = Argument(Real)
            yf = Argument(Real)
            xf = Argument(Real)
            zf = Argument(Real)
            Return(lerp(lerp(lerp(c_000, c_010, xf), lerp(c_100, c_110, xf), yf), lerp(lerp(c_001, c_011, xf), lerp(c_101, c_111, xf), yf), zf))
            
        with Function() as main_func:
            input_image  = Argument(Image)
            output_image = Argument(Image)
            output_image.resize(input_image.sizes())
            
            T_start_total = Var(wall_time())
            
            # Get grayscale/luminance image
            input_image_grayscale  = Var(Image_grayscale)
            input_image_grayscale.resize( [ input_image.height(), input_image.width() ] )
            y = Var(Int())
            x = Var(Int())
            T_start_luminance = Var(wall_time())
            with ForEach((y, x), input_image_grayscale):
                input_image_grayscale[y,x] = input_image[y,x,R_COORD] * 0.299 + \
                                             input_image[y,x,G_COORD] * 0.587 + \
                                             input_image[y,x,B_COORD] * 0.114 
            T_end_luminance = Var(wall_time())
            if use_yuv:
                input_image.rgb2yuv()
            
            # Params
            sampling_sigma_spatial = Var(Real, Select(input_image.height() > input_image.width(), input_image.height(), input_image.width())/64) 
            sampling_sigma_range = Var(Real, DEFAULT_SIGMA_RANGE)
            
            # b_grid dimensions
            b_grid_height = Var(Int(), ceil(input_image.height() / sampling_sigma_spatial) + 1)
            b_grid_width = Var(Int(), ceil(input_image.width() / sampling_sigma_spatial) + 1)
            b_grid_num_ranges = Var(Int(), ceil(1.0/sampling_sigma_range) + 1)
            b_grid_num_channels = 4 # for r, g, b, weight
            
            # Form b_grid
            b_grid = Var(Array(Real, 4, sizes=(None, None, None, None)))
            b_grid.resize( [b_grid_height, b_grid_width, b_grid_num_ranges, b_grid_num_channels] )
            b_grid.clear() # we want everything to start at zero
            
            # Populate b_grid
            b_grid_y = Var(Int())
            b_grid_x = Var(Int())
            b_grid_which_range = Var(Int())
            T_start_populate_b_grid = Var(wall_time())
            with ForEach((y, x), input_image, input_image, do_reconstruct=False, parallel=False) as populate_b_grid_loop:
                Assign(b_grid_y, round(y/sampling_sigma_spatial))
                Assign(b_grid_x, round(x/sampling_sigma_spatial))
                Assign(b_grid_which_range, round(input_image_grayscale[y,x]/sampling_sigma_range))
                b_grid[b_grid_y,b_grid_x,b_grid_which_range,R_COORD] = \
                    b_grid[b_grid_y,b_grid_x,b_grid_which_range,R_COORD] + input_image[y,x,R_COORD]
                b_grid[b_grid_y,b_grid_x,b_grid_which_range,G_COORD] = \
                    b_grid[b_grid_y,b_grid_x,b_grid_which_range,G_COORD] + input_image[y,x,G_COORD]
                b_grid[b_grid_y,b_grid_x,b_grid_which_range,B_COORD] = \
                    b_grid[b_grid_y,b_grid_x,b_grid_which_range,B_COORD] + input_image[y,x,B_COORD]
                b_grid[b_grid_y,b_grid_x,b_grid_which_range,WEIGHT_COORD] = \
                    b_grid[b_grid_y,b_grid_x,b_grid_which_range,WEIGHT_COORD] + 1
            T_end_populate_b_grid = Var(wall_time())
            
            # Form b_grid_blurred_y, b_grid_blurred_x, b_grid_blurred_z
            b_grid_blurred_y = Var(Array(Real, 4, sizes=(None, None, None, None)))
            b_grid_blurred_y.resize( [b_grid_height, b_grid_width, b_grid_num_ranges, b_grid_num_channels] )
            b_grid_blurred_x = Var(Array(Real, 4, sizes=(None, None, None, None)))
            b_grid_blurred_x.resize( [b_grid_height, b_grid_width, b_grid_num_ranges, b_grid_num_channels] )
            b_grid_blurred_z = Var(Array(Real, 4, sizes=(None, None, None, None)))
            b_grid_blurred_z.resize( [b_grid_height, b_grid_width, b_grid_num_ranges, b_grid_num_channels] )
            b_grid_blurred_y.clear() # we want everything to start at zero
            b_grid_blurred_x.clear()
            b_grid_blurred_z.clear()
            
            # Blur b_grid
            i = Var(Int())
            z = Var(Int())
            
            # Figure out kernel coefficients
            DEFAULT_GAUSSIAN_BLUR_SIGMA_SPATIAL = 1.5
            DEFAULT_GAUSSIAN_BLUR_SIGMA_RANGE = 1.5
            gaussian_blur_sigma_spatial = Var(Real, DEFAULT_GAUSSIAN_BLUR_SIGMA_SPATIAL)
            gaussian_blur_sigma_range = Var(Real, DEFAULT_GAUSSIAN_BLUR_SIGMA_RANGE)
            gaussian_blur_sigma_spatial_int = Var(Int(), round(gaussian_blur_sigma_spatial)) # cast to int
            gaussian_blur_sigma_range_int = Var(Int(), round(gaussian_blur_sigma_range)) # cast to int
            kernel_index = Var(Int())
            # These are only half kernels, i.e. [6,4,1] instead of [1,4,6,4,1]
            kernel_spatial = Var(Array(Real, 1, sizes=(None))) 
            kernel_spatial.resize([gaussian_blur_sigma_spatial_int+1])
            kernel_range = Var(Array(Real, 1, sizes=(None)))
            kernel_range.resize([gaussian_blur_sigma_range_int+1])
            with For(kernel_index,0, kernel_spatial.height(), 1):
                kernel_spatial[kernel_index] = G(kernel_index, gaussian_blur_sigma_spatial)
            with For(kernel_index,0, kernel_range.height(), 1):
                kernel_range[kernel_index] = G(kernel_index, gaussian_blur_sigma_range)
            
            T_start_blur_b_grid = Var(wall_time())
            
            T_start_blur_b_grid_y = Var(wall_time())
            # Blur b_grid in y
            with ForEach((y,x,z,i), b_grid_blurred_y, b_grid) as blur_y_loop:
                with For(kernel_index,0, kernel_spatial.height(), 1):
                    with If(y-kernel_index >= 0):
                        b_grid_blurred_y[y,x,z,i] = b_grid_blurred_y[y,x,z,i] + b_grid[y-kernel_index,x,z,i] * kernel_spatial[kernel_index]
                    with If( And( y+kernel_index < b_grid_blurred_y.height() , kernel_index!=0 ) ):
                        b_grid_blurred_y[y,x,z,i] = b_grid_blurred_y[y,x,z,i] + b_grid[y+kernel_index,x,z,i] * kernel_spatial[kernel_index]
                '''
                with If(y-2 >= 0):
                    b_grid_blurred_y[y,x,z,i] = b_grid_blurred_y[y,x,z,i] + b_grid[y-2,x,z,i]
                with If(y-1 >= 0):
                    b_grid_blurred_y[y,x,z,i] = b_grid_blurred_y[y,x,z,i] + b_grid[y-1,x,z,i] * 4
                b_grid_blurred_y[y,x,z,i] = b_grid_blurred_y[y,x,z,i] + b_grid[y  ,x,z,i] * 6 
                with If(y+1 < b_grid_blurred_y.height()):
                    b_grid_blurred_y[y,x,z,i] = b_grid_blurred_y[y,x,z,i] + b_grid[y+1,x,z,i] * 4 
                with If(y+2 < b_grid_blurred_y.height()):
                    b_grid_blurred_y[y,x,z,i] = b_grid_blurred_y[y,x,z,i] + b_grid[y+2,x,z,i]
                '''
            T_end_blur_b_grid_y = Var(wall_time())
                
            T_start_blur_b_grid_x = Var(wall_time())
            # Blur b_grid in x
            with ForEach((y,x,z,i), b_grid_blurred_x, b_grid_blurred_y) as blur_x_loop:
                with For(kernel_index,0, kernel_spatial.height(), 1):
                    with If(x-kernel_index >= 0):
                        b_grid_blurred_x[y,x,z,i] = b_grid_blurred_x[y,x,z,i] + b_grid_blurred_y[y,x-kernel_index,z,i] * kernel_spatial[kernel_index]
                    with If( And( x+kernel_index < b_grid_blurred_x.width() , kernel_index!=0 ) ):
                        b_grid_blurred_x[y,x,z,i] = b_grid_blurred_x[y,x,z,i] + b_grid_blurred_y[y,x+kernel_index,z,i] * kernel_spatial[kernel_index]
                '''
                with If(x-2 >= 0):
                    b_grid_blurred_x[y,x,z,i] = b_grid_blurred_x[y,x,z,i] + b_grid_blurred_y[y,x-2,z,i]
                with If(x-1 >= 0):
                    b_grid_blurred_x[y,x,z,i] = b_grid_blurred_x[y,x,z,i] + b_grid_blurred_y[y,x-1,z,i] * 4
                b_grid_blurred_x[y,x,z,i] = b_grid_blurred_x[y,x,z,i] + b_grid_blurred_y[y,x,z,i] * 6
                with If(x+1 < b_grid_blurred_x.width()):
                    b_grid_blurred_x[y,x,z,i] = b_grid_blurred_x[y,x,z,i] + b_grid_blurred_y[y,x+1,z,i] * 4
                with If(x+2 < b_grid_blurred_x.width()):
                    b_grid_blurred_x[y,x,z,i] = b_grid_blurred_x[y,x,z,i] + b_grid_blurred_y[y,x+2,z,i]
                '''
            T_end_blur_b_grid_x = Var(wall_time())
                
            T_start_blur_b_grid_z = Var(wall_time())
            # Blur b_grid in z
            with ForEach((y,x,z,i), b_grid_blurred_z, b_grid_blurred_x) as blur_z_loop:
                with For(kernel_index,0, kernel_range.height(), 1):
                    with If(z-kernel_index >= 0):
                        b_grid_blurred_z[y,x,z,i] = b_grid_blurred_z[y,x,z,i] + b_grid_blurred_x[y,x,z-kernel_index,i] * kernel_range[kernel_index]
                    with If( And( z+kernel_index < b_grid_blurred_z.channels() , kernel_index!=0 ) ):
                        b_grid_blurred_z[y,x,z,i] = b_grid_blurred_z[y,x,z,i] + b_grid_blurred_x[y,x,z+kernel_index,i] * kernel_range[kernel_index]
                '''
                with If(z-2 >= 0):
                    b_grid_blurred_z[y,x,z,i] = b_grid_blurred_z[y,x,z,i] + b_grid_blurred_x[y,x,z-2,i]
                with If(z-1 >= 0):
                    b_grid_blurred_z[y,x,z,i] = b_grid_blurred_z[y,x,z,i] + b_grid_blurred_x[y,x,z-1,i] * 4
                b_grid_blurred_z[y,x,z,i] = b_grid_blurred_z[y,x,z,i] + b_grid_blurred_x[y,x,z,i] * 6
                with If(z+1 < b_grid_blurred_z.channels()):
                    b_grid_blurred_z[y,x,z,i] = b_grid_blurred_z[y,x,z,i] + b_grid_blurred_x[y,x,z+1,i] * 4
                with If(z+2 < b_grid_blurred_z.channels()):
                    b_grid_blurred_z[y,x,z,i] = b_grid_blurred_z[y,x,z,i] + b_grid_blurred_x[y,x,z+2,i]
                '''
            T_end_blur_b_grid_z = Var(wall_time())
            
            T_end_blur_b_grid = Var(wall_time())
            
            # Get values for final output image
            color = Var(Int())
            T_start_trilinear_interpolate = Var(wall_time())
            with ForEach((y,x,color), output_image, input_image) as trilerp_loop:
                # Figure out the coordinates we need in the b_grid
                val = Var(Real, input_image_grayscale[y,x])
                zi = Var(Int(), (val/sampling_sigma_range) ) 
                zf = Var(Real, (val/sampling_sigma_range) - zi)
                xi = Var(Int(), (x/sampling_sigma_spatial))
                xf = Var(Real, (x/sampling_sigma_spatial) - xi )
                yi = Var(Int(), (y/sampling_sigma_spatial) )
                yf = Var(Real, (y/sampling_sigma_spatial) - yi )
                
                # Trilinearly interpolate the intensity value
                intensity = Var(Real, trilerp(b_grid_blurred_z[yi  , xi  , zi  , color], \
                                              b_grid_blurred_z[yi  , xi  , zi+1, color], \
                                              b_grid_blurred_z[yi  , xi+1, zi  , color], \
                                              b_grid_blurred_z[yi  , xi+1, zi+1, color], \
                                              b_grid_blurred_z[yi+1, xi  , zi  , color], \
                                              b_grid_blurred_z[yi+1, xi  , zi+1, color], \
                                              b_grid_blurred_z[yi+1, xi+1, zi  , color], \
                                              b_grid_blurred_z[yi+1, xi+1, zi+1, color], \
                                              yf, xf, zf ) )
                # Trilinearly interpolate the weight value
                weight    = Var(Real, trilerp(b_grid_blurred_z[yi  , xi  , zi  , WEIGHT_COORD], \
                                              b_grid_blurred_z[yi  , xi  , zi+1, WEIGHT_COORD], \
                                              b_grid_blurred_z[yi  , xi+1, zi  , WEIGHT_COORD], \
                                              b_grid_blurred_z[yi  , xi+1, zi+1, WEIGHT_COORD], \
                                              b_grid_blurred_z[yi+1, xi  , zi  , WEIGHT_COORD], \
                                              b_grid_blurred_z[yi+1, xi  , zi+1, WEIGHT_COORD], \
                                              b_grid_blurred_z[yi+1, xi+1, zi  , WEIGHT_COORD], \
                                              b_grid_blurred_z[yi+1, xi+1, zi+1, WEIGHT_COORD], \
                                              yf, xf, zf ) )
                
                output_image[y,x,color] = intensity / weight
            if use_yuv:
                output_image.yuv2rgb()
            T_end_trilinear_interpolate = Var(wall_time())
            
            
            # Do loop approximations from file
            apply_approximations_from_file(globals(), locals(), approximation_file_name)
            
            T_end_total = Var(wall_time())
            
            #"""
            printf('\n')
            printf('Get Luminance/Grayscale Image:   %f\n', T_end_luminance-T_start_luminance)
            printf('Populate Bilateral Grid:         %f\n', T_end_populate_b_grid-T_start_populate_b_grid)
            printf('Blur Entire Bilateral Grid:      %f\n', T_end_blur_b_grid-T_start_blur_b_grid)
            printf('Blur Bilateral Grid in y:        %f\n', T_end_blur_b_grid_y-T_start_blur_b_grid_y)
            printf('Blur Bilateral Grid in x:        %f\n', T_end_blur_b_grid_x-T_start_blur_b_grid_x)
            printf('Blur Bilateral Grid in z:        %f\n', T_end_blur_b_grid_z-T_start_blur_b_grid_z)
            printf('Trilinear Interpolation:         %f\n', T_end_trilinear_interpolate-T_start_trilinear_interpolate)
            printf('Total:                           %f\n', T_end_total-T_start_total)
            #"""
    
    return (program, locals())

def main(approx_file="", output_directory=os.path.abspath('./output/'), input_directory=os.path.abspath('./input/'), kw0={}):
    
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    kw = dict(parallel=False, is_vectorize=False, debug=False, **kw0)
    (program, locals_d) = create_program(is_vectorize=kw['is_vectorize'], approximation_file_name=approx_file)
    
    return compile_and_run_on_several_images(approx_file=approx_file, input_directory=input_directory, output_directory=output_directory, kw0=kw, program=program)

if __name__ == '__main__':
    main(**parse_app_commandline(sys.argv))


