from sym_adjpdr.islpy_utils import interpolate
from sym_adjpdr.frames import *
from sym_adjpdr.model import *

oracle = None # Is set externally to the value of the heuristc...

def linear_generalization(F: Frame, s: isl.Point, M: Model) -> tuple[Fraction, Frame]:
    delta = oracle.pw.eval(s)
    z = Frame.ones(isl.DEFAULT_CONTEXT, F.variables)
    # print(f"Generalizing state: {s}, with delta: {delta}")
    for i, (xi, (_, u_xi)) in enumerate(F.variables.items()):
        _, z_ = linear_generalize_variable(F, s, delta, i, xi, u_xi, M)
        z = Frame.meet(z, z_)
    return z.eval(s), z

N = 5

def linear_generalize_state_binary(F: Frame, s: isl.Point, M: Model) -> tuple[Fraction, Frame]:
    for i, (xi, (_, u_xi)) in enumerate(F.variables.items()):
        lb = Fraction(0)
        ub = Fraction(1)
        n = N
        z = Frame.ones(F.pw.get_ctx(), F.variables)
        while n > 0:
            mid = ub - (ub - lb) / 2
            success, z_ = linear_generalize_variable(F, s, isl.Val(frac_to_isl(mid)), i, xi, u_xi, M)
            if success:
                z = Frame.meet(z,z_)
                ub = mid # When succesful, we want to start searching lower.
            else:
                lb = mid
            n -= 1
    return z.eval(s), z

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
    xi_isl = isl.Aff.var_on_domain(space, isl.dim_type.set, i)
    s_xi = s.get_coordinate_val(isl.dim_type.set, i)
    s_x_i_to_u_xi = s.set_coordinate_val(isl.dim_type.set, i, isl.Val(u_xi))
    Phi2_F = M.Phi(M.Phi(F))
    m_xi = vtp(Phi2_F.pw.eval(s_x_i_to_u_xi))
    theta = theta_domain(i, xi_isl, s_xi, s, M)
    
    e = interpolate(
        x1=vtp(s_xi),
        y1=vtp(delta),
        x2=u_xi,
        y2=m_xi,
        var=xi_isl,
        space=space
    )
    z = Frame.from_pieces(M.ctx, M.vars, [(theta, e)], default_val=Fraction(1))
    if M.Phi(M.Phi(F)) <= z:
        return True, z
    return False, Frame.ones(isl.DEFAULT_CONTEXT, F.variables)