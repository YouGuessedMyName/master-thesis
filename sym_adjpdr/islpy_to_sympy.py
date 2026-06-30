from typing import Iterable

import islpy as isl
import sympy as sp
from fractions import Fraction

def vtp(v: isl.Val) -> Fraction:
    if v.is_int():
        return Fraction(v.to_python())
    num, den = str(v).split("/")
    return Fraction(int(num), int(den))

def aff_to_sympy(aff: isl.Aff, sym_vars: Iterable[sp.Symbol]) -> sp.Expr:
    expr = 0

    for i, v in enumerate(sym_vars):
        coeff = aff.get_coefficient_val(isl.dim_type.in_, i)
        expr += sp.Integer(vtp(coeff)) * v

    const = vtp(aff.get_constant_val())
    expr += sp.Rational(const)

    return expr

def set_to_condition(s: isl.Set, sym_vars: Iterable[sp.Symbol]) -> sp.Expr:
    conds = []
    for bset in s.get_basic_sets():
        bset_conds = []
        for c in bset.get_constraints():
            aff = c.get_aff()
            
            lhs = 0
            for i, v in enumerate(sym_vars):
                coeff = aff.get_coefficient_val(isl.dim_type.in_, i)
                lhs += vtp(coeff) * v
            
            lhs += vtp(aff.get_constant_val())
            
            if c.is_equality():
                bset_conds.append(sp.Eq(lhs, 0))
            else:
                bset_conds.append(sp.GreaterThan(lhs, 0))
        conds.append(sp.And(*bset_conds))
    return sp.Or(*conds)

def frame_to_sympy(pw: isl.PwAff, sym_vars: Iterable[sp.Symbol]):
    pieces = []

    for sset, aff in pw.get_pieces():
        expr = aff_to_sympy(aff, sym_vars)
        cond = set_to_condition(sset.coalesce(), sym_vars)
        pieces.append((expr, cond))

    return sp.Piecewise(*pieces)