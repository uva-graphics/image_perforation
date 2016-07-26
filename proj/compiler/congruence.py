
from z3 import *

class CongruenceError(Exception):
    pass

def is_congruent(s, m, value, var_assume=None, ignore_errors=True, verbose=False):
    """
    Returns True if str expression s is congruent to value mod m (via z3). Or False if it cannot be proved.

    If provided, var_assume(varname) is called for each var. If it returns False then is_congruent() returns False.
    If it returns a non-empty str then that string is added to the assumption.    
    """
    s_full = '(%s) %% %d == %d' % (s, m, value)
    d = {}
    assumeL = []
    while True:
        try:
            expr = eval(s_full, d)
            break
        except NameError, e:
            name = e.message.split("'")[1]
            if var_assume is not None:
                assume = var_assume(name)
                if assume == False:
                    return False
                elif isinstance(assume, str):
                    if len(assume):
                        assumeL.append(assume)
                else:
                    raise ValueError('bad var_assume return')
            d[name] = Int(name)
        except Exception, e:
            if ignore_errors:
                return False
            else:
                raise CongruenceError(e.message)
    
    s = Solver()
#    s.set('timeout', 10000)                  # Connelly: disabled timeout. Ideally would be enabled but some z3 do not support it
#    print expr
        
    s.add(Not(expr))
#    print assumeL
    for assume in assumeL:
        try:
            s.add(eval(assume, d))
        except Exception, e:
            if ignore_errors:
                return False
            else:
                raise CongruenceError(e.message)
                
    r = s.check()
    ans = r == unsat
    if verbose:
        print 'congruence test: %s, s.t. %s => %r' % (expr, ','.join(assumeL), ans)

    return ans
    
def main():
    L = [(lambda: is_congruent('x*2',   2, 0), True),
         (lambda: is_congruent('x*2+1', 2, 0), False),
         (lambda: is_congruent('x*2',   2, 1), False),
         (lambda: is_congruent('x*2+1', 2, 1), True),
         (lambda: is_congruent('x*3',   2, 0), False),
         (lambda: is_congruent('x*3',   2, 0, lambda x: 'x%2==0'), True),
         (lambda: is_congruent('x*3',   2, 0, lambda x: 'x%2==1'), False),
         (lambda: is_congruent('x*3',   2, 1, lambda x: 'x%2==1'), True),
         (lambda: is_congruent('x*3',   2, 1, lambda x: False), False),
         (lambda: is_congruent('x*3+1', 2, 1, lambda x: 'x%2==0'), True),
         (lambda: is_congruent('x*4-y', 4, 0, lambda x: 'x%2==0' if x == 'x' else 'y%4==0'), True),
         (lambda: is_congruent('x*4-y', 4, 1, lambda x: 'x%2==0' if x == 'x' else 'y%4==0'), False),
         (lambda: is_congruent('x*4',   2, 0), True),
         (lambda: is_congruent('x*4+1', 2, 0), False),
         (lambda: is_congruent('x*4+2', 2, 0), True),
         (lambda: is_congruent('x*4+3', 2, 0), False),
         (lambda: is_congruent('x*4',   2, 1), False),
         (lambda: is_congruent('x*4+1', 2, 1), True),
         (lambda: is_congruent('x*4+2', 2, 1), False),
         (lambda: is_congruent('x*4+3', 2, 1), True),
         (lambda: is_congruent('x*4+y*4',   4, 0), True),
         (lambda: is_congruent('x*4+y*4+1', 4, 0), False),
         (lambda: is_congruent('x*4+y*4',   4, 1), False),
         (lambda: is_congruent('x*4+y*4+1', 4, 1), True),
         (lambda: is_congruent('x+t*delta_n*g(y,x,X_COORD)', 2, 0), False),
         (lambda: is_congruent('(r-center_coord)**2/(2.0*blur_kernel_sigma**2)', 2, 0), False)]
         
    for (i, (f, correct)) in enumerate(L):
        print 'Testing %d' % i
        ans = f()
        assert ans == correct, ('Got %r should be %r' % (ans, correct))
        
if __name__ == '__main__':
    main()
