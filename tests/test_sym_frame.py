import islpy as isl
from fractions import Fraction
from sym_adjpdr.frames import *

# ----------------- helpers -----------------

def make_frame(ctx, vars, pieces):
    return Frame.from_pieces(ctx, vars, pieces)

def make_simple_frame(ctx, vars, guard, val):
    return make_frame(ctx, vars, [
        (isl.Set.read_from_str(ctx, guard), val)
    ])

def make_frame_str(ctx, vars, pieces):
    return Frame.from_pieces(ctx, vars, [(isl.Set.read_from_str(ctx, guard), isl.Aff.read_from_str(ctx, aff))
        for guard, aff in pieces])

s = isl.Set.read_from_str
a = isl.Aff

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

def test_eval_frac():
    ctx = isl.Context()
    vars = {"x": (0, 5)}

    f = make_frame(ctx, vars, [
        (isl.Set.read_from_str(ctx, "{ [x] : x <= 2 }"), Fraction(1,2)),
        (isl.Set.read_from_str(ctx, "{ [x] : x >= 3 }"), Fraction(2,3)),
    ])

    for x in range(6):
        expected = Fraction(1,2) if x <= 2 else Fraction(2,3)
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

# ----------------- dot tests with piecewise affine -----------------

def test_dot_single_var_affine():
    ctx = isl.Context()
    vars = {"x": (0, 5)}
    domain = make_domain(ctx, vars)
    # Example: 
    # Frame(pw=PwAff("{ [x, y] -> [(1)] : (x = 0 and y = 1) or (x = 1 and y = 0); [x, y] -> [(2)] : y = x and 0 <= x <= 1 }")
    pwf = isl.PwAff.read_from_str(ctx, "{ [x] -> [(x)] : x <= 3; [x] -> [(3)] : x > 3 }")
    f = Frame(pwf, domain, vars)
    pwg = isl.PwAff.read_from_str(ctx, "{ [x] -> [(6)] }")
    g = Frame(pwg, domain, vars)
    
    assert Frame.dot(f, g) == Frame.dot_slow(f, g)

def test_huge_domain():
    for _ in range(500):
        ctx = isl.Context()
        HUGE = 10**12
        vars = {"x": (0, HUGE)}
        f = Frame.from_pieces(ctx, vars, [(s(ctx, "{ [x] : }"), Fraction(1))])
        g = Frame.from_pieces(ctx, vars, [(s(ctx, "{ [x] : }"), Fraction(3))])

        assert f <= g
        assert Frame.dot(f,g) == 3 * (HUGE+1)
