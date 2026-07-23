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

BENCHMARKS = "benchmarks_included"
TIMEOUT = 10#240  # seconds

NO_GEN_PARTITIONS = 100
PROPAGATE = False

DEBUG = False
TRACE = False
# [Cs, Cb]  [Cs, CbGen, CmGen]
HEURISTICS = [Cs, Cb]
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
        print(result[0], end=",")
    except MemoryError:
        print("M/O", end=",")
    except:
        print("CRASHED", end=",")

def hname(gen: Callable | None) -> str:
    return "None" if gen is None else gen.__name__


print("result", "no.", "file", "lambda", "heuristic", "generalization", f"time (T/O={TIMEOUT})", sep=",")
for file in sorted(BENCHMARK_FOLDER.iterdir()):
    if file.is_file() and str(file.suffix) == ".pm":
        if TRACE:
            print("Opening:", str(file))
        with file.open("r") as f:
            for lambda_float in LAMBDAS[str(file.name)]:
                lambda_ = Fraction(lambda_float).limit_denominator(1000)
                try:
                    ctx = isl.Context()
                    model = Model.from_prism_file(ctx, str(file), lambda_, False, NO_GEN_PARTITIONS, bad_label="goal")
                except:
                    print("CRASH LOADING", iteration,file,lambda_, "-", "-", "-", sep=",")
                    continue
                
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
                            print("?", iteration, str(file), lambda_float,hname(heur), hname(gen), "T/O", sep=",")
                        else:
                            elapsed = time.perf_counter() - start
                            print(iteration, str(file), lambda_float, hname(heur), hname(gen), f"{elapsed:.3f}", sep=",")
                        iteration += 1
                    
print("Done.")
    

