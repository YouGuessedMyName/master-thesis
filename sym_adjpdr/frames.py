# frames.py

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterator
import islpy as isl
from itertools import product
from sym_adjpdr.barvinok_bindings import *
import re

# LP solver
from scipy.optimize import linprog

type State = dict[str, int]
type Vars = dict[str, tuple[int, int]] # Represents a variable with a name and a domain.

TECHNICAL = "TECHNICAL" # Includes the factors that we abstract away from
ABSTRACT = "ABSTRACT"
VERBOSE = "VERBOSE"
FRAME_PRINTING = VERBOSE

# ---------- Helpers ----------

def make_domain(ctx: isl.Context, variables: Vars) -> isl.Set:
    """Create an isl.Set that represents the domains of the variables.
    For example, {"x": (0, 5), "y": (1, 3)} gives { [x, y] : 0 <= x <= 5 and 0 < y <= 3 }.
    """
    constraints = []
    for v, (lb, ub) in variables.items():
        constraints.append(f"{lb} <= {v}")
        constraints.append(f"{v} <= {ub}")
    varlist = ",".join(variables.keys())
    return isl.Set.read_from_str(ctx, f"{{ [{varlist}] : {' and '.join(constraints)} }}")


def enumerate_states(variables: Vars) -> Iterator[State]:
    """Enumerate over all the states of the variables."""
    names = list(variables.keys())
    ranges = [range(lb, ub + 1) for lb, ub in variables.values()]
    for vals in product(*ranges):
        yield dict(zip(names, vals))


def frac_to_isl(fr: Fraction) -> str:
    return f"{fr.numerator}/{fr.denominator}"

from fractions import Fraction
import islpy as isl

def pretty_print_pwaff(pw: isl.PwAff, name: str = "f", factor: int = 1) -> str:
    """
    Pretty print a PwAff as a piecewise function, removing unnecessary
    braces and brackets for singleton domains.
    """
    l = str(pw).strip("{}").split(';')
    def order(s):
        index = len(s)-1 if s[len(s)-1] != " " else len(s)-2
        return int(s[index])
    sorted_l = sorted(l, key=order)
    return "\n".join(sorted_l)

def divide_numbers_in_parentheses(s: str, factor: int) -> str:
    """
    Replace every number inside parentheses in string `s` with number/factor.
    Fractions are displayed if division is not exact.
    """
    def repl(match):
        num_str = match.group(1)
        # Handle integers only (or floats if needed)
        num = int(num_str)
        result = Fraction(num, factor)
        # Return integer if exact, else Fraction
        if result.denominator == 1:
            return f"({result.numerator})"
        else:
            return f"({result})"

    # Match numbers inside parentheses: e.g., (123)
    pattern = r"\((\d+)\)"
    return re.sub(pattern, repl, s)


# ---------- Frame ----------

