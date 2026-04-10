from adjpdr.adjpdr import *
from adjpdr.examples import *

heurs = []
used = Cs
M = from_prism_file("prism/chain_small.pm", 0.25, "bad")

testAdjointPDRdown(M, heurs, used, propagate_=False, print_=True, assert_=True, loop_check=True)