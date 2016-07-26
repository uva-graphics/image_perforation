
import os, os.path
import sys
import glob
import numpy
import visualize_results

def usage():
    print 
    print "usage: python visualize_multi.py <approx_directory> <output_directory> <program_name> <image_dir>"
    print 
    print '  Same as visualize_results.py, but runs on every image in image_dir and outputs also aggregate statistics.'
    print
    sys.exit(1)

def main():
    args = sys.argv[1:]
    if len(args) < 4:
        usage()

    approx_directory = args[0]
    output_directory = args[1]
    program_name = args[2]
    image_dir = args[3]
    
    input_images = sorted([os.path.abspath(x) for x in glob.glob(os.path.join(image_dir, '*.png'))])
    
    if program_name in ['patchmatch', 'gpm']:
        a_images = sorted([os.path.abspath(x) for x in glob.glob(os.path.join(image_dir, 'a', '*.png'))])
        b_images = sorted([os.path.abspath(x) for x in glob.glob(os.path.join(image_dir, 'b', '*.png'))])
        assert len(a_images) == len(b_images)
        
        input_images = [(a_images[i], b_images[i]) for i in range(len(a_images))]

    approx_list = [os.path.abspath(filename) for filename in glob.glob(os.path.join(approx_directory, '*.approx'))]
    output_list = [os.path.join(output_directory, 'image%03d' % i) for i in range(len(input_images))]
    
    for (i, img) in enumerate(input_images):
        print '='*80
        print 'Visualizing image %d/%d (%s)' % (i, len(input_images), img)
        print '='*80
        print
        visualize_results.visualize_results(approx_list, output_list[i], program_name, run_args={'input_file_locations': img}, open_html=False)
    
    out_csv = os.path.join(output_directory, 'aggregate.csv')
    
    print 'Aggregating results into %s' % out_csv
    
    L = [numpy.recfromcsv(os.path.join(output_list[i], 'visualization_data.csv')) for i in range(len(output_list))]
    
    time     = numpy.mean([L[i].time     for i in range(len(L))], 0)
    mean_lab = numpy.mean([L[i].mean_lab for i in range(len(L))], 0)
    psnr_lab = numpy.mean([L[i].psnr_lab for i in range(len(L))], 0)
    try:
        error    = numpy.mean([L[i].error    for i in range(len(L))], 0)
        has_error = True
    except AttributeError:
        has_error = False
    
    with open(out_csv, 'wt') as f:
        f.write('Approx File, Time, Mean Lab, PSNR Lab' + (', Error' if has_error else '') + '\n')
        for i in range(len(time)):
            f.write('%s, %f, %f, %f' % (L[0].approx_file[i], time[i], mean_lab[i], psnr_lab[i]))
            if has_error:
                f.write(', %f' % error[i])
            f.write('\n')

if __name__ == '__main__':
    main()
    
