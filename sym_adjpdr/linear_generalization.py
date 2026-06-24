from sym_adjpdr.islpy_utils import interpolate
from sym_adjpdr.frames import *
from sym_adjpdr.model import *

def linear_generalize_state_conflict(F: Frame, G: FrameSet, M, z: Frame, s: isl.Point) -> tuple[Fraction, Frame]:
    delta = z.pw.eval(s)
    z_ = Frame.ones(isl.DEFAULT_CONTEXT, F.variables)
    print(f"Generalizing state: {s}, with delta: {delta}")
    for i, (xi, (_, u_xi)) in enumerate(F.variables.items()):
        _, F_ = linear_generalize_variable(F, s, delta, i, xi, u_xi, M)
        z_ = Frame.meet(z_, F_)
    return delta, z_

def linear_generalize_variable(F: Frame, s: isl.Point, delta: isl.Val, i: int, x_i: str, u_xi: int, M: Model) -> tuple[bool, Frame]:
    space = M.domain.space
    F_ = Frame.from_pieces(M.ctx, M.vars, [(isl.Set.from_point(s), delta)], default_val=Fraction(1))
    xi_isl = isl.Aff.var_on_domain(space, isl.dim_type.set, i)
    s_xi = s.get_coordinate_val(isl.dim_type.set, i)
    theta: isl.Set = M.domain.copy().add_constraints(
        [isl.Constraint.equality_from_aff(
                isl.Aff.var_on_domain(space, isl.dim_type.set, j) 
            - 
                s.get_coordinate_val(isl.dim_type.set, j))
            for j in range(len(M.vars)) if j != i
        ]
        ) # all variables equal to s(x)
    theta = theta.add_constraint(isl.Constraint.inequality_from_aff(xi_isl - s_xi)) # xi - s(xi) <= 0 <-> s(xi) <= xi
    # Note that the constraint xi <= u_xi is already implicit in the domain size!

    s_x_i_to_u_xi = s.set_coordinate_val(isl.dim_type.set, i, isl.Val(u_xi))
    Phi_F = M.Phi(F)
    m_xi = vtp(Phi_F.pw.eval(s_x_i_to_u_xi))
    
    e = interpolate(
        x1=vtp(s_xi),
        y1=vtp(delta),
        x2=u_xi,
        y2=m_xi,
        var=xi_isl,
        space=space
    )
    F__ = Frame.from_pieces(M.ctx, M.vars, [(theta, e)], default_val=Fraction(1))
    if M.Phi(F) <= F__:
        print(f"var: {x_i}; interpolating: x1 {vtp(s_xi)}, y1 {vtp(delta)}, x2 {u_xi}, y2 {m_xi}, SUCCESS.")
        print(f"e: {e}")
        print(f"gen res: {F__}")
        return True, Frame.meet(F_, F__)
    print(f"var: {x_i}; interpolating: x1 {vtp(s_xi)}, y1 {vtp(delta)}, x2 {u_xi}, y2 {m_xi}, FAIL.")
    return False, F_