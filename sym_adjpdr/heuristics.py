from sym_adjpdr.frames import *
from sym_adjpdr.model import *

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

def Cmax(F: Frame, _G: FrameSet, M: Model):
    # TODO: heuristic that takes Cs, but for all values that matter in G, 
    # they are maximized s.t. the thing still holds.
    # Alternatively, it may even be viable to make a version of Cb because the G set will be sparse in most benchmark models anyway?
    # However, I suspect that it will be faster in practice to do something even simpler!
    # We could even have a case distinction where it counts the amount of states, and based on that decides what is viable.
    # For the simple line example it even suffices to just account for the one thing.
    # Even wilder idea: approach the limits in the heuristics as a cure for loops!
    res = M.Phi(F)
    res[M.init] = M.max_prob
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