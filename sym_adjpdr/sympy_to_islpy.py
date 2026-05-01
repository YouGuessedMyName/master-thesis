from sympy import Poly
import islpy as isl

def sympy_poly_to_isl_pwqp_multi(poly_expr, sym_vars, isl_ctx=None):
    """
    Convert a SymPy multivariate polynomial (e.g. from interpolate or Poly)
    into an isl.PwQPolynomial.

    Parameters
    ----------
    poly_expr : sympy expression
        Polynomial expression
    sym_vars : list of sympy symbols
        Variables (e.g. [x, y, z])
    isl_ctx : isl context (optional)

    Returns
    -------
    isl.PwQPolynomial
    """

    if isl_ctx is None:
        isl_ctx = isl.DEFAULT_CONTEXT

    poly = Poly(poly_expr, *sym_vars)

    terms = []

    # Iterate over all monomials
    for monom, coeff in poly.terms():
        if coeff == 0:
            continue

        term_parts = [str(coeff)]

        for var, exp in zip(sym_vars, monom):
            if exp == 0:
                continue
            elif exp == 1:
                term_parts.append(f"*{var}")
            else:
                term_parts.append(f"*{var}^{exp}")

        terms.append("".join(term_parts))

    isl_expr_str = " + ".join(terms)
    if isl_expr_str == "":
        isl_expr_str = str(poly_expr)

    # Build PwQPolynomial over full domain
    vars_str = ",".join(str(v) for v in sym_vars)
    pwqp_str = f"{{ [{vars_str}] -> ({isl_expr_str}) : true }}"
    pwqp = isl.PwQPolynomial.read_from_str(
        isl_ctx,
        pwqp_str
    )

    return pwqp