from sym_adjpdr.prism import *
from sym_adjpdr.model import *
import islpy as isl
from copy import deepcopy

MAX_PROB = Fraction(9,10)

pl = Model.from_prism_file("prism/probline.prism", MAX_PROB, True)
ctx = isl.Context()

def test_phi_probline():
    var = "x"
    F0 = Frame.from_vector(ctx, var, [0,0,0])
    F1 = Frame.from_vector(ctx, var, [0,0,1])
    F2 = Frame.from_vector(ctx, var, [0,Fraction(1,2),1])
    F3 = Frame.from_vector(ctx, var, [Fraction(1,4),Fraction(3,4),1])
    F4 = Frame.from_vector(ctx, var, [Fraction(4,8),Fraction(7,8),1])
    F5 = Frame.from_vector(ctx, var, [Fraction(11,16),Fraction(15,16),1])

    PhiF0 = pl.Phi(F0)
    PhiF1 = pl.Phi(F1)
    PhiF2 = pl.Phi(F2)
    PhiF3 = pl.Phi(F3)
    PhiF4 = pl.Phi(F4)
    
    assert F1 == PhiF0
    assert F2 == PhiF1
    assert F3 == PhiF2
    assert F4 == PhiF3
    assert F5 == PhiF4
