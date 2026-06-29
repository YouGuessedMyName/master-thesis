from sym_adjpdr.frames import *
from sym_adjpdr.model import *
from sym_adjpdr.generalization import iterate_isl_set
import z3

def Ca(M: Model) -> FrameSet:
    F = Frame.zeroes(M.ctx, M.vars)
    F[M.init] = 1
    return FrameSet([(F,M.max_prob)], M.vars)

def De(_F: Frame, G: FrameSet, M: Model, _print_policiy: bool = False) -> FrameSet:
    return M.Psi(G)

def Cs(F: Frame, _G: FrameSet, M: Model) -> Frame:
    return M.Phi(F)

def disjoint_union(F_region: Frame, region: isl.Set, F_not_region: Frame, not_region: isl.Set) -> Frame:
    restricted_F_region = F_region.pw.intersect_domain(region)
    restricted_F_not_region = F_not_region.pw.intersect_domain(not_region)
    return Frame(restricted_F_region.union_add(restricted_F_not_region), F_region.domain, F_region.variables)

def CmGen(F: Frame, G: FrameSet, M: Model) -> Frame:
    Phi_F = M.Phi(F)
    w, r = G.eqs[0]
    w_non_zero = list(iterate_isl_set(w.pw.non_zero_set()))

    # Set up and solve equation system.
    u = [z3.Real(f"u_{i}") for i in range(len(w_non_zero))]
    opt = z3.Optimize()
    for ui in u:
        opt.add(ui >= 0)
        opt.add(ui <= 1)
    opt.add(z3.Sum([u[i] * w.eval(s) for i,s in enumerate(w_non_zero)]) <= r)
    opt.add([u[i] >= Phi_F.eval(s) for i,s in enumerate(w_non_zero)])
    opt.maximize(z3.Sum(u))
    opt.check()
    model = opt.model()
    sol = [model[ui].as_fraction() for ui in u]

    # Convert back to frame
    res = Frame.from_pieces(isl.DEFAULT_CONTEXT, F.variables, 
        [(isl.Set.from_point(s), sol[i]) for i,s in enumerate(w_non_zero)], default_val=Fraction(1))
    res = disjoint_union(res, w.pw.non_zero_set(), Phi_F, w.pw.zero_set())

    return res

def compute_meet(min: Frame, w: Frame, r_: Fraction, coeffs: list[isl.Point], s: isl.Point | None, d: Frame, Z: Frame):
    # str_d = str(d)
    # str_Z = str(Z)
    
    if len(coeffs) == 0:
        if s is None and r_ == 0:
            return Frame.meet(Z, d)
        elif s is not None:
            fr = r_ / w.eval(s)
            if min.eval(s) <= fr and fr < 1:
                res = Frame.meet(Z,d).set_point(s, isl.Val(frac_to_isl(fr)))
                # str_res = str(res)
                return res
    else:
        s_ = coeffs.pop()
        # Debug
        min_s_ = min.eval(s_)
        w_s_ = w.eval(s_)
        
        
        if min.eval(s_) == 0:
            d_ = d.copy().set_point(s_, isl.Val.zero(isl.DEFAULT_CONTEXT))
            Z = Frame.meet(Z, compute_meet(min, w, r_, coeffs.copy(), s, d_, Z))
        if w.eval(s_) <= r_:
            d_ = d.copy().set_point(s_, isl.Val.one(isl.DEFAULT_CONTEXT))
            r_ = r_ - w.eval(s_)
            Z = Frame.meet(Z, compute_meet(min, w, r_, coeffs.copy(), s, d_, Z))
        if s is None and min.eval(s_) < 1: # Choose s_ as the unique fractional coordinate.
            Z = Frame.meet(Z, compute_meet(min, w, r_, coeffs.copy(), s_, d, Z))
    
    return Z

def CbGen(F: Frame, G: FrameSet, M: Model) -> Frame:
    assert len(G.eqs) == 1
    w, r = G.eqs[0][0], G.eqs[0][1]
    coeffs = list(iterate_isl_set(w.pw.non_zero_set()))
    Phi_F = M.Phi(F)
    meetZk = compute_meet(Phi_F, w, r, coeffs.copy(), None, Frame.ones(isl.DEFAULT_CONTEXT, F.variables), Frame.ones(isl.DEFAULT_CONTEXT, F.variables))
    
    if meetZk == Frame.ones(isl.DEFAULT_CONTEXT, F.variables): # Zk is empty...
        meetZk = Phi_F
    
    # New
    res = Frame.from_pieces(isl.DEFAULT_CONTEXT, F.variables, 
        [(isl.Set.from_point(s), meetZk.eval(s)) for i,s in enumerate(coeffs)], default_val=1)

    # res = Frame.meet(res, M.Chi(F))
    res = disjoint_union(res, w.pw.non_zero_set(), Phi_F, w.pw.zero_set())
    return res
