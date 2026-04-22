from sympy import Symbol, Add, Mul, Pow, Integer, Rational, Piecewise
from z3 import Real, Int, If, Solver, sat
from fractions import Fraction
import z3

def sympy_to_z3(expr: Piecewise, var_map: dict[Symbol, z3.ExprRef]):
    """
    Convert a SymPy expression into a Z3 expression.
    
    var_map: dict mapping SymPy symbols → Z3 variables
    """

    # Variables
    if isinstance(expr, Symbol):
        return var_map[expr]

    # Constants
    if isinstance(expr, (int, Integer)):
        return expr

    if isinstance(expr, Rational):
        return expr.p / expr.q

    # Addition
    if isinstance(expr, Add):
        return sum(sympy_to_z3(arg, var_map) for arg in expr.args)

    # Multiplication
    if isinstance(expr, Mul):
        result = sympy_to_z3(expr.args[0], var_map)
        for arg in expr.args[1:]:
            result *= sympy_to_z3(arg, var_map)
        return result

    # Power
    if isinstance(expr, Pow):
        base = sympy_to_z3(expr.args[0], var_map)
        exp = expr.args[1]
        if exp.is_Integer:
            return base ** int(exp)
        raise NotImplementedError("Non-integer powers not supported in Z3 translation")

    raise NotImplementedError(f"Unsupported expression: {expr}")

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
) -> None | dict[str, Fraction]:
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

