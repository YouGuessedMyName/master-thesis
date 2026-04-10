from adjpdr.adjpdr import *
from adjpdr.examples import *

CAV = "prism/Benchmarks_CAV/"

heurs = [Cs, Cb, C01, C01_alt, COpt]
used = Cb
M = from_prism_file("prism/Benchmarks_CAV/chain_small.pm", 0.5, "goal")

testAdjointPDRdown(M, heurs, used, propagate_=False, print_=True, assert_=True, loop_check=True)