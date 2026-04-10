from fractions import Fraction
from dataclasses import dataclass
from typing import Callable, Collection
from itertools import product
from numpy import argmax as npargmax
from z3 import Real, Solver, Sum, sat
import random

# "frac" for fractions and "float" for floats (this only affects printing, we use Fracs for everything otherwise.)
FRAC = "FRAC"
FLOAT = "FLOAT"
NUMBERS = FRAC

SPARSE = "SPARSE"
DENSE = "DENSE"
VECTOR_PRINTING = DENSE

DENOM_LIMIT = 1e100
ROUNDING = 20

def dedup(l):
    res = []
    [res.append(x) for x in l if x not in res]
    return res

def ceil(n):
    return Frac(0) if n == Frac(0) else Frac(1)

def argmax(results, args):
    #print("args", args)
    return args[npargmax(results)]

def apply(f, n, arg):
    """Apply f n times to arg."""
    return arg if n <= 0 else f(apply(f, n-1, arg)) 

def apply2(f, n, arg, M):
    """Apply a function n times to these two arguments."""
    return arg if n <= 0 else f(apply2(f, n-1, arg, M), M)

class Frac(Fraction):
    """Custom fraction type that supports nice printing."""

    def __new__(cls, *args):
        if len(args) == 2:
            args = (int(args[0]), int(args[1]))
        return super().__new__(cls, *args)

    def __str__(self):
        if NUMBERS == FRAC:
            if self.is_integer():
                return str(int(self))
            return f"{self.numerator}/{self.denominator}"
        else:
            return str(round(float(self), ROUNDING))

    def limit_denominator(self, max_denominator = 1000000):
        return self.fix(Frac(super().limit_denominator(max_denominator)))

    @classmethod
    def fix(cls, fraction: Fraction):
        return cls(int(fraction.numerator), int(fraction.denominator))
    
    @staticmethod
    def sum(l: Collection["Frac"]):
        res = Frac(0)
        for li in l:
            res += li
        return res.limit_denominator(DENOM_LIMIT)

class V(list):
    """Custom Vector datatype. Supports the desired functionality of <=, and nice printing."""

    def __add__(self, value):
        return V(super().__add__(value))

    def __le__(x, y):
        if len(x) == 0:
            return True
        assert len(x) == len(y)
        for xi, yi in zip(x,y):
            if xi > yi:
                return False
        return True
    
    def __str_dense(l):
        res = "["
        for i in range (len(l)):
            res += str(l[i]) 
            if i != len(l) -1:
                res += ", "
        return res + "]"

    def __str_sparse(l):
        res = "["
        for i in range (len(l)):
            if l[i] != 0:
                res += f"{i}: {l[i]}" 
                if i != len(l) -1:
                    res += ", "
        return res + "]"

    def __str__(self):
        if VECTOR_PRINTING == DENSE:
            return self.__str_dense()
        return self.__str_sparse()
    
    @classmethod
    def empty(cls):
        return cls([])
    
    @classmethod
    def zeroes(cls, n):
        return cls([Frac(0)]*n)
    
    @classmethod
    def ones(cls, n):
        return cls([Frac(1)]*n)
    
    @classmethod
    def random(cls, n):
        return cls([Frac(random.uniform(0,1)).limit_denominator(DENOM_LIMIT)]*n)
    
def downarrow(p: V) -> V:
    for i, entry in enumerate(p):
        if i != 0:
            assert entry == 1
    return LowerSet([(
        V([Frac(1)] + [0 for _ in range(len(p)-1)]), 
            Frac(p[0]).limit_denominator(DENOM_LIMIT))])

def downarrow1(p: V) -> V:
    for i, entry in enumerate(p):
        if i != 0:
            assert entry == 1
    return LowerSet([(
        V([Frac(1/p[0]).limit_denominator(DENOM_LIMIT)] + [0 for _ in range(len(p)-1)]), 
            Frac(1))])

def meet(l: Collection[V[Frac]]) -> V:
    """Get the meet of the list of vectors. If the collection is empty, returns a vector of length 0."""
    if len(l) == 0:
        return V([])
    lowest = l[0]
    for li in l:
        lowest = [Frac(min(x,y)).limit_denominator(DENOM_LIMIT) for x, y in zip(li, lowest)]
    return V(lowest)

