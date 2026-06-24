from sym_adjpdr.prism import *
from sym_adjpdr.model import *
from sym_adjpdr.adjpdr import *
from sym_adjpdr.heuristics import *

MAX_PROB = Fraction(50,100)

ctx = isl.Context()
M = Model.from_prism_file(ctx, "prism/lingen.pm", MAX_PROB, False)

heurs = [CmGen, CbGen]
used_heur = CbGen

gens = [linear_generalize_state_binary]
used_gen = linear_generalize_state_binary

testAdjointPDRdown(M, heurs, used_heur, gens, used_gen, propagate_=False, print_=True, assert_=True, loop_check=True)
