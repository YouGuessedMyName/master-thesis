from sym_adjpdr.prism import *
from sym_adjpdr.model import *
from sym_adjpdr.adjpdr import *
from sym_adjpdr.heuristics import *

MAX_PROB = Fraction(1,4)

ctx = isl.Context()
M = Model.from_prism_file(ctx, "prism/probline_new.prism", MAX_PROB, True)
print("prop", M.prop)

heurs = []
used = Citer

testAdjointPDRdown(M, heurs, used, propagate_=False, print_=False, assert_=True, loop_check=True)