@dataclass
class Frame:
    pw: isl.PwAff
    domain: isl.Set
    variables: Vars
    factor: int = 1

    # ---------- canonical constructor ----------
    @staticmethod
    def from_pieces(ctx: isl.Context, variables: Vars, pieces: Iterator[tuple[isl.Set, Fraction | isl.Aff]], 
                    factor: int = 1, default_val: Fraction = Fraction(0)):
        domain = make_domain(ctx, variables)

        used = isl.Set.empty(domain.get_space())
        pw = None

        for region, val in pieces:
            clean = region.subtract(used).intersect(domain) 
            # Clean represents the region that was not taken yet by any other region, to ensure no overlap between regions.
            if clean.is_empty():
                continue

            used = used.union(clean)
            space = clean.get_space()

            if type(val) == Fraction:
                aff = isl.Aff.zero_on_domain(space)
                val_isl = isl.Val(frac_to_isl(val), clean.get_ctx())
                aff = aff.set_constant_val(val_isl)
            else:
                aff = val

            pw_piece = isl.PwAff.from_aff(aff).intersect_domain(clean)
            pw = pw_piece if pw is None else pw.union_max(pw_piece)

        # fill remaining domain with 0
        remaining = domain.subtract(used)
        if not remaining.is_empty():
            space = remaining.get_space()
            isl_default_val = isl.Val(frac_to_isl(default_val))
            aff = isl.Aff.val_on_domain(space, isl_default_val)
            pw_piece = isl.PwAff.from_aff(aff).intersect_domain(remaining)
            
            pw = pw_piece if pw is None else pw.union_max(pw_piece)

        return Frame(pw, domain, variables, factor)
    
    @staticmethod
    def zero(ctx: isl.Context, variables: Vars, factor: int = 1):
        return Frame.from_pieces(ctx, variables, [], factor)

    # ---------- evaluation ----------
    def eval(self, s: State) -> Fraction:
        ctx = self.domain.get_ctx()
        point = isl.Point.zero(self.domain.get_space())

        for i, v in enumerate(self.variables):
            point = point.set_coordinate_val(
                isl.dim_type.set, i, isl.Val.int_from_si(ctx, s[v])
            )

        val = self.pw.eval(point)
        if val.is_int():
            return Fraction(val.to_python() / self.factor).limit_denominator()
        else:
            return (Fraction(val.to_str()) / self.factor).limit_denominator()

    # ---------- partial order ----------
    def __le__(self, other: "Frame") -> bool:
        return self.pw.le_set(other.pw).is_equal(self.domain)

    def le_slow(self, other: "Frame") -> bool:
        for s in enumerate_states(self.variables):
            if self.eval(s) > other.eval(s):
                return False
        return True

    # ---------- meet ----------
    @staticmethod
    def meet(f: "Frame", g: "Frame") -> "Frame":
        assert f.factor == g.factor
        pw = f.pw.min(g.pw)
        return Frame(pw, f.domain, f.variables, f.factor)

    @staticmethod
    def meet_slow(f: "Frame", g: "Frame") -> "Frame":
        ctx = f.domain.get_ctx()
        pieces = []
        for s in enumerate_states(f.variables):
            val = min(f.eval(s), g.eval(s))
            point = isl.Set.read_from_str(
                ctx,
                "{ [" + ",".join(str(s[v]) for v in f.variables) + "] }"
            )
            pieces.append((point, val))
        return Frame.from_pieces(ctx, f.variables, pieces)

    @staticmethod
    def dot(f: "Frame", g: "Frame") -> Fraction:
        # piecewise product
        prod = f.pw * g.pw
        prod = isl.PwQPolynomial.from_pw_aff(prod.intersect_domain(f.domain))
        return barvinok_sum_pwqp(prod)

    # ---------- slow dot ----------
    @staticmethod
    def dot_slow(f: "Frame", g: "Frame") -> Fraction:
        total = Fraction(0)
        for s in enumerate_states(f.variables):
            total += f.eval(s) * g.eval(s)
        return total
    
    def __str__(self) -> str:
        if FRAME_PRINTING == TECHNICAL:
            return "[" + str(self.factor) + "]" + str(self.pw)
        elif FRAME_PRINTING == ABSTRACT:
            return (divide_numbers_in_parentheses(str(self.pw), self.factor))
        else:
            return pretty_print_pwaff(self.pw, "f", self.factor)
        
    def __sub__(self, other):
        return Frame(self.pw - other.pw, self.domain, self.variables, self.factor)
    
    def sum(self):
        return barvinok_sum_pwqp(isl.PwQPolynomial.from_pw_aff(self.pw).intersect_domain(self.domain))
    
    def __setitem__(self, key: dict[str, int], value: Fraction):        
        set_str = "{ [" + ",".join(key) + "] : "  + "and".join(f"{k}={v}" for k,v in key.items()) + " }"
        sset = isl.Set(set_str)
        pw_inter = self.pw.intersect_domain(sset.complement())
        point_aff = isl.Aff.val_on_domain(sset.space, isl.Val(frac_to_isl(value))).intersect_domain(sset)
        self.pw = pw_inter.union_add(point_aff)
    
    def __eq__(self, value):
        return self.pw.is_equal(value.pw)
    
    def zero_region(self, region: dict[str, tuple[int, int]] | isl.Set):
        if isinstance(region, dict):
            region: isl.Set = make_domain(self.domain.get_ctx(), region)
        aff = isl.Aff.zero_on_domain(region.get_space()).intersect_domain(region)
        zeroed = self.pw.union_min(aff)
        return Frame(zeroed, self.domain, self.variables, self.factor)
    
    def sum_over_region(self, region: dict[str, tuple[int, int]] | isl.Set):
        if isinstance(region, dict):
            region: isl.Set = make_domain(self.domain.get_ctx(), region)
        regionalized = isl.PwQPolynomial.from_pw_aff(self.pw.intersect_domain(region))
        return barvinok_sum_pwqp(regionalized)

# ---------- FrameSet ----------

@dataclass
class FrameSet:
    eqs: list[tuple[Frame, Fraction]]  # list of (Frame r, Fraction r0)
    variables: Vars

    # ---------- membership ----------
    def __contains__(self, F: Frame) -> bool:
        for (r, r0) in self.eqs:
            total = Frame.dot(r, F)
            if total > r0:
                return False
        return True

    # ---------- slow membership ----------
    def contains_slow(self, F: Frame) -> bool:
        for (r, r0) in self.eqs:
            total = Frame.dot_slow(r, F)
            if total > r0:
                return False
        return True

    # ---------- subset inclusion ----------
    def __le__(self, other: "FrameSet") -> bool:
        # build region partition
        regions = []
        for (r, _) in self.eqs:
            for (R, _) in r.pw.get_pieces():
                regions.append(R)

        # counts
        counts = [r.count_val().to_python() for r in regions]

        n = len(regions)

        for (q, q0) in other.eqs:
            c = []
            for R in regions:
                val = 0
                for (Qreg, qv) in q.pw.get_pieces():
                    if not R.intersect(Qreg).is_empty():
                        val = qv.get_constant_val().to_python()
                        break
                c.append(val)

            A = []
            b = []
            for (r, r0) in self.eqs:
                row = []
                for R in regions:
                    val = 0
                    for (Rr, rv) in r.pw.get_pieces():
                        if not R.intersect(Rr).is_empty():
                            val = rv.get_constant_val().to_python()
                            break
                    row.append(val)
                A.append(row)
                b.append(float(r0))

            bounds = [(0, 1)] * n

            res = linprog(
                c=[-ci for ci in c],
                A_ub=A,
                b_ub=b,
                bounds=bounds,
                method="highs"
            )

            if res.success and -res.fun > float(q0):
                return False

        return True