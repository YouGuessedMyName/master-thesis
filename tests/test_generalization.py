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
    ctx = isl.DEFAULT_CONTEXT
    space = isl.Space.create_from_names(ctx, set=["x"])
    x = isl.Aff.var_on_domain(space, isl.dim_type.set, 0)

    # line through (1, 3) and (4, 9): y = 2x + 1
    aff = interpolate(1, 3, 4, 9, x, space)

    assert eval_aff_at(aff, 1) == 3
    assert eval_aff_at(aff, 2) == 5
    assert eval_aff_at(aff, 4) == 9