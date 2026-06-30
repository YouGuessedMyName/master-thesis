from sym_adjpdr.frames import *
from sym_adjpdr.islpy_utils import val_to_aff
from sym_adjpdr.model import *
from sym_adjpdr.linear_generalization import theta_domain
from sympy import Rational, root, simplify, nan, zoo
from sym_adjpdr.visualization import plot_exponential_with_pw_aff
from sym_adjpdr.generalization import iterate_isl_set


def limit_denominator_lower(x, max_denominator):
    """
    Largest fraction <= x with denominator <= max_denominator.
    """
    f = Fraction(x).limit_denominator(max_denominator)

    if f <= x:
        return f

    # Move one step down in the Farey sense
    return Fraction(f.numerator - 1, f.denominator).limit_denominator(max_denominator)

def exponential_generalize_state(F: Frame, _G: FrameSet, M: Model, z: Frame, s: isl.Point) -> tuple[Fraction, Frame]:
    z_ = Frame.ones(isl.DEFAULT_CONTEXT, F.variables)
    # print(f"Generalizing state: {s}, with delta: {delta}")
    for i, (xi, (_, u_xi)) in enumerate(F.variables.items()):
        _, F_, _ = exponential_generalize_variable(F, s, i, xi, u_xi, M)
        z_ = Frame.meet(z_, F_)
    delta = z_.eval(s)
    return z_.eval(s), z_

def exponential_through_3(x0, h, y0, y1, y2):
    y0 = float(y0)
    y1 = float(y1)
    y2 = float(y2)
    # y_i may be Rational objects

    b = (y0*y2 - y1**2) / (y0 + y2 - 2*y1)

    ah = (y2 - b) / (y1 - b)
    a = root(ah, h)          # exact h-th root if possible

    c = simplify((y0 - b) / a**x0)

    return a, b, c

def exponential_through_3_exact(x0, h, y0, y1, y2):
    y0 = Rational(y0)
    y1 = Rational(y1)
    y2 = Rational(y2)
    # y_i may be Rational objects

    b = simplify((y0*y2 - y1**2) / (y0 + y2 - 2*y1))

    ah = simplify((y2 - b) / (y1 - b))
    a = root(ah, h)          # exact h-th root if possible

    c = simplify((y0 - b) / a**x0)

    return a, b, c

def exponential_to_1_through_3_exact(x0, h, y0, y1, y2, max_x):
    y0 = Rational(y0)
    y1 = Rational(y1)
    y2 = Rational(y2)

    ah = ((1 - y0) / (1 - y1)).simplify()
    a = ah**(Rational(1, h))

    if ((1 - y2) - a**(max_x - (x0 + 2*h))).simplify() != 0:
        raise ValueError("Points do not fit 1 - a^(Z-x) exactly")

    return a

def eval_exponential(a,b,c,d,x) -> Fraction:
    return c * a**(x-d) + b

def float_interpolate(x1: int, y1: float, x2: int, y2: float) -> tuple[float, float]:
    if x2 - x1 == 0:
        a = 0
    else:
        a = (y2 - y1) / (x2 - x1)
    b = y1 - a * x1
    return a, b

FL_ACC_LOSS = 0.2

