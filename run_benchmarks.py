from sym_adjpdr.prism import *
from sym_adjpdr.model import *
from sym_adjpdr.adjpdr import *
from sym_adjpdr.heuristics import *
from sym_adjpdr.generalization import *
from sym_adjpdr.exponential_generalization import *
from pathlib import Path
import sys
from multiprocessing import Process
import time

TIMEOUT = 2  # seconds

ctx = isl.Context()
NO_GEN_PARTITIONS = 100
PROPAGATE = False

DEBUG = False
TRACE = False
# [Cs, Cb]  [Cs, CbGen, CmGen]
HEURISTICS = [Cs, CbGen]
# [no_generalization, linear_generalize_state_conflict, linear_generalize_state_binary, exponential_generalize_state]
GENERALIZATIONS = [no_generalization, linear_generalize_state_conflict, linear_generalize_state_binary, exponential_generalize_state]

MIN_ITERATION = int(sys.argv[1])
iteration = 0
BENCHMARK_FOLDER = Path("benchmarks")

def run_benchmark(M: Model, do_propagate: bool, heuristics, used_heuristic, generalizations, used_generalization, 
                   print_ : bool = True, assert_: bool = True, loop_check: bool = True):
    result = adjointPDRdown(M,do_propagate,heuristics,used_heuristic, generalizations, used_generalization, print_, assert_, loop_check)
    print(result[0], end=" ")
    # Long-running work
    # time.sleep(3)

for file in sorted(BENCHMARK_FOLDER.iterdir()):
    if file.is_file():
        with file.open("r") as f:
            max_prob = Fraction(f.readline().replace("//", "").replace(" ", ""))
            model = Model.from_prism_file(ctx, str(file), max_prob, False, NO_GEN_PARTITIONS)
            
            for heur in HEURISTICS:
                for gen in GENERALIZATIONS:
                    if iteration < MIN_ITERATION:
                        continue

                    if TRACE:
                        print("**NOW RUNNING**", str(file), float(max_prob), heur.__name__, gen.__name__, "...")
                    
                    p = Process(target=run_benchmark, args=(model, False,[heur], heur, [gen], gen, DEBUG, DEBUG, DEBUG))
                    start = time.perf_counter()
                    p.start()
                    p.join(TIMEOUT)
                    if p.is_alive():
                        p.terminate()
                        p.join()
                        print(iteration, str(file), float(max_prob), heur.__name__, gen.__name__, "T/O")
                    else:
                        elapsed = time.perf_counter() - start
                        print(iteration, str(file), float(max_prob), heur.__name__, gen.__name__, f"{elapsed:.3f}")
                    iteration += 1
                    

    

