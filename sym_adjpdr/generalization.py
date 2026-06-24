from sym_adjpdr.frames import *
from sym_adjpdr.model import *
from sym_adjpdr.islpy_to_sympy import *
from sym_adjpdr.sympy_to_islpy import *
from sym_adjpdr.sympy_to_z3 import *

PARTITIONS = None

def Phi_generalization(F: Frame, G: FrameSet, z: Frame, M: Model, _ = None):
    assert len(G.eqs) == 1
    w = G.eqs[0][0]
    z_non_zero = z.pw.intersect_domain(w.pw.non_zero_set())
    Phi_zero = M.Phi(F).pw.intersect_domain(w.pw.zero_set())
    return Frame(z_non_zero.union_add(Phi_zero), F.domain, F.variables)

def no_generalization(_F: Frame, _G: FrameSet, z: Frame, _M: Model, _ = None):
    return z

def iterate_isl_set(S: isl.Set) -> Iterator[isl.Point]:
    while not S.is_empty():
        p = S.sample_point()
        yield p
        S = S.subtract(isl.Set.from_point(p))

def generalization_framework(F: Frame, G: FrameSet, z: Frame, M: Model, state_generalization: Callable):
    assert len(G.eqs) == 1
    res = Frame.ones(isl.DEFAULT_CONTEXT, F.variables)
    w = G.eqs[0][0]
    r_ = G.eqs[0][1]
    debug = list(iterate_isl_set(w.pw.non_zero_set()))
    print(f"{G} has '{debug}' as non-zero entries")
    for s in iterate_isl_set(w.pw.non_zero_set()):
        delta, z__ = state_generalization(F,G,M,z,s)
        res = Frame.meet(res, z__)
        str_z_ = str(res)
        r_ -= w.eval(s) * delta
        if r_ < 0:
            return z # Generalization failed
    return res # Generalization succeeded

def isl_point_to_sym_state(p: isl.Point, sym_vars: list[sp.Symbol]) -> dict[sp.Symbol, Fraction]:
    return {x : vtp(p.get_coordinate_val(i)) for i, x in enumerate(sym_vars)}
