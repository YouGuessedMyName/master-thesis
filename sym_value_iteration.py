from sym_adjpdr.prism import *
from sym_adjpdr.model import *
import islpy as isl
from copy import deepcopy

MAX_PROB = Fraction(9,10)

model = Model.from_prism_file("prism/probline.prism", MAX_PROB, True)
print("prop", model.prop)

MAX_ITERS = 100
F = Frame.zero(model.ctx, model.vars)
for iter in range(MAX_ITERS):
    print(iter)
    print(F)
    F = model.Phi(F)
    if not F <= model.prop:
        print("unsafe!")
        break
