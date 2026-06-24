from sym_adjpdr.prism import *
from sym_adjpdr.model import *
from sym_adjpdr.adjpdr import *
from sym_adjpdr.heuristics import *

MAX_PROB = Fraction(40,100)

ctx = isl.Context()
M = Model.from_prism_file(ctx, "prism/lingen.pm", MAX_PROB, False)

heurs = [CmGen, CbGen]
used_heur = CmGen

gens = [Phi_generalization, no_generalization, linear_generalize_state_conflict]
used_gen = linear_generalize_state_conflict

testAdjointPDRdown(M, heurs, used_heur, gens, used_gen, propagate_=False, print_=True, assert_=True, loop_check=True)
