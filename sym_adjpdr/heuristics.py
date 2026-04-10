from sym_adjpdr.frames import *
from sym_adjpdr.model import *

def Ca(M: Model) -> FrameSet:
    F = Frame.zeroes(M.ctx, M.vars)
    F[M.init] = 1
    return FrameSet([(F,M.max_prob)], M.vars)

def Cs(F: Frame, _G: FrameSet, M: Model) -> Frame:
    return M.Phi(F)

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