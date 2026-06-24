from sym_adjpdr.frames import *
from sym_adjpdr.model import *
from sym_adjpdr.heuristics import *
from sym_adjpdr.generalization import iterate_isl_set
import z3
import islpy as isl

def point(space: isl.Space, x: int, y: int):
    p = isl.Point.zero(space)
    p = p.set_coordinate_val(isl.dim_type.set, 0, isl.Val.int_from_si(isl.DEFAULT_CONTEXT, x))
    p = p.set_coordinate_val(isl.dim_type.set, 1, isl.Val.int_from_si(isl.DEFAULT_CONTEXT, y))
    return p

def test_compute_meet():
    variables = {'x': (0, 5), 'y': (0, 2)}
    w = Frame(pw=isl.PwAff("{ [x, y] -> [(0)] : (3 <= x <= 5 and 0 <= y <= 2) or (y = 3 - x and 0 < x <= 2) or (x = 0 and 0 <= y <= 2) or (x = 1 and y = 0); [x, y] -> [(1)/10] : x = 1 and y = 1; [x, y] -> [(9)/20] : x = 2 and (y = 2 or y = 0) }"), domain=isl.Set("{ [x, y] : 0 <= x <= 5 and 0 <= y <= 2 }"), variables={'x': (0, 5), 'y': (0, 2)}, factor=1, is_empty=False)
    r = Fraction(2, 5)
    min = Frame(pw=isl.PwAff("{ [x, y] -> [(0)] : 0 <= x <= 5 and (y = 0 or y = 2); [x, y] -> [(1)] : y = 1 and 0 <= x <= 5 }"), domain=isl.Set("{ [x, y] : 0 <= x <= 5 and 0 <= y <= 2 }"), variables={'x': (0, 5), 'y': (0, 2)}, factor=1, is_empty=False)
    spc = make_domain(isl.DEFAULT_CONTEXT, variables).get_space()
    coeffs = [point(spc, 1, 1), point(spc, 2, 2), point(spc, 2, 0)]
    meetZk = compute_meet(min, w, r, coeffs.copy(), None, Frame.ones(isl.DEFAULT_CONTEXT, variables), Frame.ones(isl.DEFAULT_CONTEXT, variables))

    min_str = str(min)
    w_str = str(w)

    mZk = str(meetZk)

    z = Frame.from_pieces(isl.DEFAULT_CONTEXT, variables, 
        [(isl.Set.from_point(s), meetZk.eval(s)) for i,s in enumerate(coeffs)], default_val=Fraction(1))
    G = FrameSet([(w, r)], variables)
    assert z in G and min <= z

def test_compute_meet2():
    variables = {'x': (0, 5), 'y': (0, 2)}
    w = Frame(pw=isl.PwAff("{ [x, y] -> [(0)] : (x >= 0 and x <= y <= 2) or (4 <= x <= 5 and 0 <= y <= 2) or (y = -2 + x and 2 <= x <= 3) or (x = 1 and y = 0); [x, y] -> [(9)/100] : x = 2 and y = 1; [x, y] -> [(81)/200] : x = 3 and (y = 2 or y = 0) }"), domain=isl.Set("{ [x, y] : 0 <= x <= 5 and 0 <= y <= 2 }"), variables={'x': (0, 5), 'y': (0, 2)}, factor=1, is_empty=False)
    r = Fraction(3, 10)
    min = Frame(pw=isl.PwAff("{ [x, y] -> [(0)] : 0 <= x <= 5 and (y = 0 or y = 2); [x, y] -> [(1)] : y = 1 and 0 <= x <= 5 }"), domain=isl.Set("{ [x, y] : 0 <= x <= 5 and 0 <= y <= 2 }"), variables={'x': (0, 5), 'y': (0, 2)}, factor=1, is_empty=False)
    spc = make_domain(isl.DEFAULT_CONTEXT, variables).get_space()
    coeffs = [point(spc, 3, 2), point(spc, 3, 0), point(spc, 2, 1), ]
    min_str = str(min)
    w_str = str(w)
    meetZk = compute_meet(min, w, r, coeffs.copy(), None, Frame.ones(isl.DEFAULT_CONTEXT, variables), Frame.ones(isl.DEFAULT_CONTEXT, variables))

    z = Frame.from_pieces(isl.DEFAULT_CONTEXT, variables, 
        [(isl.Set.from_point(s), meetZk.eval(s)) for i,s in enumerate(coeffs)], default_val=Fraction(1))
    G = FrameSet([(w, r)], variables)
    mZk = str(meetZk)
    assert z in G and min <= z

def test_compute_meet3():
    variables = {'x': (0, 5), 'y': (0, 2)}
    w = Frame(pw=isl.PwAff("{ [x, y] -> [(0)] : (x >= 0 and 0 <= y <= 4 - x and y <= 2) or (y = 2 and 3 <= x <= 4) or (x = 5 and y = 1); [x, y] -> [(729)/10000] : x = 4 and y = 1; [x, y] -> [(6561)/20000] : x = 5 and (y = 2 or y = 0) }"), domain=isl.Set("{ [x, y] : 0 <= x <= 5 and 0 <= y <= 2 }"), variables={'x': (0, 5), 'y': (0, 2)}, factor=1, is_empty=False)
    r = Fraction(129, 1000)
    min = Frame(pw=isl.PwAff("{ [x, y] -> [(0)] : 0 <= x <= 5 and (y = 0 or y = 2); [x, y] -> [(1)] : y = 1 and 0 <= x <= 5 }"), domain=isl.Set("{ [x, y] : 0 <= x <= 5 and 0 <= y <= 2 }"), variables={'x': (0, 5), 'y': (0, 2)}, factor=1, is_empty=False)
    spc = make_domain(isl.DEFAULT_CONTEXT, variables).get_space()
    coeffs = [point(spc, 5, 2), point(spc, 5, 0), point(spc, 4, 1)]
    min_str = str(min)
    w_str = str(w)
    meetZk = compute_meet(min, w, r, coeffs.copy(), None, Frame.ones(isl.DEFAULT_CONTEXT, variables), Frame.ones(isl.DEFAULT_CONTEXT, variables))

    z = Frame.from_pieces(isl.DEFAULT_CONTEXT, variables, 
        [(isl.Set.from_point(s), meetZk.eval(s)) for i,s in enumerate(coeffs)], default_val=Fraction(1))
    G = FrameSet([(w, r)], variables)
    mZk = str(meetZk)
    truth = z in G
    assert z in G and min <= z

