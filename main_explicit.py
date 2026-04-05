from adjpdr.adjpdr import *
from adjpdr.examples import *


heurs = [Cs]
used = Cs
M = example_21()

testAdjointPDRdown(M, heurs, used, propagate_=False, print_=True, assert_=True, loop_check=True)