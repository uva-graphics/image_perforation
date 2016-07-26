
"""
Rescale algorithms -- naive (Newton) vs histogram
"""

# How maximum error varies with histogram buckets (for 1000 test iterations):

# Histogram buckets (m)      err_max
# 100                        0.043051
# 256                        0.017270
# 1000                       0.004479
# 4000                       0.001123
# 10000                      0.000450
#
# err_max = b0 / m
# log(err_max) = log(b0) - log(m)
# Mean estimator for log(b0) gives b0 = 4.4 (4.43884).
# Predicted err_max from this model agrees quite well with actual err_max (within 3% tolerance).

import numpy
import random
import time

verbose = False

def check(h, x, f, n):
    m = len(x)
    for k in range(1, m):
        full = (f*n - sum([h[i] for i in range(k+1, m)])) / sum([h[i]*x[i] for i in range(k)]) * x[k]
        assert full <= 1, (full, h, x, f, n, k)

def test_check():
    iters = 100
    for m in range(1, 10):
        for j in range(iters):
            print 'm=%d, j=%d'%(m, j)
            x = numpy.array([1.0/3.0, 2.0/3.0]) #(numpy.arange(float(m))+(0.5))
            h = numpy.ones(m)
            #for i in range(n):
            #    h[random.randrange(m)] += 1
            f = 0.5 #random.uniform(0, 1)
            n = numpy.sum(h)
            check(h, x, f, n)

def solve_newton(v, f):
    if verbose:
        print 'Newton solver:'
    n = len(v)
    def g_gprime(s):
        return (numpy.sum(numpy.minimum(s*v, 1.0)) - n*f, numpy.sum((s*v<1.0)*v))

    s = 0.0
    for i in range(100):
        (g, gp) = g_gprime(s)
        if gp == 0.0:
            return s
        if verbose:
            print s, g
        s -= g/gp
    
    if verbose:
        print
        
    return s

def solve_histogram(v, f, m=1000):
    if verbose:
        print 'Histogram solver:'
    eps = 1e-8
    
    n = len(v)
    (h, right) = numpy.histogram(v, m)
    assert len(right) == m+1
    assert abs(numpy.sum(h) - n) < 1e-8
    x = numpy.array([(right[i]+right[i+1])/2.0 for i in range(m)])
    
    #T0 = time.time()
    
    h_partial = numpy.cumsum(h)      # h_partial[k] is sum(h[i]*(1-x[i]), 0 <= i <= k)
    hx_partial = numpy.cumsum(h*x)   # h_partial[k] is sum(h[i]*(1-x[i]), 0 <= i <= k)
        
    for k in range(m-1,-1,-1): #range(m-1,-1,-1):
        
        s = (h_partial[k] - n*(1-f)) / hx_partial[k] if hx_partial[k] else 0.0
        s_max = 1.0/x[k]
        s_min = 1.0/x[k+1] if k+1 < len(x) else 0.0
        
        if verbose:
            err = s*hx_partial[k] - h_partial[k] - n*(f-1)
            err_brute = numpy.sum(h * numpy.minimum(s*x, 1.0)) - f*n
        
            #term1_brute = numpy.sum(h*(s*x<1.0)*(s*x))
        
            #term1 = s*hx_partial[k]
            #term2 = -h_partial[k]
            #term3 = -n*(f-1)

            if k < m:
                print 'k=%r, h=%r, x=%.4f, s_min=%.4f, s_max=%.4f, s=%.4f, err=%.4f, err_brute=%.4f' % (k, h[k], x[k], s_min, s_max, s, err, err_brute)

        if s <= s_max*(1+eps) and s >= s_min/(1+eps):
            #print k, time.time()-T0
            return s

    return 1e100
    
def main():
#    numpy.random.seed(0)
#    random.seed(0)
    err_max = 0.0
    
    for i in range(1000):
        random.seed(i)
        numpy.random.seed(i)
        
        f = random.uniform(0.05, 0.95)
        tol = 0.02
        
        if random.randrange(10) == 0:
            f = 1.0 if random.randrange(2) == 1 else 0.0
            tol = 0.2
            
        v = (numpy.random.random(10000)*0.9+0.1)*(random.random()*0.9+0.1) #numpy.abs(numpy.random.normal(0, 1, 10))
#        v[0] = 5.0
#        v[1] = 4.0
#        v[2] = 3.0
#        v[3] = 2.0
        
        s_newton = solve_newton(v, f)
        s_hist = solve_histogram(v, f)

        rel_err = abs(s_newton - s_hist) / (s_newton+0.01)
        err_max = max(err_max, rel_err)
        
        print 'iter=%d, f=%.4f, s_newton=%.4f, s_hist=%.4f, rel_err=%f, err_max=%f' % (i, f, s_newton, s_hist, rel_err, err_max)
                
        assert rel_err < tol, (i, f, s_newton, s_hist, rel_err)

    
if __name__ == '__main__':
    main()
    