from sym_adjpdr.frames import *
from sym_adjpdr.islpy_utils import find_partitions_list, interpolate, pwqp_to_pwaff_overapproximation
from sym_adjpdr.model import *
import sympy as sp
from sym_adjpdr.islpy_to_sympy import *
from sym_adjpdr.sympy_to_islpy import *
from sym_adjpdr.sympy_to_z3 import *

N = 5 # How many counterexamples to try during polynomial generalization.

def hybrid_polynomial_generalization(F: Frame, p: isl.Point, delta: isl.Val, M: Model) -> Frame:
    global PARTITIONS
    if PARTITIONS is None:
        PARTITIONS = find_partitions_list(M.vars)
        [print(p) for p in PARTITIONS]
    # Do polynomial generalization. Outputs a simpy piecewise.
    assert eval_safe(M.Phi(F), p) <= delta

    sym_vars = [sp.Symbol(x) for x in M.vars]
    z3_vars = [z3.Int(x) for x in M.vars]
    sympy_to_z3_var_map = dict(zip(sym_vars, z3_vars))
    str_to_z3_var_map = dict(zip(M.vars, z3_vars))

    F1 = Frame.from_pieces(M.ctx, M.vars, 
        [(isl.Set.from_point(p), delta)], default_val=Fraction(1)) # No need for infty, 1 suffices since the range is [0,1]
    F1_aff = F1.pw
    
    Phi_F = M.Phi(F)
    Phi_F_sp = frame_to_sympy(Phi_F.pw, sym_vars)
    assert not Phi_F_sp.has(sp.nan)
    Phi_F_z3 = sympy_to_z3(Phi_F_sp, sympy_to_z3_var_map)
    
    F1_poly = isl.PwQPolynomial.from_pw_aff(F1.pw)

    
    F1_sp = frame_to_sympy(F1.pw, sym_vars)

    for k, (x, (_lb, ub)) in enumerate(M.vars.items()):
        # TODO we are repeating work here... In the future have the vars on domain available from M and cache!
        space = M.domain.space
        x_sp = sp.Symbol(x)
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
        
        Phi_F_eval = vtp(eval_safe(Phi_F.pw, sigma_subst))
        points = [(vtp(cur_val), vtp(delta)), (ub, Phi_F_eval)]

        i = 0
        while True:
            e_sp = sp.interpolate(points, x_sp)
            if e_sp.has(sp.zoo):
                break
            #e_sp = e_sp.subs(list(e_sp.free_symbols), sym_vars)
            e = sympy_poly_to_isl_pwqp_multi(e_sp, sym_vars)
            pw_not_theta_one = isl.PwQPolynomial.from_pw_aff(to_indicator_function(theta.complement(), M.domain))
            F2_poly = e.intersect_domain(theta).add(pw_not_theta_one).coalesce()
            F2_aff = pwqp_to_pwaff_overapproximation(F2_poly, PARTITIONS, space, k)
            F2_sp = sp.Piecewise(
                (e_sp, theta_sp),
                (1, True)
            )
            F2_z3 = sympy_to_z3(F2_sp, sympy_to_z3_var_map)
            
            if F2_poly.min() < 0 or F2_poly.max() > 1: # Not a Frame
                break

            sigma2 = find_greater(Phi_F_z3, F2_z3, str_to_z3_var_map)
            if sigma2 is not None: # Counterexample
                sigma2_sp = dict(zip(sym_vars, sigma2.values()))
                #sigma2_sp_floats = {k: sp.Rational(v) for k,v in sigma2_sp.items()}
                upper = Phi_F_sp.subs(sigma2_sp)
                if upper != sp.nan:
                    points.append((sigma2[x], upper))
            else: # We can generalize!
                F1_aff = F1_aff.union_min(F2_aff)
                break
            
            if i > N: # The do-while loop
                break
    return Frame(F1_aff.union_max(Phi_F.pw), F.domain, F.variables)
