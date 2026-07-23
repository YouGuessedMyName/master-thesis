from sym_adjpdr.prism import *
from sym_adjpdr.model import *
from sym_adjpdr.adjpdr import *
from sym_adjpdr.heuristics import *
from sym_adjpdr.generalization import *
from sym_adjpdr.exponential_generalization import *


MAX_PROB = Fraction(9,10)

ctx = isl.Context()
no_generalization_partitions = 100
M = Model.from_prism_file(ctx, "benchmarks_included/brp_small.pm", MAX_PROB, False, no_generalization_partitions, bad_label="goal")

heurs = []
used_heur = Cs

gens = []
used_gen = exponential_generalization

testAdjointPDRdown(M, heurs, used_heur, gens, used_gen, propagate_=False, print_=True, assert_=True, loop_check=True)


# ctx = isl.Context()
# M = Model.from_prism_file(ctx, "benchmarks_included/chain_gigantic.pm", MAX_PROB, False, no_generalization_partitions, bad_label="goal")
# testAdjointPDRdown(M, heurs, used_heur, gens, used_gen, propagate_=False, print_=False, assert_=True, loop_check=True)