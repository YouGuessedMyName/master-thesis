from sym_adjpdr.prism import *
from sym_adjpdr.model import *
from sym_adjpdr.adjpdr import *
from sym_adjpdr.heuristics import *
from sym_adjpdr.generalization import *
from sym_adjpdr.exponential_generalization import *


MAX_PROB = Fraction(50,100)

ctx = isl.Context()
no_generalization_partitions = 100
M = Model.from_prism_file(ctx, "notebooks/spread_tiny.pm", MAX_PROB, False, no_generalization_partitions)
# M = Model.from_prism_file(ctx, "prism/chain_small_lin_gen.pm", MAX_PROB, True, no_generalization_partitions)

heurs = []
used_heur = Cs

gens = []
used_gen = None

testAdjointPDRdown(M, heurs, used_heur, gens, used_gen, propagate_=False, print_=True, assert_=True, loop_check=True)
