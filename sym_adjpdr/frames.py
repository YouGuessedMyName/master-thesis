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
FRAME_PRINTING = TECHNICAL

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
    pieces = []

    # iterate over pieces
    for piece in pw.get_pieces():
        dom = piece[0]  # isl.Set
        aff = piece[1]  # isl.Aff

        # Convert Aff to string with fractions for constants
        terms = []
        for i in range(aff.dim(isl.dim_type.in_)):
            coeff = aff.get_coefficient_val(isl.dim_type.in_, i)
            if coeff is None:
                continue
            try:
                coeff_val = (Fraction(coeff.num, coeff.den) / factor).limit_denominator()
            except:
                coeff_val = Fraction(coeff.to_python() / factor).limit_denominator()
            var_name = pw.get_space().get_dim_name(isl.dim_type.in_, i)
            if coeff_val == 1:
                terms.append(f"{var_name}")
            elif coeff_val == -1:
                terms.append(f"-{var_name}")
            elif coeff_val != 0:
                terms.append(f"{coeff_val}*{var_name}")

        # constant term
        c = aff.get_constant_val()
        if c is not None:
            try:
                c_val = (Fraction(c.num, c.den)/factor).limit_denominator()
            except:
                c_val = Fraction(c.to_python() / factor).limit_denominator()
            if c_val != 0 or not terms:
                terms.append(f"{c_val}")

        aff_str = " + ".join(terms) if terms else "0"

        # domain string
        dom_str = str(dom)
        # Clean domain string: remove braces and brackets if singleton or simple
        if dom.is_empty():
            dom_str = "empty"
        else:
            # If it has ": " it's a normal constraint, take the right-hand side
            if ": " in dom_str:
                dom_str = dom_str.split(": ", 1)[1]
            # Remove surrounding { [ ] } if they exist
            dom_str = dom_str.strip("{}[] ").replace("[", "").replace("]", "")
            # Remove extra spaces around equals
            dom_str = dom_str.replace(" = ", "=")

        pieces.append((aff_str, dom_str))

    # Build the final piecewise string
    s = f"{name}(x) = {{\n"
    for aff_str, dom_str in pieces:
        s += f"    {aff_str}   if {dom_str}\n"
    s += "}"
    return s

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
    def from_pieces(ctx: isl.Context, variables: Vars, pieces: Iterator[tuple[isl.Set, Fraction | isl.Aff]], factor: int = 1):
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
            aff = isl.Aff.zero_on_domain(space)
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
        return Fraction(val.to_python() / self.factor).limit_denominator()

    # ---------- partial order ----------
    def __le__(self, other: "Frame") -> bool:
        diff = (self.pw - other.pw).intersect_domain(self.domain)
        max_val = diff.max_val()
        return max_val.is_neg() or max_val.is_zero()

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