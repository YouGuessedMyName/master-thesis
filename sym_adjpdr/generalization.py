from sym_adjpdr.frames import *
from sym_adjpdr.model import *
import sympy as sp
from sym_adjpdr.islpy_to_sympy import *
from sym_adjpdr.sympy_to_z3 import *

def iterate_isl_set(S: isl.Set) -> Iterator[isl.Point]:
    while not S.is_empty():
        p = S.sample_point()
        yield p
        S = S.subtract(isl.Set.from_point(p))

def non_zero_states(G: FrameSet) -> isl.Set:
    """Return a isl.Set containing exactly the states/points in the FrameSet where the coefficient is non-zero."""
    assert len(G.eqs) == 1
    pw = G.eqs[0][0].pw
    res = isl.Set.empty(pw.get_domain_space())
    for guard, aff in pw.get_pieces():
        gt = aff.gt_set(isl.Aff.zero_on_domain(guard.space)).intersect(guard)
        res = res.union(gt)
    return res.coalesce()

    # Idea .sample_point()!!

def val_to_aff(v: isl.Val, space: isl.Space) -> isl.Aff:
    return isl.Aff.zero_on_domain(space).set_constant_val(v)

def interpolate(x1: int, y1: int, x2: int, y2: int, var: isl.Aff, space: isl.Space) -> isl.Aff:
    if x2 - x1 == 0:
        a = Fraction(0,1)
    else:
        a = Fraction(y2 - y1, x2 - x1)
    b = y1 - a * x1
    a_aff = val_to_aff(isl.Val(frac_to_isl(a)), space)
    e = a_aff * var + val_to_aff(isl.Val(frac_to_isl(b)), space)
    return e

def linear_generalization(F: Frame, p: isl.Point, delta: isl.Val, M: Model) -> Frame:
    assert M.Phi(F).pw.eval(p) <= delta

    F_ = Frame.from_pieces(M.ctx, M.vars, 
        [(isl.Set.from_point(p), delta)], default_val=Fraction(1)) # No need for infty, 1 suffices since the range is [0,1]

    for i, (x, (_lb, ub)) in enumerate(M.vars.items()):
        # TODO we are repeating work here... In the future have the vars on domain available from M and cache!
        sp = M.domain.space
        x_isl = isl.Aff.var_on_domain(sp, isl.dim_type.set, i)
        cur_val = p.get_coordinate_val(isl.dim_type.set, i)
        theta = M.domain.copy().add_constraints(
            [isl.Constraint.equality_from_aff(
                    isl.Aff.var_on_domain(sp, isl.dim_type.set, j) 
                - 
                    p.get_coordinate_val(isl.dim_type.set, j))
                for j in range(len(M.vars)) if j != i
            ]
            )
        theta = theta.add_constraint(isl.Constraint.inequality_from_aff(x_isl - cur_val))

        sigma_subst = p.set_coordinate_val(isl.dim_type.set, i, isl.Val(ub))
        Phi_F = M.Phi(F)
        Phi_F_eval = Phi_F.pw.eval(sigma_subst).to_python()
        e = interpolate(
            x1=vtp(cur_val),
            y1=vtp(delta),
            x2=ub,
            y2=Phi_F.pw.eval(sigma_subst).to_python(),
            var=x_isl,
            space=sp
        )
        F__ = Frame.from_pieces(M.ctx, M.vars, [(theta, e)], default_val=Fraction(1))
        if M.Phi(F) <= F__:
            F_ = Frame.meet(F_, F__)

    return F_

def isl_point_to_sym_state(p: isl.Point, sym_vars: list[sp.Symbol]) -> dict[sp.Symbol, Fraction]:
    return {x : vtp(p.get_coordinate_val(i)) for i, x in enumerate(sym_vars)}

def polynomial_generalization(F: Frame, p: isl.Point, delta: isl.Val, n: int, M: Model) -> sp.Piecewise:
    # Do polynomial generalization. Outputs a simpy piecewise.
    assert M.Phi(F).pw.eval(p) <= delta

    PHI_F_SP = frame_to_sympy(M.Phi(F))
    PHI_F_Z3 = sympy_to_z3(PHI_F_SP)

    F1 = Frame.from_pieces(M.ctx, M.vars, 
        [(isl.Set.from_point(p), delta)], default_val=Fraction(1)) # No need for infty, 1 suffices since the range is [0,1]
    
    sym_vars = [sp.symbol(x) for x in M.vars]
    z3_vars = [z3.Real(x) for x in M.vars]
    F1_sp = aff_to_sympy(F1.pw, sym_vars)

    for k, (x, (_lb, ub)) in enumerate(M.vars.items()):
        # TODO we are repeating work here... In the future have the vars on domain available from M and cache!
        space = M.domain.space
        x_spy = sp.Symbol(x)
        x_isl = isl.Aff.var_on_domain(space, isl.dim_type.set, k)
        cur_val = p.get_coordinate_val(isl.dim_type.set, k)
        theta: isl.Set = M.domain.copy().add_constraints(
            [isl.Constraint.equality_from_aff(
                    isl.Aff.var_on_domain(space, isl.dim_type.set, j) 
                - 
                    p.get_coordinate_val(isl.dim_type.set, j))
                for j in range(len(M.vars)) if j != k
            ]
            )
        theta = theta.add_constraint(isl.Constraint.inequality_from_aff(x_isl - cur_val))
        theta_sp = set_to_condition(theta, sym_vars)

        sigma_subst = p.set_coordinate_val(isl.dim_type.set, k, isl.Val(ub))
        Phi_F = M.Phi(F)
        Phi_F_eval = vtp(Phi_F.pw.eval(sigma_subst))
        points = [(vtp(cur_val), vtp(delta)), (ub, Phi_F_eval)]

        i = 0
        while True:
            e = sp.interpolate(points, x_spy)
            # TODO try to use ISL instead! Saves a bunch of pain probably.
            F2_sp = sp.Piecewise((e, theta_sp), (1, True))
            F2_z3 = sympy_to_z3(F2_sp)
            
            if not check_in_bounds(F2_z3, z3_vars, 0, 1): # Not a Frame
                break
            sigma2 = find_greater(PHI_F_Z3, F2_z3)
            sigma2_spy = {var: val for var, val in zip(sym_vars, sigma2.values())}
            if sigma2 is not None: # Counterexample
                points.append((sigma2[x], PHI_F_SP.subs(sigma2_spy)))
            else: # We can generalize!
                F1_sp = sp.Min(F1_sp, F2_sp)
            
            if i > n: # The do-while loop
                break

    return F1_sp

def sympy_piecewise_to_pw_aff_approximation():
    pass
