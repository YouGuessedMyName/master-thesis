from sym_adjpdr.helpers import *
from sym_adjpdr.prism import *
from sym_adjpdr.z3_to_isl import *
import islpy as isl

PATH = "prism/line.prism"
with open(PATH, "r") as f:
    PRISM = f.read()

tree = prism_parser.parse(PRISM)
# print(tree.pretty())
m: Module = PrismTransformer().transform(tree)
m.constants["N"] = 4
m.set_property()
m.set_expected_result(PATH)
m.clear_constants()

def test_frame():
    s1: State = {"x": 2, "y": 3}
    s2: State = {"x": 1, "y": 3}
    frame = Frame([(z3.Int("x") >= 2, Frac(1, 5)),
                    (z3.Int("y") <= 3, Frac(1, 10))], m)
    assert str(frame.z3_frame) == "If(x >= 2, 1/5, 0) + If(y <= 3, 1/10, 0)"
    assert frame.f(s1) == Frac(3, 10)
    assert frame.f(s2) == Frac(1, 10)

    frame2 = Frame([(z3.Int("x") >= 2, Frac(1, 5)),
                    (z3.Int("y") <= 3, Frac(1, 10))], m)
    assert frame <= frame2 and frame2 <= frame

    gframe = Frame([(z3.Int("x") >= 2, Frac(2, 5)),
                    (z3.Int("y") <= 3, Frac(1, 10))], m)
    assert frame <= gframe and (not gframe <= frame)

def test_simpl_subst():
    N = z3.Int("N")
    x = z3.Int("x")

    assert simpl_subst(N - 1, "N", 4) == 3
    assert simpl_subst(x < N, "N", 4) == z3.simplify(x < 4)

def test_frame_set():
    x = z3.Int("x")

    z = z3.IntVal(5)

    # F = [0 0 1 1] = 1 if x >= 2 else 0
    F = Frame([(z3.Int("x") >= 2, Frac(1))], m)
    # F2 = [0 1 1 1] = 1 if x >= 1 else 0
    F2 = Frame([(z3.Int("x") >= 1, Frac(1))], m)
    # eq frame = [0 1/4 1/4 1/4] = 1/4 if x >= 1 else 0
    eq_frame = Frame([(z3.Int("x") >= 1, Frac(1,4))], m)
    G = FrameSet([(eq_frame, Frac(1,2))], m)
    assert G.contains_slow(F)
    assert F in G
    assert not G.contains_slow(F2)
    assert not F2 in G

    y = z3.Int("y")
    # TODO extend test!

def test_z3_to_islpy():
    x = z3.Int("x")
    e = z3.And(x >= 1, x >= 2)
    e_isl = z3_to_isl_set(e, ["x"], {"x": [0,5]})
    assert str(e_isl) == "{ [x] : 2 <= x <= 5 }"

    y = z3.Int("")