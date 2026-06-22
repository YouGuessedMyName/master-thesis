from sym_adjpdr.frames import *
from sym_adjpdr.model import *
from sym_adjpdr.generalization import iterate_isl_set, non_zero_states
import z3

def Ca(M: Model) -> FrameSet:
    F = Frame.zeroes(M.ctx, M.vars)
    F[M.init] = 1
    return FrameSet([(F,M.max_prob)], M.vars)

def Cs(F: Frame, _G: FrameSet, M: Model) -> Frame:
    return M.Phi(F)

def Cs1(F: Frame, G: FrameSet, M: Model) -> Frame:
    zero_set = G.eqs[0][0].pw.zero_set()
    phi = M.Phi(F)
    res = phi.set_region(zero_set, isl.Val(1))
    return res

def CmGen(F: Frame, G: FrameSet, M: Model):
    Phi_F = M.Phi(F)
    w, r = G.eqs[0]
    w_non_zero = list(iterate_isl_set(non_zero_states(G)))

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
    return res
    
def Citer(F: Frame, G: FrameSet, M: Model):
    """Conflict heuristic based on simply doing value iteration a couple of times."""
    MAX_ITERS = 1000
    for _iter in range(MAX_ITERS):
        newF = M.Phi(F)
        if newF == F:
            break
        if newF in G:
            F = newF
        else:
            # try to find the value that fucks it up and increase it to the maximum,
            #  s.t. it doesn't fuck it up anymore?
            pass
    return F

def COpt(F: Frame, G: FrameSet, M: Model) -> Frame:
    pass

def Cp(F: Frame, G: FrameSet, M: Model) -> Frame:
    """Conflict heuristic based on linear generalization."""
    # TODO

def De(_F: Frame, G: FrameSet, M: Model, _print_policiy: bool = False) -> FrameSet:
    return M.Psi(G)