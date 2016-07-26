filter-approx
=============

Filter Approximation project, ongoing research.

Install:

 - GCC/G++ 4.7+. For Ubuntu you can use an unofficial package (repeat the lines containing gcc with g++ also):
   http://askubuntu.com/questions/271388/how-to-install-gcc-4-8-in-ubuntu-12-04-from-the-terminal
 
   Verify that 'g++ --version' reports version 4.7+

 - Z3 Python module.
   Install from: http://z3.codeplex.com/ . Download the source package and follow the
   directions for step (2) Python install.

 - X11, Boost, libpng, ImageMagick, unbuffer, png++ (sudo apt-get install libx11-dev libboost-all-dev libpng12-dev imagemagick expect-dev, png++)

 - Python libraries needed: numpy, matplotlib (sudo pip install numpy, sudo pip install matplotlib or sudo apt-get install python-numpy python-matplotlib).

Test:

% cd proj/compiler
% python approx.py
   -- Should automatically generate out.cpp, then run g++ on it to create out, then run out.

% cd proj/img_abstraction
% python img_abstraction.py

