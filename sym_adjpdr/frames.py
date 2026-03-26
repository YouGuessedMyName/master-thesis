# frames.py

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterator
import islpy as isl
from itertools import product
from sym_adjpdr.barvinok_bindings import *

# LP solver
from scipy.optimize import linprog

type State = dict[str, int]
type Vars = dict[str, tuple[int, int]] # Represents a variable with a name and a domain.

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


# ---------- Frame ----------

@dataclass
class Frame:
    pw: isl.PwAff
    domain: isl.Set
    variables: Vars

    # ---------- canonical constructor ----------
    @staticmethod
    def from_pieces(ctx: isl.Context, variables: Vars, pieces: Iterator[tuple[isl.Set, Fraction | isl.Aff]]):
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

        return Frame(pw, domain, variables)
    
    # ---------- evaluation ----------
    def eval(self, s: State) -> Fraction:
        ctx = self.domain.get_ctx()
        point = isl.Point.zero(self.domain.get_space())

        for i, v in enumerate(self.variables):
            point = point.set_coordinate_val(
                isl.dim_type.set, i, isl.Val.int_from_si(ctx, s[v])
            )

        val = self.pw.eval(point)
        return Fraction(val.to_python()).limit_denominator()

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
        pw = f.pw.min(g.pw)
        return Frame(pw, f.domain, f.variables)

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

    # ---------- FAST dot product ----------
    # @staticmethod
    # def dot(f: "Frame", g: "Frame") -> Fraction:
    #     prod = f.pw * g.pw
    #     prod = prod.intersect_domain(f.domain)

    #     total = Fraction(0)
    #     for sset, aff in prod.get_pieces():
    #         count = sset.count_val().to_python()
    #         val = aff.get_constant_val().to_python()
    #         total += count * val

    #     return total

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