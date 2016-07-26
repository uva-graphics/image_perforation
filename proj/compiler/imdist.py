
import os
from PIL import Image
import sys
import numpy
import scipy.optimize
import time
import copy

R_COORD = 0
G_COORD = 1
B_COORD = 2 

X_COORD = 0
Y_COORD = 1
Z_COORD = 2 

L_COORD = 0
A_COORD = 1
B_COORD = 2 

REFERENCE_WHITE_X = 0.9642
REFERENCE_WHITE_Y = 1.0000
REFERENCE_WHITE_Z = 0.8249

CIE_EPSILON = 0.008856
CIE_KAPPA = 903.3

def im2uint8(I_):
    I = copy.deepcopy(I_)
    I.setflags(write=True)
    assert numpy.amin(I) >= 0.0, "Need elements to be doubles and scaled, i.e. in the range [0.0, 1.0]"
    assert numpy.amax(I) <= 1.0, "Need elements to be doubles and scaled, i.e. in the range [0.0, 1.0]"
    I = I*255
    return numpy.rint(I)

def im2double(I_):
    I = copy.deepcopy(I_)
    I.setflags(write=True)
    if (numpy.amin(I) >= 0.0 and numpy.amax(I) <= 1.0):
        return I
    I = I/255.0
    return I
    
def rgb2xyz(I_):
    assert numpy.amin(I_) >= 0.0, "Need elements to be scaled, i.e. in the range [0.0, 1.0]"
    assert numpy.amax(I_) <= 1.0, "Need elements to be scaled, i.e. in the range [0.0, 1.0]"
    assert len(I_.shape) == 3, "Need exactly 3 dims to convert from sRGB to XYZ"
    
    I = copy.deepcopy(I_)
    I.setflags(write=True)
    
    I = numpy.where(I <= 0.04045, I/12.92, ((I+0.055)/1.055)**2.4)
    
    I = numpy.concatenate( ( (I*[0.4360747, 0.3850649, 0.1430804]).sum(axis=2)[...,None], \
                             (I*[0.2225045, 0.7168786, 0.0606169]).sum(axis=2)[...,None], \
                             (I*[0.0139322, 0.0971045, 0.7141733]).sum(axis=2)[...,None]), axis=2)
    return I

def xyz2lab(I_):
    assert len(I_.shape) == 3, "Need exactly exactly 3 dims to convert from XYZ to L*a*b*"
    
    I = copy.deepcopy(I_)
    I.setflags(write=True)
    
    I = I / [REFERENCE_WHITE_X, REFERENCE_WHITE_Y, REFERENCE_WHITE_Z]
    
    I = numpy.where(I > CIE_EPSILON, I ** (1.0/3.0), (CIE_KAPPA*I+16.0)/116.0)
    
    I = numpy.concatenate( ( (116.0*I[:,:,Y_COORD]-16.0)[...,None], \
                             (500.0*(I[:,:,X_COORD]-I[:,:,Y_COORD]))[...,None], \
                             (200.0*(I[:,:,Y_COORD]-I[:,:,Z_COORD]))[...,None]), axis=2)
    
    return I

def rgb2lab(I_):
    I = copy.deepcopy(I_)
    I.setflags(write=True)
    return xyz2lab(rgb2xyz(I))

