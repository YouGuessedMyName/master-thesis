from sym_adjpdr.frames import *
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

# test_frame_pw.py

def make_frame(ctx, vars, pieces):
    return Frame.from_pieces(ctx, vars, pieces)


def test_eval():
    ctx = isl.Context()
    vars = {"x": (0, 5)}

    f = make_frame(ctx, vars, [
        (isl.Set.read_from_str(ctx, "{ [x] : x <= 2 }"), Fraction(1)),
        (isl.Set.read_from_str(ctx, "{ [x] : x >= 3 }"), Fraction(2)),
    ])

    for x in range(6):
        expected = 1 if x <= 2 else 2
        assert f.eval({"x": x}) == expected


def test_le():
    ctx = isl.Context()
    vars = {"x": (0, 5)}

    f = make_frame(ctx, vars, [
        (isl.Set.read_from_str(ctx, "{ [x] : }"), Fraction(1))
    ])
    g = make_frame(ctx, vars, [
        (isl.Set.read_from_str(ctx, "{ [x] : }"), Fraction(2))
    ])

    assert f <= g
    assert f.le_slow(g)


def test_meet():
    ctx = isl.Context()
    vars = {"x": (0, 5)}

    f = make_frame(ctx, vars, [
        (isl.Set.read_from_str(ctx, "{ [x] : }"), Fraction(3))
    ])
    g = make_frame(ctx, vars, [
        (isl.Set.read_from_str(ctx, "{ [x] : }"), Fraction(1))
    ])

    m = Frame.meet(f, g)

    for x in range(6):
        assert m.eval({"x": x}) == 1


def test_dot_fast_equals_slow():
    ctx = isl.Context()
    vars = {"x": (0, 5)}

    f = make_frame(ctx, vars, [
        (isl.Set.read_from_str(ctx, "{ [x] : x <= 2 }"), Fraction(1)),
        (isl.Set.read_from_str(ctx, "{ [x] : x >= 3 }"), Fraction(2)),
    ])

    g = make_frame(ctx, vars, [
        (isl.Set.read_from_str(ctx, "{ [x] : }"), Fraction(3)),
    ])

    assert Frame.dot(f, g) == Frame.dot_slow(f, g)


def test_partition_no_overlap():
    ctx = isl.Context()
    vars = {"x": (0, 5)}

    f = make_frame(ctx, vars, [
        (isl.Set.read_from_str(ctx, "{ [x] : x <= 3 }"), Fraction(1)),
        (isl.Set.read_from_str(ctx, "{ [x] : x >= 2 }"), Fraction(2)),
    ])

    # canonicalization ensures no ambiguity
    for x in range(6):
        val = f.eval({"x": x})
        assert val in [1, 2]