class LowerSet:
    eqs: list[tuple[V, Frac]]

    def __init__(self, eqs: tuple[list[V|list], Frac|float]):
        self.eqs = [(V([Frac(ri) for ri in row]), Frac(r)) for row,r in eqs]

    def approx_contains(self, F: V, epsilon: float):
        if len(F) == 0:
            return True
        for (row, r) in self.eqs:
            if sum(row[s] * F[s] for s in range(len(F))) > r + abs(epsilon):
                return False
        return True

    def __contains__(self, F: V):
        if len(F) == 0:
            return True
        for (r, r0) in self.eqs:
            if sum([Frac.fix(r[s]) * F[s] for s in range(len(F))]) > r0:
                return False
        return True

    def __add__(one, two):
        if one == []:
            return two
        if two == []:
            return one
        return LowerSet(dedup(one.eqs + two.eqs))

    def __len__(self):
        return len(self.eqs)

    def __str__(self):
        if len(self.eqs) == 0:
            return "{ v : True }" 
        if self.is_empty():
            return "{ }"
        res = "{ v: "
        for row, r in self.eqs:
            res += str(row) + " * v <= " + str(r) + "; "
        return res + "}"
    
    def __le__(self, other):
        """Checking if a lower set is contained in another lower set is accomplished 
        by asking the SMT solver to come up with a point that is inside the one but not the other."""
        vars_ = [Real(f"x_{i}") for i in range(len(self.eqs[0][0]))]
        s = Solver()
        for x in vars_:
            s.add(x >= 0)
            s.add(x <= 1)
        for i in range(len(self)):
            for j in range(len(other)):
                srow, sr = self.eqs[i]
                otrow, otr = other.eqs[j]
                
                s.add(Sum([srow[i] * vars_[i] for i in range(len(vars_)) if srow[i] != 0]) <= sr) # A point contained in self
                s.add(Sum([otrow[i] * vars_[i] for i in range(len(vars_)) if otrow[i] != 0]) > otr) # That is *not* contained in other
        if s.check() == sat:
            #print("Not contained, take the point:", s.model())
            return False
        return True
    
    def is_empty(self):
        for r,r0 in self.eqs:
            if r0 < 0:
                #print("empty",r,r0)
                return True
        return False
    
    @classmethod
    def empty(cls, q):
        return cls([([0]*q, -1)])

@dataclass
class MDP:
    S: list[int]
    P: Callable
    av: Callable
    B: list[int]
    PROP: list[Frac]
    EXPECTED_RESULT: float

    def has_multiple_policies(self) -> bool:
        return any([len(self.av(s)) > 1 for s in self.S])

    def possible_policies(self) -> list[list]:
        """Enumerate all possible policies on this MDP."""
        return [list(t) for t in product(*[self.av(s) for s in self.S])]

    def Phi(M, F: V) -> V:
        if len(F) == 0:
            return V.empty()
        return V([
            Frac(1) if s in M.B else
                Frac.fix(Frac(max([(sum(M.P(s,a,s_) * F[s_] for s_ in M.S)) 
                    for a in M.av(s)])).limit_denominator(DENOM_LIMIT))
            for s in M.S
        ])
    
    def PhiPolicy(M, policy: list[str], F: V) -> V:
        return V([
            Frac(1) if s in M.B else
                Frac(sum(M.P(s,policy[s],s_) * F[s_] for s_ in M.S)).limit_denominator(DENOM_LIMIT)
            for s in M.S
        ])

    def PhiPolicyArgMax(M, F: V) -> list:
        """Return the policy that maximizes Phi for F."""
        if len(F) == 0:
            return []
        return [
                argmax([Frac(sum(M.P(s,a,s_) * F[s_] for s_ in M.S))
                    for a in M.av(s)], M.av(s))
            for s in M.S
        ]

    def Theta(M, policy: list, F: V) -> V:
        """Apply the next step in the MDP for this policy (Theta)"""
        # print("NEXT")
        # print("F", str_list(F))
        # print("pol", policy)
        return V([
            Frac.fix(Frac(sum(M.P(s_,policy[s_],s) * F[s_] for s_ in M.S)).limit_denominator(DENOM_LIMIT))
            for s in M.S
        ])

    def PsiPolicyEq(M, policy: list[str], row: V, r: Frac) -> LowerSet:
        """Get Psi for one linear equation and policy."""
        new_row = V([Frac.fix(Frac(ri)) for ri in row])
        deduct = Frac(0)
        for s in M.B:
            #print(s)
            deduct += new_row[s]
            new_row[s] = Frac(0)
        next_step = M.Theta(policy, new_row)
        #print("next step", str_list(next_step))
        # Now account for Phi setting bad states to 1
        
        # print("r", r, "deduct", deduct)
        return next_step, Frac.fix(Frac(r - deduct).limit_denominator(DENOM_LIMIT))

    def PsiPolicy(M, policy: list, G: LowerSet) -> LowerSet:
        """Get Psi for this policy."""
        return LowerSet([M.PsiPolicyEq(policy, row, r) for (row, r) in G.eqs])

    def Psi(M, G: LowerSet) -> LowerSet:
        res = LowerSet([])
        for policy in M.possible_policies():
            psipol = M.PsiPolicy(policy, G)
            if psipol == []:
                return []
            res += psipol
            # print("plc", policy)
            # print("Psi", PsiPolicy(policy, G, M))
            # print(res)
        if len(res.eqs) == 0:
            return []
        return res
