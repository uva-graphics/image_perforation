
import os
import sys
import numpy
import matplotlib
import matplotlib.pyplot

TIME_INDEX=0
ERROR_INDEX=1

TITLE_FONT_SIZE=35
AXIS_FONT_SIZE=20

def clear():
    os.system('clear')

def makedirs(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)

def median(l):
    length = len(l)
    return sorted(l)[length/2]

def median_of_points_by_error(l):
    length = len(l)
    return sorted(l,key=lambda x:x[ERROR_INDEX])[length/2]

def median_of_points_by_time(l):
    length = len(l)
    return sorted(l,key=lambda x:x[TIME_INDEX])[length/2]

def usage(): 
    print >> sys.stderr, 'python '+__file__+' csv_file_a csv_file_b output_dir'
    sys.exit(1)


def main():
    args = sys.argv
    if len(args) < 4:
        usage()
    clear()
    
    csv_file_a = os.path.abspath(args[1])
    csv_file_b = os.path.abspath(args[2])
    output_directory = os.path.abspath(args[3])
    makedirs(output_directory)
    
    csv_file_a_mean_points = []
    csv_file_b_mean_points = []
    csv_file_a_median_points = []
    csv_file_b_median_points = []
    csv_file_a_non_mean_points = []
    csv_file_b_non_mean_points = []
    
    fig_mean, subplot_mean = matplotlib.pyplot.subplots()
    fig_median, subplot_median = matplotlib.pyplot.subplots()
    for csv_file in [csv_file_a,csv_file_b]:
        
        if csv_file == csv_file_a:
            point_color = 'r'
        elif csv_file == csv_file_b:
            point_color = 'b'
        
        text_lines = open(csv_file, 'rt').readlines()
        non_mean_points = []
        median_points = []
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
            median_point = median_of_points_by_error(points_from_line) # because error has more variance
            median_points.append(median_point)
        
        background_alpha=0.05 #0.05
            
        x = map(lambda x: x[1], non_mean_points) # error on x
        y = map(lambda x: x[0], non_mean_points) # time on y
        subplot_mean.scatter(x, y,zorder=10, color=point_color, alpha = background_alpha)
        subplot_median.scatter(x, y,zorder=10, color=point_color, alpha = background_alpha)
        x = map(lambda x: x[1], mean_points) # error on x
        y = map(lambda x: x[0], mean_points) # time on y
        subplot_mean.scatter(x, y,zorder=10, color=point_color, alpha = 1.0)
        x = map(lambda x: x[1], median_points) # error on x
        y = map(lambda x: x[0], median_points) # time on y
        subplot_median.scatter(x, y,zorder=10, color=point_color, alpha = 1.0)
        mean_points = sorted(mean_points, key=lambda x:x[1])
        median_points = sorted(median_points, key=lambda x:x[1])
        for i in xrange(len(mean_points)):
            if i == len(mean_points)-1:
                break
            subplot_mean.plot( [mean_points[i][1], mean_points[i+1][1]], [mean_points[i][0], mean_points[i+1][0]], color=point_color )
            subplot_median.plot( [median_points[i][1], median_points[i+1][1]], [median_points[i][0], median_points[i+1][0]], color=point_color )
        if csv_file == csv_file_a:
            csv_file_a_mean_points = list(mean_points)
            csv_file_a_non_mean_points = list(non_mean_points)
            csv_file_a_median_points = list(median_points)
        elif csv_file == csv_file_b:
            csv_file_b_mean_points = list(mean_points)
            csv_file_b_non_mean_points = list(non_mean_points)
            csv_file_b_median_points = list(median_points)
    for subplot in [subplot_mean,subplot_median]:
        subplot.set_title('Performance vs Accuracy', fontsize=TITLE_FONT_SIZE, y=1.04)
        subplot.set_xlabel('Mean LAB Error',fontsize=AXIS_FONT_SIZE)
        subplot.set_ylabel('Relative Time',fontsize=AXIS_FONT_SIZE)
        subplot.set_xlim(left=0)
        subplot.set_xlim(right=50)
        subplot.set_ylim(bottom=0)
        subplot.set_ylim(top=1.2)
        subplot.set_aspect(42)
    fig_mean.savefig(os.path.abspath(os.path.join(output_directory,'point_cloud.png')), bbox_inches='tight')
    fig_median.savefig(os.path.abspath(os.path.join(output_directory,'point_cloud_median.png')), bbox_inches='tight')
    with open(os.path.abspath(os.path.join(output_directory,'mean_points.csv')),'wt') as f:
        f.write('Image Perforation Time, Image Perforation Error, Loop Perforation Time, Loop Perforation Error \n')
        for i in xrange(max(len(csv_file_a_mean_points),len(csv_file_b_mean_points))):
            a,b,c,d='','','',''
            if i < len(csv_file_a_mean_points):
                a = csv_file_a_mean_points[i][0]
                b = csv_file_a_mean_points[i][1]
            if i < len(csv_file_b_mean_points):
                c = csv_file_b_mean_points[i][0]
                d = csv_file_b_mean_points[i][1]
            f.write(str(a)+','+str(b)+','+str(c)+','+str(d)+'\n')
    with open(os.path.abspath(os.path.join(output_directory,'non_mean_points.csv')),'wt') as f:
        f.write('Image Perforation Time, Image Perforation Error, Loop Perforation Time, Loop Perforation Error \n')
        for i in xrange(max(len(csv_file_a_non_mean_points),len(csv_file_b_non_mean_points))):
            a,b,c,d='','','',''
            if i < len(csv_file_a_non_mean_points):
                a = csv_file_a_non_mean_points[i][0]
                b = csv_file_a_non_mean_points[i][1]
            if i < len(csv_file_b_non_mean_points):
                c = csv_file_b_non_mean_points[i][0]
                d = csv_file_b_non_mean_points[i][1]
            f.write(str(a)+','+str(b)+','+str(c)+','+str(d)+'\n')
    print "Done!"

if __name__ == '__main__':
    main()

