from sym_adjpdr.prism import *
from sym_adjpdr.model import *
import islpy as isl
from copy import deepcopy

MAX_PROB = Fraction(9,10)

pl = Model.from_prism_file("prism/probline.prism", MAX_PROB, True)
ctx = isl.Context()

def test_equality():
    var = "x"
    F5 = Frame.from_vector(ctx, var, [Fraction(1,16),Fraction(4,16),Fraction(11,16)])
    F5_ = Frame.from_vector(ctx, var, [Fraction(1,16),Fraction(4,16),Fraction(3,16)])

    assert not F5 == F5_

def test_theta_probline():
    var = "x"
    F1 = Frame.from_vector(ctx, var, [1,0,0])
    F2 = Frame.from_vector(ctx, var, [Fraction(1,2),Fraction(1,2),0])
    F3 = Frame.from_vector(ctx, var, [Fraction(1,4),Fraction(1,2),Fraction(1,4)])
    F4 = Frame.from_vector(ctx, var, [Fraction(1,8),Fraction(3,8),Fraction(1,2)])
    F5 = Frame.from_vector(ctx, var, [Fraction(1,16),Fraction(4,16),Fraction(11,16)])

    ThetaF1 = pl.Theta(F1)
    ThetaF2 = pl.Theta(F2)
    ThetaF3 = pl.Theta(F3)
    ThetaF4 = pl.Theta(F4)

    assert ThetaF1 == F2
    assert ThetaF2 == F3
    assert ThetaF3 == F4
    assert ThetaF4 == F5