
## Image Perforation code

This is code from the paper "Image Perforation: Automatically Accelerating Image Pipelines by Intelligently Skipping Samples," by Liming Lou, Paul Nguyen, Jason Lawrence, Connelly Barnes, ACM Transactions on Graphics 2016 (ACM SIGGRAPH 2016).

Project website: http://www.cs.virginia.edu/~connelly/project_pages/image_perforation/

## Platforms

Linux and Mac are currently supported.

## Install

Install the requirements:

 - GCC/G++ 4.7+. For Ubuntu you can use an unofficial package (repeat the lines containing gcc with g++ also):
   http://askubuntu.com/questions/271388/how-to-install-gcc-4-8-in-ubuntu-12-04-from-the-terminal
 
 - Z3 Python module.
   Install from: http://z3.codeplex.com/ . Download the source package and follow the
   directions for step (2) Python install.

 - X11, Boost, libpng, ImageMagick, unbuffer, png++ (sudo apt-get install libx11-dev libboost-all-dev libpng12-dev imagemagick expect-dev, png++)

 - Python libraries needed: numpy, matplotlib (sudo pip install numpy, sudo pip install matplotlib or sudo apt-get install python-numpy python-matplotlib).

 - Edit proj/compiler/compiler_config.py to point it to your g++ binary, and modify
   the compiler and linker options as needed for your platform.

## Run (Reference Output)

To run one of the applications explored in the paper (artistic_blur, bilateral_filter, bilateral_grid, blur, demosaic, median, unsharp_mask), change to its directory and run the associated program with Python 2.7:

    $ cd proj/blur
    $ python blur.py

This runs the original program and obtains the reference output. By default the training images in images/train are used for inputs and the outputs are written into the directory 'output'.

## Run (Our System)

To run our full system on an image pipeline, first place your image pipline app in proj/appname/appname.py. You can mimick the syntax used in the other example apps checked in. Verify that the apps works when run standalone, and that it is reasonably quick to run (e.g. a second).

Next, retrieve the test set images:

    $ cd proj/images
    $ wget http://www.cs.virginia.edu/~connelly/share/image_perforation_test.zip
    $ unzip image_perforation_test.zip

Finally, run the genetic algorithm autotuner (the "cross validation directory" is equivalent to the test set directory). For this test we will assume you are using the built-in median filter application (proj/median/median.py):

    $ cd ../ga
    $ python ga.py median result_median -population_size 100 -generations 200 -run_final_generation 1 -cross_validation_directory ../images/test

This writes to the output directory 'result_median'. Wait some time (hours to a day) until the genetic algorithm is finished. The special generation 100,000 in the output directory contains the final tuned program variants reported in the paper (including plots similar to Figures 5 and 6 in the paper in the file gen100000/visualize/mean_lab_relative.png).

Suppose you want to use one of the approximated program variants. Let us assume the main method of your app is configured similarly to that of the exemplars such as median.py, which accepts one of the .approx files output by the tuner as its first argument. Then you can just run your app on one of the final generation's approx files, e.g. for median:

    $ cd ../proj/median
    $ python median.py ../ga/result_median/gen100000/indiv000.approx

The above command outputs the approximated C++ program source code and runs it to obtain time used for each input image.
