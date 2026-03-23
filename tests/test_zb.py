from adjpdr.heuristics import *
from adjpdr.examples import *
from adjpdr.spaces import *
import random
import numpy as np

TESTS = 100
N = 4
epsilon = 0.01

# If this test fails, its just rounding errors dw.
def test_generators():
    for _ in range(TESTS):
        row = V.random(N)
        r = Frac(random.uniform(0,1)).limit_denominator(DENOM_LIMIT)
        with_cdd = sorted(generator_set_cdd(row, r))
        own_impl = sorted(generator_set(row, r))
        equal = all(np.all(np.array(c) - np.array(o) <= epsilon) for c,o in zip(with_cdd,own_impl))
        if not equal:
            print("row", row)
            print("r", r)
            print("with_cdd", [str(v) for v in with_cdd])
            print("own_impl", [str(v) for v in own_impl])
            # print("with_cdd", with_cdd)
            # print("own_impl", own_impl)
        assert equal

def test_meet():
    for _ in range(TESTS):
        r = V.random(N)
        r0 = Frac(random.uniform(0,1)).limit_denominator(DENOM_LIMIT)
        v = V.random(N)

        # Counterexample
        # r = V([Frac(3/4), Frac(0), Frac(0), Frac(1/4)])
        # r0 = Frac(1/4)
        # v = V(V.zeroes(N-1) + [Frac(1)])
        slow = meet_Zk_slow(r, r0, v)
        fast = meet_Zk_fast(r, r0, v)
        equal = slow == fast
        if not equal:
            print("r", r)
            print("r0", r0)
            print('v', v)
            print("slow", slow)
            print("fast", fast)
            # print("gens", [str(w) for w in generator_set(r, r0)])
            # print("tight", [str(w) for w in tight(generator_set(r,r0), r, r0)])
            # print("meet", meet(tight(generator_set(r,r0), r, r0)))
        assert equal