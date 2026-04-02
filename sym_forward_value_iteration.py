from sym_adjpdr.prism import *
from sym_adjpdr.model import *
import islpy as isl
from copy import deepcopy

MAX_PROB = Fraction(9,10)

model = Model.from_prism_file("prism/probline.prism", MAX_PROB, True)


MAX_ITERS = 10
F = Frame.zero(model.ctx, model.vars)
F[{"x": 0}] = 1
# print("prop", model.prop)
# print("F", F)
badness = Fraction(0)
for iter in range(MAX_ITERS):
    print(iter)
    print(F)
    print("badness", badness)
    if badness > MAX_PROB:
        print("unsafe")
        break
    F = model.Theta(F)
    # badness += F.sum_over_region(model.bad)
    # F = F.zero_region(model.bad)
    