def affine_overapproximation(a,b,c,d, x_isl, min_x,max_x, theta_set: isl.Set, no_pieces, space, variables: Vars, lowest_start) -> Frame:
    true_no_pieces = min((max_x-min_x+1)//2, no_pieces)
    distance = math.ceil((max_x-min_x) / true_no_pieces)
    
    x1 = max_x

    result = Frame.ones(isl.DEFAULT_CONTEXT, variables)
    # Here, we assume y0 to be leftmost!
    lowest = lowest_start
    while x1 >= 0:
        x0 = max(x1-distance+1, min_x)
        # print("range", x0,x1)

        not_y0 = eval_exponential(a,b,c,d,x1 + FL_ACC_LOSS)
        not_y1 = eval_exponential(a,b,c,d,x1+1 + FL_ACC_LOSS)

        slope = (not_y1 - not_y0) 

        #slope, _ = float_interpolate(x0, not_y0, x1, not_y1)

        # y1 = max_y_so_far
        if not lowest == lowest_start:
            lowest += -slope
        slope_compensation = lowest - slope * x1
        
        # print(slope_compensation)
        # with this offset, it will appear starting at zero, plus accounting for the y so far.
        

        slope_aff = val_to_aff(isl.Val(frac_to_isl(Fraction(slope))), space)
        e: isl.Aff = (x_isl * slope_aff) + val_to_aff(isl.Val(frac_to_isl(Fraction(slope_compensation))), space)
        #e: isl.Aff = (x_isl * slope_aff) + val_to_aff(isl.Val(1), space)
        # x - x1 <= 0 <-> x <= x1
        # x0 - x <= 0 <-> x0 <= x
        e_domain = theta_set.add_constraint(isl.Constraint.inequality_from_aff(-x_isl + isl.Val(x1)))\
            .add_constraint(isl.Constraint.inequality_from_aff(x_isl - isl.Val(x0)))
        e = e.intersect_domain(e_domain)

        result.pw = result.pw.union_min(e)


        lowest += (x1-x0) * -slope
        x1 -= distance

        # TODO account for floating point inaccuracies!

    # print(result)
    return result

def exponential_generalize_variable(F: Frame, s: isl.Point, i: int, x_i: str, u_xi: int, M: Model) -> tuple[bool, Frame]:
    xi_isl = isl.Aff.var_on_domain(M.domain.space, isl.dim_type.set, i)
    s_xi = s.get_coordinate_val(isl.dim_type.set, i)
    Phi_5_F = M.Phi(M.Phi(M.Phi(M.Phi(M.Phi(F)))))
    if s_xi == u_xi:
        return False, Frame.ones(isl.DEFAULT_CONTEXT, F.variables), None
    if u_xi-2 < 0:
        return False, Frame.ones(isl.DEFAULT_CONTEXT, F.variables), None
    s0 = s.copy().set_coordinate_val(isl.dim_type.set, i, isl.Val(u_xi))
    s1 = s.copy().set_coordinate_val(isl.dim_type.set, i, isl.Val(u_xi-1))
    s2 = s.copy().set_coordinate_val(isl.dim_type.set, i, isl.Val(u_xi-2))
    y0 = Phi_5_F.eval(s0)
    y1 = Phi_5_F.eval(s1)
    y2 = Phi_5_F.eval(s2)

    # y = c * a^x + b
    a,b,c = exponential_through_3_exact(-2, 1, y2, y1, y0)
    d = u_xi
    # Now correct the b...
    # b -= limit_denominator_lower(eval_exponential(a,b,c,u_xi), 1e5)
    # y0 -= eval_exponential(a,b,c,u_xi)
    # y1 -= eval_exponential(a,b,c,u_xi)
    # y2 -= eval_exponential(a,b,c,u_xi)
    # print(x_i, f"({u_xi-2},{y2}) ({u_xi-1},{y1}) ({u_xi},{y0})")

    print(f"{c} * ({a})^(x-{d}) + {b}")

    if a.has(nan,zoo) or b.has(nan,zoo):
        return False, Frame.ones(isl.DEFAULT_CONTEXT, F.variables), None


    # assert eval_exponential(a,b,c,d,u_xi) == y0
    # assert eval_exponential(a,b,c,d,u_xi-1) == y1
    # assert eval_exponential(a,b,c,d,u_xi-2) == y2

    theta = theta_domain(i, xi_isl, s_xi, s, M)

    # We need to convert to float because the exact representation will become too big to handle for large input sizes!
    lowest_start = min(y0, Phi_5_F.eval(s0)) + Fraction(1,10000)
    
    F_res = affine_overapproximation(float(a),float(b),float(c),float(d), xi_isl, vtp(s_xi),u_xi, theta, M.no_generalize_partitions, M.domain.space, F.variables, lowest_start)
    
    # fig = plot_exponential_with_pw_aff(a,b,c,d, [u_xi-2, u_xi-1, u_xi], [y2, y1, y0], F_res, s, i, xlim=(0,u_xi), ylim=(0,1), padding=0)
    # fig.savefig("exponential.png", dpi=300, bbox_inches="tight")
    # print([float(F_res.eval({"c": c, "g": 0})) for c in range(u_xi+1)])
    
    # F_res_restricted = F_res.copy()
    # F_res_restricted.pw = F_res_restricted.pw.intersect_domain(theta)

    # Phi_5_F_restricted = Phi_5_F.copy()
    # Phi_5_F_restricted.pw = Phi_5_F_restricted.pw.intersect_domain(theta)

    # print("F", F_res)
    # print("Phi", Phi_5_F)
    # le_set = Phi_5_F.pw.le_set(F_res.pw)
    # gt_set = F_res.pw.gt_set(Phi_5_F.pw)
    # for p in iterate_isl_set(le_set):
    #     print(p)
    
    # for p in iterate_isl_set(gt_set):
    #     print("gt", p)

    # phi = Phi_5_F.eval({"c": 9, "g": 0})
    # res = F_res.eval({"c": 9, "g": 0})
    # print(phi, res)
    if Phi_5_F <= F_res:
        init_val = F_res.eval(M.init)
        assert M.Phi(F_res) <= F_res
        
        return True, F_res, theta
    return False, Frame.ones(isl.DEFAULT_CONTEXT, F.variables), theta
