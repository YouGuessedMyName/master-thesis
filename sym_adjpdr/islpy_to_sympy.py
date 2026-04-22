from typing import Iterable

import islpy as isl
import sympy as spy
from fractions import Fraction

def vtp(v: isl.Val) -> Fraction:
    if v.is_int():
        return Fraction(v.to_python())
    return Fraction(v.get_num_si(), v.get_den_val().to_python())

def aff_to_sympy(aff: isl.Aff, sym_vars: Iterable[spy.Symbol]) -> spy.Expr:
    expr = 0

    for i, v in enumerate(sym_vars):
        coeff = aff.get_coefficient_val(isl.dim_type.in_, i)
        expr += spy.Integer(vtp(coeff)) * v

    const = aff.get_constant_val().to_python()
    expr += spy.Integer(const)

    return expr

def set_to_condition(s: isl.Set, vars: Iterable[spy.Symbol]) -> spy.Expr:
    conds = []
    for bset in s.get_basic_sets():
        for c in bset.get_constraints():
            aff = c.get_aff()
            
            lhs = 0
            for i, v in enumerate(vars):
                coeff = aff.get_coefficient_val(isl.dim_type.in_, i)
                lhs += vtp(coeff) * v
            
            lhs += vtp(aff.get_constant_val())
            
            if c.is_equality():
                conds.append(lhs == 0)
            else:
                conds.append(lhs >= 0)
    
    return spy.And(*conds)

def frame_to_sympy(pw: isl.PwAff, vars: Iterable[str]):
    sym_vars = [spy.Symbol(v) for v in vars]
    pieces = []

    for sset, aff in pw.get_pieces():
        expr = aff_to_sympy(aff, sym_vars)
        cond = set_to_condition(sset, sym_vars)
        pieces.append((expr, cond))

    return spy.Piecewise(*pieces)