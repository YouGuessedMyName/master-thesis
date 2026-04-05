from sym_adjpdr.frames import *
from sym_adjpdr.model import *

def Ca(M: Model) -> FrameSet:
    F = Frame.zeroes(M.ctx, M.vars)
    F[M.init] = 1
    return FrameSet([(F,M.max_prob)], M.vars)

def Cs(F: Frame, _G: FrameSet, M: Model) -> Frame:
    return M.Phi(F)

def De(_F: Frame, G: FrameSet, M: Model, _print_policiy: bool = False) -> FrameSet:
    return M.Psi(G)