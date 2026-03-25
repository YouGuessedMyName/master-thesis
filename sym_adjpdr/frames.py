# frame_system_pw.py

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterator
import islpy as isl
from itertools import product

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
    def from_pieces(ctx, variables, pieces):
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
            aff = isl.Aff.zero_on_domain(space)

            val_isl = isl.Val(frac_to_isl(val), clean.get_ctx())
            aff = aff.set_constant_val(val_isl)

            pw_piece = isl.PwAff.from_aff(aff).intersect_domain(clean)
            pw = pw_piece if pw is None else pw.union_max(pw_piece)

        # fill remaining domain with 0
        remaining = domain.subtract(used)
        if not remaining.is_empty():
            zero = isl.PwAff.read_from_str(ctx, f"{{ {remaining} -> 0 }}")
            pw = zero if pw is None else pw.union_max(zero)

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
    @staticmethod
    def dot(f: "Frame", g: "Frame") -> Fraction:
        # multiply → PwQPolynomial
        prod = f.pw * g.pw

        # restrict domain
        prod = prod.intersect_domain(f.domain)

        # sum over domain
        total = prod.sum()

        return Fraction(total.to_python()).limit_denominator()

    # ---------- slow dot ----------
    @staticmethod
    def dot_slow(f: "Frame", g: "Frame") -> Fraction:
        total = Fraction(0)
        for s in enumerate_states(f.variables):
            total += f.eval(s) * g.eval(s)
        return total