from dataclasses import dataclass

from adjpdr.helpers import Frac
from sym_adjpdr.prism import *
import z3

DENOM_LIMIT = 1e4

type State = list[tuple[str, int]]

@dataclass
class Frame:
    """Conceptually, a frame/expectation is a function from States to values in [0,1].
    Internally, this is a list of tuples which represent a piecewise function."""
    frame: list[tuple[z3.BoolRef, Frac]]
    z3_frame: z3.ArithRef
    module: Module

    def __init__(self, frame, module):
        self.frame = frame
        self.z3_frame = z3.Sum([z3.If(guard, z3.Q(val.numerator, val.denominator), 0) for guard, val in frame])
        self.module = module

    def f(self, s: State) -> Frac:
        return z3.simplify(z3.substitute(self.z3_frame, [(z3.Int(name), z3.IntVal(val)) for name, val in s]))
    
    def __le__(self, other: "Frame"):
        """self <= other, iff for all states, other is at least as great as self."""
        s = z3.Solver()
        s.add(self.z3_frame > other.z3_frame)
        for vname, (lb, ub) in self.module.variables.items():
            s.add(z3.Int(vname) >= lb)
            s.add(z3.Int(vname) <= ub)
        return s.check() == z3.unsat
