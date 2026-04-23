import sympy as sp
import z3
from sym_adjpdr.sympy_to_z3 import *

def test_simple_piecewise():
    x = sp.Symbol('x')
    expr = sp.Piecewise(
        (x**2, x <= 2),
        (x, True)
    )

    x_z3 = z3.Real('x')
    z3_expr = sympy_to_z3(expr, {x: x_z3})

    # Test behavior with solver
    s = z3.Solver()

    # Case 1: x = 2 → should use x^2
    s.push()
    s.add(x_z3 == 2)
    s.add(z3_expr != 4)  # 0^2 = 0
    assert s.check() == z3.unsat
    s.pop()

    # Case 2: x = 3 → should use x
    s.push()
    s.add(x_z3 == 3)
    s.add(z3_expr != 3)
    assert s.check() == z3.unsat
    s.pop()

# def test_min_like_piecewise():
#     x, n = sp.symbols('x n')

#     expr = sp.Piecewise(
#         (x, x <= n/2),
#         (n - x, True)
#     )

#     x_z3 = z3.Real('x')
#     n_z3 = z3.Real('n')

#     z3_expr = sympy_to_z3(expr, {x: x_z3, n: n_z3})

#     s = z3.Solver()

#     # Test point: x <= n/2
#     s.push()
#     s.add(n_z3 == 10, x_z3 == 3)
#     s.add(z3_expr != 3)
#     assert s.check() == z3.unsat
#     s.pop()

#     # Test point: x > n/2
#     s.push()
#     s.add(n_z3 == 10, x_z3 == 8)
#     s.add(z3_expr != 2)  # n - x = 2
#     assert s.check() == z3.unsat
#     s.pop()

# def test_nested_piecewise():
#     x = sp.symbols('x')

#     expr = sp.Piecewise(
#         (x, x < 0),
#         (sp.Piecewise((x**2, x < 2), (x + 1, True)), True)
#     )

#     x_z3 = z3.Real('x')
#     z3_expr = sympy_to_z3(expr, {x: x_z3})

#     s = z3.Solver()

#     # x < 0 → x
#     s.push()
#     s.add(x_z3 == -1)
#     s.add(z3_expr != -1)
#     assert s.check() == z3.unsat
#     s.pop()

#     # 0 <= x < 2 → x^2
#     s.push()
#     s.add(x_z3 == 1)
#     s.add(z3_expr != 1)
#     assert s.check() == z3.unsat
#     s.pop()

#     # x >= 2 → x + 1
#     s.push()
#     s.add(x_z3 == 3)
#     s.add(z3_expr != 4)
#     assert s.check() == z3.unsat
#     s.pop()

# def test_boolean_conditions():
#     x = sp.symbols('x')

#     expr = sp.Piecewise(
#         (1, (x > 0) & (x < 5)),
#         (0, True)
#     )

#     x_z3 = z3.Real('x')
#     z3_expr = sympy_to_z3(expr, {x: x_z3})

#     s = z3.Solver()

#     s.push()
#     s.add(x_z3 == 3)
#     s.add(z3_expr != 1)
#     assert s.check() == z3.unsat
#     s.pop()

#     s.push()
#     s.add(x_z3 == 6)
#     s.add(z3_expr != 0)
#     assert s.check() == z3.unsat
#     s.pop()