cpp_compiler = 'g++-4.8'                                                 # A g++ 4.7+ compiler
linker_options = '-L /opt/X11/lib -lpthread -lpng -ldl -fno-tree-pre'    # Linker options
compiler_options = '-O3 -fopenmp -funroll-loops -fmax-errors=3 -std=c++0x -fabi-version=6 -DBUILD_DEBUG=0 -I /opt/X11/include'
