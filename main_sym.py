from sym_adjpdr.prism import *
from sym_adjpdr.model import *
from sym_adjpdr.adjpdr import *
from sym_adjpdr.heuristics import *
from sym_adjpdr.generalization import *
from sym_adjpdr.exponential_generalization import *


MAX_PROB = Fraction(80,100)

ctx = isl.Context()
M = Model.from_prism_file(ctx, "prism/chain_small_lin_gen.pm", MAX_PROB, False)

heurs = []
used_heur = CbGen

gens = []
used_gen = exponential_generalize_state

testAdjointPDRdown(M, heurs, used_heur, gens, used_gen, propagate_=False, print_=True, assert_=True, loop_check=True)
