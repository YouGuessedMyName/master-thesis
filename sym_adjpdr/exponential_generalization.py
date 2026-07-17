from sym_adjpdr.frames import *
from sym_adjpdr.islpy_utils import val_to_aff
from sym_adjpdr.model import *
from sym_adjpdr.linear_generalization import theta_domain
from sympy import Rational, root, simplify, nan, zoo, I
from sym_adjpdr.visualization import plot_exponential_with_pw_aff

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

def eval_exponential(a,b,c,d,x) -> Fraction:
    res = c * a**(x-d) + b
    return res

FL_ACC_LOSS = 0

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

FIGURE = False

def exponential_generalize_variable(F: Frame, s: isl.Point, i: int, x_i: str, u_xi: int, M: Model) -> tuple[bool, Frame]:
    xi_isl = isl.Aff.var_on_domain(M.domain.space, isl.dim_type.set, i)
    s_xi = s.get_coordinate_val(isl.dim_type.set, i)
    Phi_4_F = M.Phi(M.Phi(M.Phi(M.Phi(F))))
    if s_xi == u_xi or u_xi-2 < 0:
        return False, Frame.ones(isl.DEFAULT_CONTEXT, F.variables)
    
    s0 = s.copy().set_coordinate_val(isl.dim_type.set, i, isl.Val(u_xi))
    s1 = s.copy().set_coordinate_val(isl.dim_type.set, i, isl.Val(u_xi-1))
    s2 = s.copy().set_coordinate_val(isl.dim_type.set, i, isl.Val(u_xi-2))
    y0 = Phi_4_F.eval(s0)
    y1 = Phi_4_F.eval(s1)
    y2 = Phi_4_F.eval(s2)

    a,b,c = exponential_through_3_exact(-2, 1, y2, y1, y0)
    d = u_xi

    if a.has(nan,zoo,I) or b.has(nan,zoo,I) or a < 0: # success?
        return False, Frame.ones(isl.DEFAULT_CONTEXT, F.variables)


    # assert eval_exponential(a,b,c,d,u_xi) == y0
    # assert eval_exponential(a,b,c,d,u_xi-1) == y1
    # assert eval_exponential(a,b,c,d,u_xi-2) == y2

    theta = theta_domain(i, xi_isl, s_xi, s, M)

    # We need to convert to float because the exact representation will become too big to handle for large input sizes!
    lowest_start = min(y0, Phi_4_F.eval(s0)) + Fraction(1,10000)
    
    z_ = affine_overapproximation(float(a),float(b),float(c),float(d), xi_isl, vtp(s_xi),u_xi, theta, M.no_generalize_partitions, M.domain.space, F.variables, lowest_start)

    if FIGURE:
        e = Frame(z_.pw.intersect_domain(theta), F.domain, F.variables)
        fig = plot_exponential_with_pw_aff(a,b,c,d, [u_xi-2, u_xi-1, u_xi], [y2, y1, y0], e, s, i, xlim=(0,u_xi), ylim=(0,1), padding=0)
        fig.savefig("exponential.png", dpi=300, bbox_inches="tight")

    if Phi_4_F <= z_:
        return True, z_
    return False, Frame.ones(isl.DEFAULT_CONTEXT, F.variables)


def exponential_generalize_state(F: Frame, s: isl.Point, M: Model) -> tuple[Fraction, Frame]:
    z = Frame.ones(isl.DEFAULT_CONTEXT, F.variables)
    # print(f"Generalizing state: {s}, with delta: {delta}")
    for i, (xi, (_, u_xi)) in enumerate(F.variables.items()):
        _, z_ = exponential_generalize_variable(F, s, i, xi, u_xi, M)
        z = Frame.meet(z, z_)
    return z.eval(s), z