def lab2xyz(I_):
    assert len(I_.shape) == 3, "Need exactly 3 dims to convert from L*a*b* to XYZ"
    
    I = copy.deepcopy(I_)
    I.setflags(write=True)
    
    I_f = numpy.zeros(I.shape)
    
    I_f[:,:,Y_COORD] = (I[:,:,L_COORD]+16)/116
    I_f[:,:,X_COORD] = I[:,:,A_COORD]/500.0 + I_f[:,:,Y_COORD]
    I_f[:,:,Z_COORD] = I_f[:,:,Y_COORD] - I[:,:,B_COORD]/200.0
    
    I[:,:,Y_COORD] = numpy.where(I[:,:,L_COORD] > CIE_KAPPA*CIE_EPSILON, I_f[:,:,Y_COORD] **3, I[:,:,L_COORD] / CIE_KAPPA)
    I[:,:,X_COORD] = numpy.where(I_f[:,:,X_COORD] ** 3 > CIE_EPSILON, I_f[:,:,X_COORD] ** 3, (116*I_f[:,:,X_COORD]-16)/CIE_KAPPA)
    I[:,:,Z_COORD] = numpy.where(I_f[:,:,Z_COORD] ** 3 > CIE_EPSILON, I_f[:,:,Z_COORD] ** 3, (116*I_f[:,:,Z_COORD]-16)/CIE_KAPPA)
            
    I = I * [REFERENCE_WHITE_X, REFERENCE_WHITE_Y, REFERENCE_WHITE_Z]
    
    return I

def xyz2rgb(I_):
    assert len(I_.shape) == 3, "Need exactly 3 dims to convert from XYZ to sRGB"
    
    I = copy.deepcopy(I_)
    I.setflags(write=True)
    
    I = numpy.concatenate( ( (I*[ 3.1338561, -1.6168667, -0.4906146]).sum(axis=2)[...,None], \
                             (I*[-0.9787684,  1.9161415,  0.0334540]).sum(axis=2)[...,None], \
                             (I*[ 0.0719453, -0.2289914,  1.4052427]).sum(axis=2)[...,None]), axis=2)
    
    I = numpy.where(I <= 0.0031308, 12.92*I, 1.055*(I ** (1.0/2.4)) - 0.055)
    
    return I

def lab2rgb(I_):
    I = copy.deepcopy(I_)
    I.setflags(write=True)
    return xyz2rgb(lab2xyz(I))

def get_distance(distance_type, color_space, img1_name, img2_name):
    T0 = time.time()
    A = numpy.asarray(Image.open(img1_name))
    B = numpy.asarray(Image.open(img2_name))
    T1 = time.time()
    if color_space == 'lab':
        max_I = 128.0
        #tic = time.time()
        A = rgb2lab(im2double(A))
        B = rgb2lab(im2double(B))
        #toc = time.time()
        #print "rgb2lab time: "+str(toc-tic)
        #time.sleep(60)
        #tic = time.time()
        #A = skimage.color.rgb2lab(A)
        #B = skimage.color.rgb2lab(B)
        #toc = time.time()
        #print "skimage time: "+str(toc-tic)
    elif color_space == 'rgb':
        max_I = 255.0
        A = numpy.asarray(A, 'double')
        B = numpy.asarray(B, 'double')
    else:
        raise ValueError
    T2 = time.time()
    d = A - B
    d = numpy.sum(d**2, 2)
    T3 = time.time()
    if distance_type == 'mean':
        d = numpy.sqrt(d)
    d = numpy.mean(d.flatten())
    if distance_type == 'rms':
        d = numpy.sqrt(d)
    elif distance_type == 'psnr':
        min_d = 1.6384e-6
        d = 10 * numpy.log(max_I**2 / numpy.maximum(d, min_d)) / numpy.log(10.0)
    T4 = time.time()
#    print T1-T0, T2-T1, T3-T2, T4-T3
    return d
    
def main():
    args = sys.argv[1:]
    if len(args) < 4:
        print >> sys.stderr, 'imdist.py rms|mean|psnr rgb|lab img1 img2'
        sys.exit(1)
    
#    for channel in range(1,3):
#        print get_channel_max(channel, -1.0)
#        print get_channel_max(channel, 1.0)
    d = get_distance(args[0], args[1], os.path.abspath(args[2]), os.path.abspath(args[3]))
    print d
    
if __name__ == '__main__':
    #l = numpy.array([[[1,2,3],[3,4,5]],[[11,12,13],[14,15,16]]])
    #print l
    #print
    #print im2uint8(lab2rgb(rgb2lab(im2double(l))))
    #exit(0)
    main()

