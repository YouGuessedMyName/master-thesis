from sym_adjpdr.prism import *
from sym_adjpdr.model import *
from sym_adjpdr.adjpdr import *
from sym_adjpdr.heuristics import *

MAX_PROB = Fraction(90,100)

ctx = isl.Context()
M = Model.from_prism_file(ctx, "prism/chain_small.pm", MAX_PROB, False)
# print("prop", M.prop)

heurs = [Cs, Cs1, Cmax]
used = Cs

testAdjointPDRdown(M, heurs, used, propagate_=False, generalization_=True, print_=False, assert_=True, loop_check=True)

# REMINDER!!! Input prism files need a more specific format, where:
# * All case distinctions are explicit
# * All variable updates are relative to the previous value x'=1 is not allowed, but x'=x+1 is!
# This will be fixed in the future but for now this is how it is.