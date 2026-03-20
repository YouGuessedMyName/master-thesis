from sym_adjpdr.helpers import *
from sym_adjpdr.prism import *

PATH = "prism/line.prism"
with open(PATH, "r") as f:
    PRISM = f.read()

tree = prism_parser.parse(PRISM)
# print(tree.pretty())
m: Module = PrismTransformer().transform(tree)
m.set_property()
m.set_expected_result(PATH)
m.clear_constants()

def test_frame():
    s1: State = [("x", 2), ("y", 3)]
    s2: State = [("x", 1), ("y", 3)]
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