from sym_adjpdr.prism import *
from sym_adjpdr.model import *
from sym_adjpdr.adjpdr import *
from sym_adjpdr.heuristics import *
from sym_adjpdr.generalization import *
from sym_adjpdr.exponential_generalization import *


MAX_PROB = Fraction(99,100)

ctx = isl.Context()
no_generalization_partitions = 100
M = Model.from_prism_file(ctx, "prism/chain_huge.pm", MAX_PROB, False, no_generalization_partitions)
# M = Model.from_prism_file(ctx, "prism/chain_small_lin_gen.pm", MAX_PROB, True, no_generalization_partitions)

heurs = []
used_heur = CbGenChi

gens = []
used_gen = no_generalization

testAdjointPDRdown(M, heurs, used_heur, gens, used_gen, propagate_=False, print_=True, assert_=True, loop_check=True)
