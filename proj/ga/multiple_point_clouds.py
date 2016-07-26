#!/usr/bin/python

import os
import sys
import numpy
import Image
import pdb
import ntpath
import matplotlib.pyplot
import matplotlib.lines

def list_dir_abs(basepath):
    return map(lambda x: os.path.join(basepath, x), os.listdir(basepath))

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

def makedirs(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)

TITLE_FONT_SIZE=35
AXIS_FONT_SIZE=25
TICK_LABEL_FONT_SIZE=20

def usage():
    print >> sys.stderr, 'python '+__file__+' output_directory csv_1 csv_2 ...'
    sys.exit(1)

def point_cloud(csv_locations_list, output_directory):
    
    alpha_for_non_mean_points = 0.05
    
    makedirs(output_directory)
    
    mean_points_dict = dict()
    non_mean_points_dict = dict()
    color_dict = dict()
    for csv_location in csv_locations_list:
        color = numpy.random.rand(3,1)
        color_dict[csv_location] = color
    
    fig_mean, subplot_mean = matplotlib.pyplot.subplots()
    
    legend_handles = []
    
    for csv_file in csv_locations_list:
        
        point_color = color_dict[csv_file]
        legend_handles.append( matplotlib.lines.Line2D([], [], color=point_color, marker='.', markersize=10, label=path_leaf(csv_file) ) )
        
        text_lines = open(csv_file, 'rt').readlines()
        non_mean_points = []
        mean_points = []
        for ppp,line in enumerate(text_lines[1:]):
            approx_name = line.split(',')[0].strip()
            data_list = map(lambda x: float(x.strip()),line.split(',')[1:])
            points_from_line = [ (data_list[2*i],data_list[2*i+1]) for i in xrange(len(data_list)/2) ]
            points_from_line = sorted(points_from_line, key=lambda x:x[1]) # sorted by error
            if points_from_line == []:
                continue
            non_mean_points += points_from_line
            mean_point = ( sum(map(lambda x:x[0], points_from_line))/float(len(points_from_line)),sum(map(lambda x:x[1], points_from_line))/float(len(points_from_line)) )
            mean_points.append(mean_point)
        x = map(lambda x: x[1], non_mean_points) # error on x
        y = map(lambda x: x[0], non_mean_points) # time on y
        subplot_mean.scatter(x, y,zorder=10, color=point_color, alpha = alpha_for_non_mean_points)
        x = map(lambda x: x[1], mean_points) # error on x
        y = map(lambda x: x[0], mean_points) # time on y
        subplot_mean.scatter(x, y,zorder=10, color=point_color, alpha = 1.0)
        mean_points = sorted(mean_points, key=lambda x:x[1])
        for i in xrange(len(mean_points)):
            if i == len(mean_points)-1:
                break
            subplot_mean.plot( [mean_points[i][1], mean_points[i+1][1]], [mean_points[i][0], mean_points[i+1][0]], color=point_color )
        mean_points_dict[csv_file] = mean_points
        non_mean_points_dict[csv_file] = non_mean_points
    
    subplot_mean.set_title('Performance vs Accuracy', fontsize=TITLE_FONT_SIZE, y=1.04)
    subplot_mean.set_xlabel('$L^2$ Error',fontsize=AXIS_FONT_SIZE)
    subplot_mean.set_ylabel('Absolute Time',fontsize=AXIS_FONT_SIZE)
    subplot_mean.set_xlim(left=0)
    subplot_mean.set_xlim(right=10)
    subplot_mean.set_ylim(bottom=0)
    subplot_mean.set_ylim(top=0.05)
    subplot_mean.legend(handles=legend_handles)
    fig_mean.savefig(os.path.abspath(os.path.join(output_directory,'point_cloud.png')), bbox_inches='tight')

def main():
    if len(sys.argv) < 3:
        usage()
    
    output_dir = os.path.abspath(sys.argv[1])
    makedirs(output_dir)
    
    csv_names = map(os.path.abspath,sys.argv[2:])
    
    point_cloud(csv_names, output_dir)
    

if __name__ == '__main__':
    main()

