# from sym_adjpdr.frames import *
# from sym_adjpdr.prism import *
# from sym_adjpdr.z3_to_isl import *
# import islpy as isl

# PATH = "prism/line.prism"
# with open(PATH, "r") as f:
#     PRISM = f.read()

# tree = prism_parser.parse(PRISM)
# # print(tree.pretty())
# m: Module = PrismTransformer().transform(tree)
# m.constants["N"] = 4
# m.set_property()
# m.set_expected_result(PATH)
# m.clear_constants()

# # test_frame_pw.py

# def make_frame(ctx, vars, pieces):
#     return Frame.from_pieces(ctx, vars, pieces)

# def make_simple_frame(ctx, vars, guard, val):
#     return make_frame(ctx, vars, [
#         (isl.Set.read_from_str(ctx, guard), val)
#     ])

# def test_eval():
#     ctx = isl.Context()
#     vars = {"x": (0, 5)}

#     f = make_frame(ctx, vars, [
#         (isl.Set.read_from_str(ctx, "{ [x] : x <= 2 }"), Fraction(1)),
#         (isl.Set.read_from_str(ctx, "{ [x] : x >= 3 }"), Fraction(2)),
#     ])

#     for x in range(6):
#         expected = 1 if x <= 2 else 2
#         assert f.eval({"x": x}) == expected


# def test_le():
#     ctx = isl.Context()
#     vars = {"x": (0, 5)}

#     f = make_frame(ctx, vars, [
#         (isl.Set.read_from_str(ctx, "{ [x] : }"), Fraction(1))
#     ])
#     g = make_frame(ctx, vars, [
#         (isl.Set.read_from_str(ctx, "{ [x] : }"), Fraction(2))
#     ])

#     assert f <= g
#     assert f.le_slow(g)


# def test_meet():
#     ctx = isl.Context()
#     vars = {"x": (0, 5)}

#     f = make_frame(ctx, vars, [
#         (isl.Set.read_from_str(ctx, "{ [x] : }"), Fraction(3))
#     ])
#     g = make_frame(ctx, vars, [
#         (isl.Set.read_from_str(ctx, "{ [x] : }"), Fraction(1))
#     ])

#     m = Frame.meet(f, g)

#     for x in range(6):
#         assert m.eval({"x": x}) == 1


# def test_dot_fast_equals_slow():
#     ctx = isl.Context()
#     vars = {"x": (0, 5)}

#     f = make_frame(ctx, vars, [
#         (isl.Set.read_from_str(ctx, "{ [x] : x <= 2 }"), Fraction(1)),
#         (isl.Set.read_from_str(ctx, "{ [x] : x >= 3 }"), Fraction(2)),
#     ])

#     g = make_frame(ctx, vars, [
#         (isl.Set.read_from_str(ctx, "{ [x] : }"), Fraction(3)),
#     ])

#     assert Frame.dot(f, g) == Frame.dot_slow(f, g)


# def test_partition_no_overlap():
#     ctx = isl.Context()
#     vars = {"x": (0, 5)}

#     f = make_frame(ctx, vars, [
#         (isl.Set.read_from_str(ctx, "{ [x] : x <= 3 }"), Fraction(1)),
#         (isl.Set.read_from_str(ctx, "{ [x] : x >= 2 }"), Fraction(2)),
#     ])

#     # canonicalization ensures no ambiguity
#     for x in range(6):
#         val = f.eval({"x": x})
#         assert val in [1, 2]

# def test_frameset_contains():
#     ctx = isl.Context()
#     vars = {"x": (0, 2)}

#     r = make_simple_frame(ctx, vars, "{ [x] : x <= 2 }", 1)
#     F = make_simple_frame(ctx, vars, "{ [x] : x <= 2 }", 1)

#     fs = FrameSet([(r, Fraction(3))], vars)

#     assert F in fs
#     assert fs.contains_slow(F)


# def test_frameset_subset():
#     ctx = isl.Context()
#     vars = {"x": (0, 2)}

#     r1 = make_simple_frame(ctx, vars, "{ [x] : x <= 2 }", 1)
#     r2 = make_simple_frame(ctx, vars, "{ [x] : x <= 2 }", 2)

#     fs1 = FrameSet([(r1, Fraction(3))], vars)
#     fs2 = FrameSet([(r2, Fraction(6))], vars)

#     assert fs1 <= fs2

# test_frame_pw_multivar.py

import islpy as isl
from fractions import Fraction
from sym_adjpdr.frames import Frame, FrameSet

# ----------------- helpers -----------------

def make_frame(ctx, vars, pieces):
    return Frame.from_pieces(ctx, vars, pieces)

def make_simple_frame(ctx, vars, guard, val):
    return make_frame(ctx, vars, [
        (isl.Set.read_from_str(ctx, guard), val)
    ])

# ----------------- tests single variable -----------------

