"""Functions that are used in the conflict heuristic that involve solution spaces for linear equations."""
import cdd
from helpers import *

def generator_set_cdd(r: V, r0: Frac) -> list[V]:
    """Get the tight generator set using cdd, for the set { v : row*v <= r }."""
    L = len(r)

    constraints_leq_1 = [([1] + [-1 if v == w else 0 for w in range(L)]) for v in range(L)] # All coordinates <= 1
    constraints_geq_0 = [([0] + [1 if v == w else 0 for w in range(L)]) for v in range(L)] # All coordinates >= 0
    constraints_eqs = [[r0] + [-x for x in r]] # Constraints from the equality itself

    mat = cdd.matrix_from_array(constraints_geq_0 + constraints_leq_1 + constraints_eqs)
    mat.rep_type = cdd.RepType.INEQUALITY
    poly = cdd.polyhedron_from_matrix(mat)
    generators_raw = cdd.copy_generators(poly).array

    return dedup([V([Frac(x).limit_denominator(DENOM_LIMIT) for x in d[1:]]) for d in generators_raw])
    # Filter to only include the tight generators.

def generator_set(r: V, r0: Frac) -> list[V]:
    """Get the tight generator set using our own implementation, for the set { v : r*v <= r0}."""

    L = len(r)
    T = [i for i in range(L) if r[i] > 0] # Only non-zeroes
    Z = [i for i in range(L) if r[i] <= 0] # Only zeroes

    generators = []

    for s_star in T:

        others = [s for s in T if s != s_star]

        for assign in product([0,1], repeat=len(others)):
            d = V.zeroes(L)
            sum_fixed = 0 # The sum that you get from the other linear factors already

            for s,val in zip(others,assign):
                d[s] = val
                sum_fixed += r[s]*val

            d_star = (r0 - sum_fixed)/r[s_star] # The maximum amount that you can still assign to s* to be within the cube.
            # print("d_star", d_star)
            # print("d", d)
            if 0 <= d_star <= 1:
                d[s_star] = d_star
                if not d in generators:
                    generators.append(V(d.copy()))
    # expand zero-coefficient coordinates
    expanded = []
    for g in generators:
        for assign in product([0,1], repeat=len(Z)):
            v = g.copy()
            for s,val in zip(Z,assign):
                v[s] = val
            expanded.append(V([Frac(vi).limit_denominator(DENOM_LIMIT) for vi in v]))
    # Add in the cube coordinates.
    cubes = [V([Frac(x) for x in t]) for t in product([0,1], repeat=L)]
    new_cubes = []
    for c in cubes:
        add = True
        for e in expanded:
            if e <= c:
                add = False
        if add:
            new_cubes.append(c)
    return dedup(expanded + new_cubes)

def tight(gens: list[V], r, r0) -> list[V]:
    """Tight generators are generators v, s.t. row*v sum up to r0."""
    epsilon = 1 / DENOM_LIMIT
    return [d for d in gens if sum([di*ri for di,ri in zip(d,r)]) >= r0 - epsilon]

def meet_Zk_slow(r, r0, v, source: str = "own"):
    """Get the meet of Zk = { d : generator_set(r, r0) | v <= d}.
    If Zk is empty, returns a vector of length 0."""
    gen = generator_set if source == "own" else generator_set_cdd
    tight_gens = tight(gen(r,r0), r, r0)
    # print("tight gen", [str(w) for w in tight_gens])
    Zk = list(filter(lambda d : v <= d, tight_gens))
    # print("Zk", [str(w) for w in Zk])
    return meet(Zk)

def meet_Zk_fast(r, r0, v):
    pass