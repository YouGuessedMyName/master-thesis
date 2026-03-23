import islpy as isl
import z3

def z3_to_isl_set(expr: z3.BoolRef, variables: list[str], bounds: dict[str, tuple[int,int]]):
    """
    Convert a Z3 conjunction into an isl.Set.
    variables: ordered list of variable names
    bounds: dict v -> (lb, ub)
    """
    ctx = isl.Context()

    constraints = []

    def extract(e):
        if z3.is_and(e):
            res = []
            for c in e.children():
                res.extend(extract(c))
            return res
        return [e]

    atoms = extract(expr)

    def to_str(a):
        # handle <=, >=, ==
        lhs = a.arg(0)
        rhs = a.arg(1)

        def expr_to_str(e):
            if z3.is_int_value(e):
                return str(e.as_long())
            elif z3.is_const(e):
                return str(e)
            elif z3.is_add(e):
                return "(" + " + ".join(expr_to_str(c) for c in e.children()) + ")"
            elif z3.is_mul(e):
                return "(" + " * ".join(expr_to_str(c) for c in e.children()) + ")"
            elif z3.is_sub(e):
                return f"({expr_to_str(e.arg(0))} - {expr_to_str(e.arg(1))})"
            else:
                raise ValueError(f"Unsupported expr: {e}")

        l = expr_to_str(lhs)
        r = expr_to_str(rhs)

        if a.decl().name() == "<=":
            return f"{l} <= {r}"
        elif a.decl().name() == ">=":
            return f"{l} >= {r}"
        elif a.decl().name() == "=":
            return f"{l} = {r}"
        else:
            raise ValueError(f"Unsupported atom: {a}")

    for a in atoms:
        constraints.append(to_str(a))

    # add bounds
    for v in variables:
        lb, ub = bounds[v]
        constraints.append(f"{lb} <= {v}")
        constraints.append(f"{v} <= {ub}")

    constraint_str = " and ".join(constraints)
    var_str = ",".join(variables)

    isl_str = f"{{ [{var_str}] : {constraint_str} }}"

    return isl.Set.read_from_str(ctx, isl_str)