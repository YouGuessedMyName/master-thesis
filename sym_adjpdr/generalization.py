from sym_adjpdr.frames import *
from sym_adjpdr.model import *
from sym_adjpdr.islpy_to_sympy import *
from sym_adjpdr.sympy_to_islpy import *
from sym_adjpdr.sympy_to_z3 import *

# def Phi_generalization(F: Frame, G: FrameSet, z: Frame, M: Model, _ = None):
#     assert len(G.eqs) == 1
#     w = G.eqs[0][0]
#     z_non_zero = z.pw.intersect_domain(w.pw.non_zero_set())
#     Phi_zero = M.Phi(F).pw.intersect_domain(w.pw.zero_set())
#     return Frame(z_non_zero.union_add(Phi_zero), F.domain, F.variables)

# def no_generalization(_F: Frame, _G: FrameSet, z: Frame, _M: Model, _ = None):
#     return z

def iterate_isl_set(S: isl.Set) -> Iterator[isl.Point]:
    while not S.is_empty():
        p = S.sample_point()
        yield p
        S = S.subtract(isl.Set.from_point(p))

def generalize(F: Frame, G: FrameSet, M: Model, state_generalization: Callable, h_fallback: Callable):
    assert len(G.eqs) == 1
    z = Frame.ones(isl.DEFAULT_CONTEXT, F.variables)
    w = G.eqs[0][0]
    r_ = G.eqs[0][1]
    for s in iterate_isl_set(w.pw.non_zero_set()):
        delta, z_g = state_generalization(F,s,M)
        z = Frame.meet(z, z_g)
        r_ -= w.eval(s) * delta
        if r_ < 0:
            return h_fallback(F,G,M) # Generalization failed
    if not M.Phi(Frame.meet(F, z)) <= z:
        return h_fallback(F,G,M) # Generalization failed
    return z # Generalization succeeded

def isl_point_to_sym_state(p: isl.Point, sym_vars: list[sp.Symbol]) -> dict[sp.Symbol, Fraction]:
    return {x : vtp(p.get_coordinate_val(i)) for i, x in enumerate(sym_vars)}
