from sym_adjpdr.islpy_utils import interpolate
from sym_adjpdr.frames import *
from sym_adjpdr.model import *

def linear_generalize_state_conflict(F: Frame, _G: FrameSet, M: Model, z: Frame, s: isl.Point) -> tuple[Fraction, Frame]:
    delta = z.pw.eval(s)
    z_ = Frame.ones(isl.DEFAULT_CONTEXT, F.variables)
    # print(f"Generalizing state: {s}, with delta: {delta}")
    for i, (xi, (_, u_xi)) in enumerate(F.variables.items()):
        _, F_, _ = linear_generalize_variable(F, s, delta, i, xi, u_xi, M)
        z_ = Frame.meet(z_, F_)
    return z_.pw.eval(s), z_

N = 5

def linear_generalize_state_binary(F: Frame, _G: FrameSet, M: Model, _z: Frame, s: isl.Point) -> tuple[Fraction, Frame]:
    e_res = None
    upper_bounds = set()
    for i, (xi, (_, u_xi)) in enumerate(F.variables.items()):
        lb = Fraction(0)
        ub = Fraction(1)
        n = N
        while n > 0:
            mid = ub - (ub - lb) / 2
            success, _, e = linear_generalize_variable(F, s, isl.Val(frac_to_isl(mid)), i, xi, u_xi, M)
            if success:
                if e_res is None:
                    e_res = e
                else:
                    e_res = e_res.union_min(e) # TODO: investigate if this shouldn't be union_max?
                ub = mid # When succesful, we want to start searching lower.
            else:
                lb = mid
            upper_bounds.add(ub)
            n -= 1
        # print(e_res.eval(s))
        # print()
    min_ub = min(upper_bounds)
    if e_res is not None:
        result_frame = Frame(e_res.union_min(Frame.ones(isl.DEFAULT_CONTEXT, F.variables).pw), F.domain, F.variables)
    else:
        result_frame = Frame.ones(isl.DEFAULT_CONTEXT, F.variables)
    return result_frame.eval(s), result_frame

def theta_domain(i: int, xi_isl: isl.Aff, s_xi: isl.Val, s: isl.Point, M: Model):
    constraints = [isl.Constraint.equality_from_aff(
                isl.Aff.var_on_domain(M.domain.space, isl.dim_type.set, j) 
            - 
                s.get_coordinate_val(isl.dim_type.set, j))
            for j in range(len(M.vars)) if j != i
        ]
    theta: isl.Set = M.domain.copy().add_constraints(constraints) # all variables equal to s(x)
    # print('M domain', M.domain)
    # print('constraints', constraints)
    # print('theta in progress:', theta, 'i', i)
    # print('theta', theta)
    # print('var', isl.Aff.var_on_domain(M.domain.space, isl.dim_type.set, i))
    
    theta = theta.add_constraint(isl.Constraint.inequality_from_aff(xi_isl - s_xi)) # xi - s(xi) <= 0 <-> s(xi) <= xi
    # Note that the constraint xi <= u_xi is already implicit in the domain size!
    return theta

def linear_generalize_variable(F: Frame, s: isl.Point, delta: isl.Val, i: int, x_i: str, u_xi: int, M: Model) -> tuple[bool, Frame]:
    space = M.domain.space
    F_ = Frame.from_pieces(M.ctx, M.vars, [(isl.Set.from_point(s), delta)], default_val=Fraction(1))
    xi_isl = isl.Aff.var_on_domain(space, isl.dim_type.set, i)
    s_xi = s.get_coordinate_val(isl.dim_type.set, i)
    theta = theta_domain(i, xi_isl, s_xi, s, M)

    s_x_i_to_u_xi = s.set_coordinate_val(isl.dim_type.set, i, isl.Val(u_xi))
    Phi2_F = M.Phi(M.Phi(F))
    m_xi = vtp(Phi2_F.pw.eval(s_x_i_to_u_xi))
    
    e = interpolate(
        x1=vtp(s_xi),
        y1=vtp(delta),
        x2=u_xi,
        y2=m_xi,
        var=xi_isl,
        space=space
    )
    F__ = Frame.from_pieces(M.ctx, M.vars, [(theta, e)], default_val=Fraction(1))
    F__with_zeroes_on_theta = F__.zero_region(F.domain - theta)
    # print("Theta", theta)
    # print("F''", F__)
    # print(F__with_zeroes_on_theta)
    if M.Phi(M.Phi(F)) <= F__:
        # print(f"var: {x_i}; interpolating: x1 {vtp(s_xi)}, y1 {vtp(delta)}, x2 {u_xi}, y2 {m_xi}, SUCCESS.")
        # print(f"e: {e}")
        # print(f"gen res: {F__}")
        return True, Frame.meet(F_, F__), e.intersect_domain(theta)
    # print(f"var: {x_i}; interpolating: x1 {vtp(s_xi)}, y1 {vtp(delta)}, x2 {u_xi}, y2 {m_xi}, FAIL.")
    return False, Frame.ones(isl.DEFAULT_CONTEXT, F.variables), None