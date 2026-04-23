import islpy as isl
from sym_adjpdr.frames import Vars
import math

def find_partitions_list(vars: Vars, maximum_amount: int = 1000) -> list[isl.BasicSet]:
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

    def build_constraints(i, indices, constraints):
        if i == dims:
            # construct isl set
            parts = []
            for c in constraints:
                parts.append(c)

            set_str = "{ [" + ", ".join(names) + "] : " + " and ".join(parts) + " }"
            return [isl.BasicSet(set_str)]

        name = names[i]
        lb, ub = vars[name]
        steps = grid_sizes[i]

        step = (ub - lb) / steps

        results = []

        for j in range(steps):
            lo = int(lb + j * step)
            hi = int(lb + (j + 1) * step)

            new_constraints = constraints + [
                f"{lo} <= {name}",
                f"{name} <= {hi}"
            ]

            results.extend(build_constraints(i + 1, indices + [j], new_constraints))

        return results

    # flatten recursion result
    def flatten(x):
        if isinstance(x, list):
            out = []
            for y in x:
                out.extend(flatten(y))
            return out
        return [x]

    partitions = flatten(build_constraints(0, [], []))

    return partitions

def pwqp_to_pwaff_overapproximation(pw: isl.PwQPolynomial, partitions_list: list[isl.BasicSet], variable_index: int) -> isl.PwAff:
    """
    Convert a isl.PwQPolynomial into an isl.PwAff overapproximation, 
    in the sense that the PwAff is connected, 
    and that the slope of the result is greater or equal to the slope of the input at all points.

    Assumes that the polynomial is decreasing in the variable corresponding to variable_index.
    """
    for bset in partitions_list:
        min_x = bset.lexmin().sample_point()
        pass

    