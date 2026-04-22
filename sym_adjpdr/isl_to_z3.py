import islpy as isl
from z3 import *

def pwqp_to_z3_solver(pwqp: isl.PwQPolynomial):
    space = pwqp.get_domain_space()
    dims = space.dim(isl.dim_type.set)

    # create Z3 variables
    z3_vars = [Int(f'x{i}') for i in range(dims)]

    s = Solver()
    disjuncts = []

    for piece in pwqp.get_pieces():
        domain = pwqp
        poly = piece.get_qpolynomial()

        # convert domain to Z3 constraints
        dom_constraints = []
        for c in domain.get_constraints():
            expr = 0
            for i in range(dims):
                coef = c.get_coefficient_val(isl.dim_type.set, i).to_python()
                expr += coef * z3_vars[i]

            const = c.get_constant_val().to_python()

            if c.is_equality():
                dom_constraints.append(expr + const == 0)
            elif c.is_inequality():
                dom_constraints.append(expr + const >= 0)

        # convert polynomial to Z3 expression (string-based shortcut)
        poly_str = str(poly)
        z3_expr = eval(poly_str, {f'x{i}': z3_vars[i] for i in range(dims)})

        # condition: domain AND poly > 0
        disjuncts.append(And(*(dom_constraints + [z3_expr > 0])))

    s.add(Or(*disjuncts))
    return s, z3_vars

pwqp = isl.PwQPolynomial.read_from_str(
    isl.DEFAULT_CONTEXT,
    "[c, g] -> { [c, g] -> (1/10 + 3/50*c) : g = 0 and 0 < c <= 15 }"
)

solver, vars = pwqp_to_z3_solver(pwqp)

if solver.check() == sat:
    m = solver.model()
    print({str(v): m[v] for v in vars})