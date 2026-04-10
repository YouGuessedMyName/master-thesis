from sym_adjpdr.prism import *
from sym_adjpdr.model import *
import islpy as isl
from copy import deepcopy

MAX_PROB = Fraction(9,10)

ctx = isl.Context()
model = Model.from_prism_file(ctx, "prism/line.prism", MAX_PROB, False)
print("prop", model.prop)

MAX_ITERS = 10**9
F = Frame.zeroes(model.ctx, model.vars)
for iter in range(MAX_ITERS):
    print(iter)
    print(F)
    F = model.Phi(F)
    if not F <= model.prop:
        print("unsafe!")
        break
print("done")