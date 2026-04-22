from sym_adjpdr.generalization import *

ctx = isl.Context()
space = isl.Space.create_from_names(ctx, set=["x"])

def test_val_to_aff():
    for v in ["3", "1/2", "-6/4"]:
        val = isl.Val(v)
        assert val_to_aff(val, space).get_constant_val() == val

def eval_aff_at(aff, x_value: int):
    """Helper: evaluate isl.Aff at a single x."""
    space = aff.get_domain_space()
    point = isl.Point.zero(space)
    point = point.set_coordinate_val(
        isl.dim_type.set, 0, isl.Val.int_from_si(aff.get_ctx(), x_value)
    )
    return aff.eval(point).to_python()


def test_interpolate_simple_line():
    x = isl.Aff.var_on_domain(space, isl.dim_type.set, 0)

    # line through (1, 3) and (4, 9): y = 2x + 1
    aff = interpolate(1, 3, 4, 9, x, space)

    assert eval_aff_at(aff, 1) == 3
    assert eval_aff_at(aff, 2) == 5
    assert eval_aff_at(aff, 4) == 9

def test_aff_to_sympy_simple():
    # Build affine expression: 2*x + 3
    aff = isl.Aff.zero_on_domain(isl.LocalSpace.from_space(space))
    aff = aff.set_coefficient_val(isl.dim_type.in_, 0, isl.Val.int_from_si(ctx, 2))
    aff = aff.set_constant_val(isl.Val.int_from_si(ctx, 3))

    # Convert
    x = sp.Symbol("x")
    expr = aff_to_sympy(aff, [x])

    # Expected SymPy expression
    
    expected = 2*x + 3

    # Assert structural equality via canonical form
    assert sp.Poly(expr, x) == sp.Poly(expected, x)

def test_set_to_condition_interval():
    # Define set: { [x] : 0 <= x <= 10 }
    s = isl.Set.read_from_str(
        ctx,
        "{ [x] : 0 <= x <= 10 }"
    )

    x = sp.Symbol("x")

    cond = set_to_condition(s, [x])

    # Expected condition
    expected = sp.And(x >= 0, x <= 10)

    # Structural comparison via simplification

    res = sp.simplify_logic(sp.Equivalent(cond, expected))
    assert res

def test_frame_to_sympy_simple_piecewise():

    # Build PwAff:
    # if x >= 0: x + 1
    # if x < 0:  x - 1

    # Piece 1: x >= 0
    set_pos = isl.Set.read_from_str(ctx, "{ [x] : x >= 0 }")
    aff_pos = isl.Aff.read_from_str(ctx, "{ [x] -> [x + 1] }")

    # Piece 2: x < 0
    set_neg = isl.Set.read_from_str(ctx, "{ [x] : x < 0 }")
    aff_neg = isl.Aff.read_from_str(ctx, "{ [x] -> [x - 1] }")

    pw = isl.PwAff.read_from_str(ctx,  "{ [x] -> [x + 1] : x >= 0; [x] -> [x - 1] : x < 0 }")

    expr = frame_to_sympy(pw, ["x"])

    x = sp.Symbol("x")

    expected = sp.Piecewise(
        (x + 1, x >= 0),
        (x - 1, x < 0)
    )

    # Compare via logical equivalence, not structural equality
    for val in [-2, 0, 3]:
        assert expr.subs(x, val) == expected.subs(x, val)