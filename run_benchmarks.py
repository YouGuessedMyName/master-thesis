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
import json

BENCHMARKS = "benchmarks"

TIMEOUT = 2  # seconds

ctx = isl.Context()
NO_GEN_PARTITIONS = 100
PROPAGATE = False

DEBUG = False
TRACE = True
# [Cs, Cb]  [Cs, CbGen, CmGen]
HEURISTICS = [Cs, CbGen]
# [no_generalization, linear_generalize_state_conflict, linear_generalize_state_binary, exponential_generalize_state]
GENERALIZATIONS = [None, linear_generalization, binary_generalization, exponential_generalization]

if len(sys.argv) > 1:
    MIN_ITERATION = int(sys.argv[1])
else:
    MIN_ITERATION = 0
iteration = 0
BENCHMARK_FOLDER = Path(BENCHMARKS)

with open(BENCHMARKS + "/lambdas.json", "r") as f:
    LAMBDAS = json.load(f)

def run_benchmark(M: Model, do_propagate: bool, heuristics, used_heuristic, generalizations, used_generalization, 
                   print_ : bool = True, assert_: bool = True, loop_check: bool = True):
    try:
        result = adjointPDRdown(M,do_propagate,heuristics,used_heuristic, generalizations, used_generalization, print_, assert_, loop_check)
    except MemoryError:
        print("M/O", end=" ")
    except:
        print("CRASHED", end=" ")
    print(result[0], end=" ")
    # Long-running work
    # time.sleep(3)

def hname(gen: Callable | None) -> str:
    return "None" if gen is None else gen.__name__

for file in sorted(BENCHMARK_FOLDER.iterdir()):
    if file.is_file() and str(file.suffix) == ".pm":
        if TRACE:
            print("Opening:", str(file))
        with file.open("r") as f:
            for lambda_float in LAMBDAS[str(file.name)]:
                lambda_ = Fraction(lambda_float)
                model = Model.from_prism_file(ctx, str(file), lambda_, False, NO_GEN_PARTITIONS, bad_label="goal")
                
                for heur in HEURISTICS:
                    for gen in GENERALIZATIONS:
                        if iteration < MIN_ITERATION:
                            continue

                        if TRACE:
                            print("**NOW RUNNING**", str(file), lambda_float, hname(heur), hname(gen), "...")
                        
                        p = Process(target=run_benchmark, args=(model, False,[heur], heur, [gen], gen, DEBUG, DEBUG, DEBUG))
                        start = time.perf_counter()
                        p.start()
                        p.join(TIMEOUT)
                        if p.is_alive():
                            p.terminate()
                            p.join()
                            print(iteration, str(file), lambda_float,hname(heur), hname(gen), "T/O")
                        else:
                            elapsed = time.perf_counter() - start
                            print(iteration, str(file), lambda_float, hname(heur), hname(gen), f"{elapsed:.3f}")
                        iteration += 1
                    
print("Done.")
    

