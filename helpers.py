from fractions import Fraction
from dataclasses import dataclass
from typing import Callable
from itertools import product

class Frac(Fraction):
    def __str__(self):
        if self == 1:
            return "1"
        elif self == 0:
            return "0"
        return f"{self.numerator}/{self.denominator}"

    def limit_denominator(self, max_denominator = 1000000):
        return Frac(super().limit_denominator(max_denominator))

@dataclass
class MDP:
    S: list[int]
    P: Callable
    av: Callable
    B: list[int]
    PROP: list[Frac]

    def possible_policies(self):
        return [list(t) for t in product(*[self.av(s) for s in self.S])]

def str_list(l):
    res = "["
    for i in range (len(l)):
        res += str(l[i]) 
        if i != len(l) -1:
            res += ", "
    return res + "]"

def str_list2(l):
    res = "["
    for i in range (len(l)):
        if l[i] != 0:
            res += f"{i}: {l[i]}" 
            if i != len(l) -1:
                res += ", "
    return res + "]"

@dataclass
class LowerSet:
    eqs: list[list[int], Frac]

    def __contains__(self, F):
        if len(F) == 0:
            return True
        for (row, r) in self.eqs:
            if sum(row[s] * F[s] for s in range(len(F))) > r:
                #print(F, "is not contained in", self)
                return False
        #print(F, "is contained in", self)
        return True

    def __add__(one, two):
        return LowerSet(dedup(one.eqs + two.eqs))

    def __len__(self):
        return len(self.eqs)

    def __str__(self):
        res = "{ "
        for row, r in self.eqs:
            res += str_list2(row) + " <= " + str(r) + "; " + "\n"
        return res + "}"

def meet(l: list[list[float]]):
    if len(l) == 0:
        return []
    for li in l:
        lowest = [min(x,y) for x, y in zip(li, l[0])]
    return lowest

def dedup(l):
    res = []
    [res.append(x) for x in l if x not in res]
    return res

def vector_leq(x, y):
    if len(x) == 0:
        return True
    assert len(x) == len(y)
    for xi, yi in zip(x,y):
        if xi > yi:
            return False
    return True

def ceil(n):
    return 0 if n == Frac(0) else Frac(1)