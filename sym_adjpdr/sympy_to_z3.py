import sympy as sp
from z3 import Real, Int, If, Solver, sat
from fractions import Fraction
import z3

def sympy_to_z3(expr: sp.Expr, var_map: dict[sp.Symbol, z3.ExprRef]):
    """
    Convert a SymPy expression (including Piecewise) into a Z3 expression.

    var_map: dict mapping SymPy symbols → Z3 variables
    """

    def convert(e):
        # --- Symbols ---
        if isinstance(e, sp.Symbol):
            return var_map[e]

        # --- Numbers ---
        if isinstance(e, sp.Integer):
            return z3.IntVal(int(e))
        if isinstance(e, sp.Rational):
            return z3.RealVal(e.p) / z3.RealVal(e.q)
        if isinstance(e, sp.Float):
            return z3.RealVal(float(e))

        # --- Arithmetic ---
        if isinstance(e, sp.Add):
            return sum(convert(arg) for arg in e.args)

        if isinstance(e, sp.Mul):
            result = convert(e.args[0])
            for arg in e.args[1:]:
                result = result * convert(arg)
            return result

        if isinstance(e, sp.Pow):
            base, exp = e.args
            return convert(base) ** convert(exp)

        # --- Comparisons ---
        if isinstance(e, sp.Rel):
            lhs = convert(e.lhs)
            rhs = convert(e.rhs)

            if isinstance(e, sp.Le):
                return lhs <= rhs
            if isinstance(e, sp.Lt):
                return lhs < rhs
            if isinstance(e, sp.Ge):
                return lhs >= rhs
            if isinstance(e, sp.Gt):
                return lhs > rhs
            if isinstance(e, sp.Eq):
                return lhs == rhs

        # --- Boolean logic ---
        if isinstance(e, sp.And):
            return z3.And(*[convert(arg) for arg in e.args])
        if isinstance(e, sp.Or):
            return z3.Or(*[convert(arg) for arg in e.args])
        if isinstance(e, sp.Not):
            return z3.Not(convert(e.args[0]))

        # --- Piecewise ---
        if isinstance(e, sp.Piecewise):
            result = None
            for value, cond in reversed(e.args):
                z3_val = convert(value)
                z3_cond = convert(cond)

                if result is None:
                    # last branch
                    result = z3_val
                else:
                    result = z3.If(z3_cond, z3_val, result)

            return result

        if e == True or e == False:
            return e

        raise NotImplementedError(f"Unsupported expression: {type(e)} -> {e}")

    return convert(expr)

def check_in_bounds(
    e: z3.ExprRef,
    z3_vars: list[z3.ExprRef],
    lb: int,
    ub: int
) -> bool:
    """
    Return True iff there exists an assignment to z3_vars such that
    lb <= e <= ub holds.
    """
    s = Solver()

    # constrain expression to bounds
    s.add(e >= lb, e <= ub)

    # optional: variables are unconstrained unless user adds constraints
    # (kept for completeness; usually unnecessary)
    for v in z3_vars:
        s.add(v >= -z3.infinity, v <= z3.infinity)

    return s.check() == sat


def find_greater(
    e1: z3.ExprRef,
    e2: z3.ExprRef,
    z3_vars: dict[str, z3.ExprRef]
) -> None | dict[str, int]:
    """
    Return an assignment where e1 > e2, otherwise None.
    """

    s = Solver()

    # constraint: we want a satisfying assignment where e1 > e2
    s.add(e1 > e2)

    if s.check() != sat:
        return None

    m = s.model()

    result = {}

    for name, var in z3_vars.items():
        val = m.eval(var, model_completion=True)

        # convert Z3 numeric to Fraction safely
        if z3.is_int_value(val):
            result[name] = Fraction(val.as_long(), 1)
        elif z3.is_rational_value(val):
            num = val.numerator_as_long()
            den = val.denominator_as_long()
            result[name] = Fraction(num, den)
        else:
            # fallback for reals/algebraic values
            result[name] = Fraction(str(val))

    return result

def z3_to_python(v):
    # Boolean
    if z3.is_true(v):
        return True
    if z3.is_false(v):
        return False

    # Integer
    if z3.is_int_value(v):
        return v.as_long()

    # Rational / Real
    if z3.is_rational_value(v):
        num = v.numerator_as_long()
        den = v.denominator_as_long()
        return num / den

    # Fallback (decimal approximation)
    try:
        return float(v.as_decimal(10).replace('?', ''))
    except Exception:
        return v

def z3_eval(expr, assignments):
    """
    Evaluate a Z3 expression at concrete variable assignments.

    Parameters
    ----------
    expr : Z3 expression
        Expression containing Z3 variables.
    assignments : dict
        Mapping {Z3_var: value}

    Returns
    -------
    Python int/float/bool
    """

    s = Solver()

    # enforce the point
    for var, val in assignments.items():
        s.add(var == val)

    if s.check() != sat:
        raise ValueError("Assignments are inconsistent or unsat")

    m = s.model()
    val = m.evaluate(expr, model_completion=True)

    return z3_to_python(val)