def test_eval_single_var():
    ctx = isl.Context()
    vars = {"x": (0, 5)}

    f = make_frame(ctx, vars, [
        (isl.Set.read_from_str(ctx, "{ [x] : x <= 2 }"), Fraction(1)),
        (isl.Set.read_from_str(ctx, "{ [x] : x >= 3 }"), Fraction(2)),
    ])

    for x in range(6):
        expected = 1 if x <= 2 else 2
        assert f.eval({"x": x}) == expected

def test_le_single_var():
    ctx = isl.Context()
    vars = {"x": (0, 5)}

    f = make_simple_frame(ctx, vars, "{ [x] : }", Fraction(1))
    g = make_simple_frame(ctx, vars, "{ [x] : }", Fraction(2))

    assert f <= g
    assert f.le_slow(g)

def test_meet_single_var():
    ctx = isl.Context()
    vars = {"x": (0, 5)}

    f = make_simple_frame(ctx, vars, "{ [x] : }", Fraction(3))
    g = make_simple_frame(ctx, vars, "{ [x] : }", Fraction(1))

    m = Frame.meet(f, g)
    for x in range(6):
        assert m.eval({"x": x}) == 1

def test_dot_single_var():
    ctx = isl.Context()
    vars = {"x": (0, 5)}

    f = make_frame(ctx, vars, [
        (isl.Set.read_from_str(ctx, "{ [x] : x <= 2 }"), Fraction(1)),
        (isl.Set.read_from_str(ctx, "{ [x] : x >= 3 }"), Fraction(2)),
    ])
    g = make_simple_frame(ctx, vars, "{ [x] : }", Fraction(3))

    assert Frame.dot(f, g) == Frame.dot_slow(f, g)

# ----------------- tests two variables -----------------

def test_eval_two_vars():
    ctx = isl.Context()
    vars = {"x": (0, 2), "y": (0, 2)}

    f = make_frame(ctx, vars, [
        (isl.Set.read_from_str(ctx, "{ [x, y] : x = y }"), Fraction(5)),
        (isl.Set.read_from_str(ctx, "{ [x, y] : x != y }"), Fraction(2)),
    ])

    for x in range(3):
        for y in range(3):
            expected = 5 if x == y else 2
            assert f.eval({"x": x, "y": y}) == expected

def test_le_two_vars():
    ctx = isl.Context()
    vars = {"x": (0, 1), "y": (0, 1)}

    f = make_frame(ctx, vars, [
        (isl.Set.read_from_str(ctx, "{ [x, y] : }"), Fraction(2))
    ])
    g = make_frame(ctx, vars, [
        (isl.Set.read_from_str(ctx, "{ [x, y] : }"), Fraction(5))
    ])

    assert f <= g
    assert f.le_slow(g)

def test_meet_two_vars():
    ctx = isl.Context()
    vars = {"x": (0, 1), "y": (0, 1)}

    f = make_frame(ctx, vars, [
        (isl.Set.read_from_str(ctx, "{ [x, y] : }"), Fraction(3))
    ])
    g = make_frame(ctx, vars, [
        (isl.Set.read_from_str(ctx, "{ [x, y] : }"), Fraction(1))
    ])

    m = Frame.meet(f, g)
    for x in range(2):
        for y in range(2):
            assert m.eval({"x": x, "y": y}) == 1

def test_dot_two_vars():
    ctx = isl.Context()
    vars = {"x": (0, 1), "y": (0, 1)}

    f = make_frame(ctx, vars, [
        (isl.Set.read_from_str(ctx, "{ [x, y] : x = y }"), Fraction(2)),
        (isl.Set.read_from_str(ctx, "{ [x, y] : x != y }"), Fraction(1)),
    ])
    g = make_simple_frame(ctx, vars, "{ [x, y] : }", Fraction(3))

    assert Frame.dot(f, g) == Frame.dot_slow(f, g)

# ----------------- FrameSet tests -----------------

def test_frameset_contains_two_vars():
    ctx = isl.Context()
    vars = {"x": (0, 1), "y": (0, 1)}

    r = make_simple_frame(ctx, vars, "{ [x, y] : x = y }", Fraction(2))
    F = make_simple_frame(ctx, vars, "{ [x, y] : x = y }", Fraction(1))

    fs = FrameSet([(r, Fraction(5))], vars)

    assert F in fs
    assert fs.contains_slow(F)

def test_frameset_subset_two_vars():
    ctx = isl.Context()
    vars = {"x": (0, 1), "y": (0, 1)}

    r1 = make_simple_frame(ctx, vars, "{ [x, y] : }", Fraction(1))
    r2 = make_simple_frame(ctx, vars, "{ [x, y] : }", Fraction(3))

    fs1 = FrameSet([(r1, Fraction(4))], vars)
    fs2 = FrameSet([(r2, Fraction(12))], vars)

    assert fs1 <= fs2