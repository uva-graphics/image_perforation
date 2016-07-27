
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

% cd proj/blur
% python blur.py

This runs the original program and obtains the reference output. By default the training images in images/train are used for inputs and the outputs are written into the directory 'output'.



