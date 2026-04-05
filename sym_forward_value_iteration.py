from sym_adjpdr.prism import *
from sym_adjpdr.model import *
import islpy as isl

MAX_PROB = Fraction(9,10)
ctx = isl.Context()
model = Model.from_prism_file(ctx, "tests/probline.prism", MAX_PROB, True)
print(model.module)

MAX_ITERS = 10
F = Frame.zeroes(model.ctx, model.vars)
F[{"x": 0}] = 1
# print("prop", model.prop)
# print("F", F)
badness = Fraction(0)
for iter in range(MAX_ITERS):
    print(iter)
    print(F)
    badness = F.sum_over_region(model.bad)
    print("badness", badness)
    if badness > MAX_PROB:
        print("unsafe")
        break
    F = model.Theta(F)
    
    
