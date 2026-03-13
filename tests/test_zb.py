from adjpdr.heuristics import *
from adjpdr.examples import *
import random

TESTS = 1000
N = 4

for _ in range(TESTS):
    Gk = LowerSet([([Frac(random.uniform(0,1)).limit_denominator(100) for _ in range(N)], Frac(random.uniform(0,1)).limit_denominator(10))])
    #Gk = LowerSet([([Frac(random.uniform(0,1)).limit_denominator(10) for _ in range(N)], Frac(1))])
    #Gk = LowerSet([([Frac(1), Frac(0)], 1)])
    #F_k_minus_1 = [Frac(random.uniform(0,1)).limit_denominator(10) for _ in range(N)]
    F_k_minus_1 = [Frac(0) for _ in range(N)]
    #lambda_ = Frac(random.uniform(0,1)).limit_denominator(1000)
    lambda_ = Frac(1)
    M = example_21(lambda_)
    zb = conflict_heuristic_zb(F_k_minus_1, Gk, M)
    zbnew = conflict_heuristic_zb_new(F_k_minus_1, Gk, M)
    if zb != zbnew:
        print("lambda", lambda_)
        print("F_k_minus_1", str_list(F_k_minus_1))
        print("Gk", Gk)
        print("zb", str_list(zb))
        print("zbnew", str_list(zbnew))
    Zknew = generate_Zk_new(F_k_minus_1, Gk, M)
    Zkold = generate_zk(F_k_minus_1, Gk, M)
    if sorted(Zknew) != sorted(Zkold):
        print("lambda", lambda_)
        print("F_k_minus_1", str_list(F_k_minus_1))
        print("Gk", Gk)
        print("Phi(F_k-1)", str_list(Phi(F_k_minus_1,M)))
        print("Zkold", ([str_list(z) for z in sorted(Zkold)]))
        print("Zknew", sorted([str_list(z) for z in sorted(Zknew)]))
    assert sorted(Zkold) == sorted(Zknew)