from dataclasses import dataclass

from adjpdr.helpers import Frac
from sym_adjpdr.prism import *
import z3
from itertools import product

type State = dict[str, int]

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
        res = z3.simplify(z3.substitute(self.z3_frame, [(z3.Int(name), z3.IntVal(val)) for name, val in s.items()]))
        return Frac(res.py_value()).limit_denominator()
    
    def __getitem__(self, s: State):
        return self.f(s)
    
    def __le__(self, other: "Frame") -> bool:
        """self <= other, iff for all states, other is at least as great as self."""
        sol = z3.Solver()
        sol.add(self.z3_frame > other.z3_frame)
        for vname, (lb, ub) in self.module.variables.items():
            sol.add(z3.Int(vname) >= lb)
            sol.add(z3.Int(vname) <= ub)
        return sol.check() == z3.unsat
    
@dataclass
class FrameSet:
    """A set of frames satisfying a list of linear inequalties."""
    eqs: list[tuple[z3.ArithRef, Frac]]
    module: Module

    def contains_slow(self, F: Frame) -> bool:
        for (r, r0) in self.eqs:
            var_names = [vname for vname in self.module.variables]
            prod = list(product(*[range(lb.py_value(),ub.py_value()+1) for _vname, (lb,ub) in self.module.variables.items()]))
            states = [{var_names[i]: val for i, val in enumerate(vals)} for vals in prod]
            sm = sum([Frac.fix(r[s]) * F[s] for s in states])
            if sm > r0:
                return False
        return True
    
    def __contains__(self, F: Frame) -> bool:
        return self.contains_slow(F)
        