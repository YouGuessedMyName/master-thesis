import islpy as isl
from sym_adjpdr.frames import Vars, frac_to_isl,eval_safe
import math
from fractions import Fraction

from sym_adjpdr.islpy_to_sympy import vtp

def val_to_aff(v: isl.Val, space: isl.Space) -> isl.Aff:
    return isl.Aff.zero_on_domain(space).set_constant_val(v)

def interpolate(x1: int, y1: int, x2: int, y2: int, var: isl.Aff, space: isl.Space) -> isl.Aff:
    if x2 - x1 == 0:
        a = Fraction(0,1)
    else:
        a = Fraction(y2 - y1, x2 - x1)
    b = y1 - a * x1
    a_aff = val_to_aff(isl.Val(frac_to_isl(a)), space)
    e = a_aff * var + val_to_aff(isl.Val(frac_to_isl(b)), space)
    return e

def find_partitions_list(vars: Vars, maximum_amount: int = 10**4) -> list[tuple[tuple[int], isl.BasicSet]]:
    """
    Partition a hyper-rectangle into ≤ maximum_amount equal smaller cubes.

    vars: dict[str, tuple(lb, ub)]
    returns: list of isl.BasicSet
    """

    ctx = isl.DEFAULT_CONTEXT

    names = list(vars.keys())
    dims = len(names)

    # ---- 1. compute grid resolution per dimension ----
    # we distribute cube count evenly across dimensions
    k = int(round(maximum_amount ** (1 / dims)))
    k = max(1, k)

    grid_sizes = [min(ub-lb+1, k) for (_, (lb, ub)) in vars.items()]

    # adjust to stay under maximum_amount
    while math.prod(grid_sizes) > maximum_amount:
        for i in range(dims):
            if grid_sizes[i] > 1:
                grid_sizes[i] -= 1
                break

    # ---- 2. build partitions ----
    partitions = []

    def build_constraints(i, indices, constraints, bounds):
        if i == dims:
            # construct isl set
            parts = []
            for c in constraints:
                parts.append(c)

            set_str = "{ [" + ", ".join(names) + "] : " + " and ".join(parts) + " }"
            return [(isl.BasicSet(set_str), bounds)]

        name = names[i]
        lb, ub = vars[name]
        steps = grid_sizes[i]

        step = (ub - lb) / steps

        results = []

        for j in range(steps):
            lo = math.ceil(lb + j * step)
            hi = math.floor(lb + (j + 1) * step)

            new_constraints = constraints + [
                f"{lo} <= {name}",
                f"{name} <= {hi}"
            ]

            new_bounds = bounds + [(lo, hi)]

            results.extend(build_constraints(i + 1, indices + [j], new_constraints, new_bounds))

        return results

    # flatten recursion result
    def flatten(x):
        if isinstance(x, list):
            out = []
            for y in x:
                out.extend(flatten(y))
            return out
        return [x]

    partitions = flatten(build_constraints(0, [], [], []))

    return partitions

def pwqp_to_pwaff_overapproximation(pw: isl.PwQPolynomial, partitions_list: list[isl.BasicSet], space: isl.Space, variable_index: int) -> isl.PwAff:
    """
    Convert a isl.PwQPolynomial into an isl.PwAff overapproximation, 
    in the sense that the PwAff is connected, 
    and that the slope of the result is greater or equal to the slope of the input at all points.

    Assumes that the polynomial is decreasing in the variable corresponding to variable_index.
    """
    res_pwaff = None
    x_isl = isl.Aff.var_on_domain(space, isl.dim_type.set, variable_index)
    for bset, bounds in partitions_list:
        x1, x2 = bounds[variable_index][0], bounds[variable_index][1]
        p1 = isl.Point.zero(space).set_coordinate_val(isl.dim_type.set, variable_index, isl.Val(x1))
        p2 = isl.Point.zero(space).set_coordinate_val(isl.dim_type.set, variable_index, isl.Val(x2))
        y1 = eval_safe(pw, p1)
        y2 = eval_safe(pw, p2)

        aff = interpolate(x1, vtp(y1), x2, vtp(y2), x_isl, space)
        if res_pwaff is None:
            res_pwaff = isl.PwAff.from_aff(aff).intersect_domain(bset)
        else:
            res_pwaff = res_pwaff.union_add(isl.PwAff.from_aff(aff).intersect_domain(bset))
    return res_pwaff