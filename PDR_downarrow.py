import cdd
import numpy as np
from typing import Callable
from dataclasses import dataclass
from examples.example_23 import *
from math import isclose
from copy import deepcopy

@dataclass
class LowerSet:
    eqs: list[list[int], float]

    def __contains__(self, F):
        if len(F) == 0:
            return True
        for (row, r) in self.eqs:
            if sum(row[s] * F[s] for s in S) > r:
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
            res += str(row) + " <= " + str(r) + "; "
        return res + "}"

def meet(l: list[list[float]]):
    if len(l) == 0:
        return []
    for li in l:
        lowest = [min(x,y) for x, y in zip(li, l[0])]
    return lowest


def PhiPolicy(policy: Callable, F: list[float]):
    return [
        1 if s in B else
            sum(P(s,policy(s),s_) * F[s_] for s_ in S)
        for s in S
    ]

def Phi(F: list[float]):
    if len(F) == 0:
        return []
    return [
        1 if s in B else
            max([round(sum(P(s,a,s_) * F[s_] for s_ in S), 4) 
                for a in available_actions(s)])
        for s in S
    ]

def NextStepPolicy(policy: Callable, F: list[float]):
    return [
        sum(P(s_,policy(s_),s) * F[s_] for s_ in S)
        for s in S
    ]

def PhiPolicy(policy: Callable, F: list[float]):
    return [
        1 if s in B else
            sum(P(s,policy(s),s_) * F[s_] for s_ in S)
        for s in S
    ]

def PsiPolicyEq(policy: Callable, row, r):
    next_step = NextStepPolicy(policy, row)
    deduct = 0
    for s in B:
        deduct += row[s]
        next_step[s] -= deduct
    return next_step, r - deduct
        

def PsiPolicy(policy: Callable, G: LowerSet):
    res = LowerSet([PsiPolicyEq(policy, row, r) for (row, r) in G.eqs])
    for (_, r) in res.eqs:
        if r < 0:
            return []
    return res

def dedup(l):
    res = []
    [res.append(x) for x in l if x not in res]
    return res

def downarrow(p):
    for i, entry in enumerate(p):
        if i == 0:
            assert entry != 0
        if i != 0:
            assert entry == 1
    return LowerSet([([1] + [0 for _ in range(len(p)-1)], p[0])])

def Psi(G: LowerSet):
    res = LowerSet([])
    for policy in possible_policies():
        res += PsiPolicy(policy, G)
    return res

def candidate_heuristic(p):
    return downarrow(p)

def decide_heuristic(F_k_minus_1, Gk):
    for number, policy in enumerate(possible_policies()):
        if PhiPolicy(policy, F_k_minus_1) not in Gk:
            print("policy no.", number)
            return PsiPolicy(policy, Gk)
    return set()

def vector_leq(x, y):
    if len(x) == 0:
        return True
    assert len(x) == len(y)
    for xi, yi in zip(x,y):
        if xi > yi:
            return False
    return True

def generate_zk(F_k_minus_1, Gk):
    # print(f"Fk-1: {F_k_minus_1}")
    # print(f"Gk: {Gk}")
    L = len(F_k_minus_1)
    assert len(Gk) == 1
    row, r = Gk.eqs[0]

    constraints_geq_0 = [([0] + [1 if v == w else 0 for w in range(L)]) for v in range(L) if row[v] == 0] # ???
    #constraints_geq_0 = [([0] + [1 if v == w else 0 for w in range(L)]) for v in range(L)] # ???
    constraints_leq_1 = [([1] + [-1 if v == w else 0 for w in range(L)]) for v in range(L)]
    constraints_eqs = [[r] + [-x for x in row]]
    mat = cdd.matrix_from_array(constraints_geq_0 + constraints_leq_1 + constraints_eqs)
    mat.rep_type = cdd.RepType.INEQUALITY
    poly = cdd.polyhedron_from_matrix(mat)
    generators_raw = cdd.copy_generators(poly).array
    #print(f"Gens raw: {generators_raw}")
    generators = [[round(x,4) for x in d[1:]] for d in generators_raw]
    #print(f"Gens: {generators}")
    #print(f"Phi(F_k_minus) {Phi(F_k_minus_1)}")
    Zk = [d for d in generators if vector_leq(Phi(F_k_minus_1), d)]
    return Zk

def conflict_heuristic_zb(F_k_minus_1, Gk):
    L = len(F_k_minus_1)
    assert len(Gk) == 1
    row, r = Gk.eqs[0]
    #print("==================")
    Zk = generate_zk(F_k_minus_1, Gk)
    print(f"Zk: {Zk}")
    meetZk = meet(Zk)
    print(f"meet of Zk: {meetZk}")
    phi_applied = Phi(F_k_minus_1)
    #print("PHI:", phi_applied)
    res = []
    for s in S:
        if row[s] != 0 and len(Zk) != 0:
            res.append(meetZk[s])
        else:
            res.append(phi_applied[s])
    #print(f"Z: {res}")
    #print("==================")
    return [round(x, 4) for x in res]

def ceil(n):
    return 0 if n == 0 else 1

def conflict_heuristic_01(F_k_minus_1, Gk):
    assert len(Gk) == 1
    row, r = Gk.eqs[0]
    Zk = generate_zk(F_k_minus_1, Gk)
    zb = conflict_heuristic_zb(F_k_minus_1, Gk)
    print("USED Gk", Gk)
    return [ceil(zb[s]) if (row[s] == 0 and len(Zk) != 0) else zb[s] for s in S]

# F_k_minus_1 = np.array([0,0,0,0])
# Gk = LowerSet([(np.array([1,0,0,0]), 2/5)])
# conflict_heuristic_zb(F_k_minus_1, Gk)



states_so_far = []

def assert_invariants(F, G, k, n):
    assert len(F[0]) == 0
    assert 1 <= k and k <= n
    for j in S[:-2]:
        if len(F[j]) > 0:
            assert vector_leq(F[j], F[j+1])

    assert vector_leq(F[n-2], PROP)
    assert vector_leq(Phi(F[j]), F[j+1])

    # TODO
    

def adjointPDRdown():
    F = [[], [0 for _ in S], [1 for _ in S]]
    G = []

    iteration = 0
    while True:
        #print("SSF", states_so_far)
        if (F,G) in states_so_far:
            print("Loopy")
            return None
        #print("Adding", F, G)
        states_so_far.append((deepcopy(F),deepcopy(G)))
        Gk = G[0] if len(G) > 0 else None # index issues
        n = len(F)
        k = n - len(G)

        assert_invariants(F, G, k, n)

        # DEBUG
        iteration += 1
        print(f"\n{iteration}")
        print(f"n: {n}, k: {k}")
        # END DEBUG

        
        for j in range(len(F)-1):
            #print(f"Fj {F[j]}, Fj+1 {F[j+1]}")
            #if len(F[j]) >= 1 and all([isclose(x, y, rel_tol=1e-4) for x, y in zip(F[j], F[j+1])]):
            #print(f"\t comparing: {F[j]} and {F[j+1]}")
            if len(F[j]) >= 1 and all([isclose(x, y) for x, y in zip(F[j], F[j+1])]):
                assert vector_leq(Phi(F[j]), F[j])
                return True
        if len(G) != 0 and len(G[0]) == 0:
            return False

        # Unfold
        if len(G) == 0 and vector_leq(F[n-1], PROP):
            print("unfold")
            F.append([1 for _ in S])

        # Candidate
        elif len(G) == 0 and not vector_leq(F[n-1], PROP):
            print("candidate")
            ZZ = candidate_heuristic(PROP)
            G = [ZZ]
        
        # Decide
        elif len(G) > 0 and Phi(F[k-1]) not in Gk:
            # print("decide")
            # print("PHI: ", Phi(F[k-1]))
            # print('Gk: ', Gk)

            
            ZZ = decide_heuristic(F[k-1], Gk)
            assert F[k-1] not in ZZ
            # I don't know how to implement the other assert...
            G.insert(0, ZZ)

        # Conflict
        elif len(G) > 0 and Phi(F[k-1]) in Gk:
            # print("conflict")
            # print("PHI: ", Phi(F[k-1]))
            # print('Gk: ', Gk)

            z = conflict_heuristic_zb(F[k-1], Gk)
            print("z:", z)
            assert z in Gk
            assert vector_leq(Phi(meet([F[k-1], z])), z)
            
            F = [meet([Fj, z]) for (j, Fj) in enumerate(F) if j <= k] + [F[j] for j in range(k+1, n-1)]
            G.pop(0)
        else:
            print("OOPS")
        print("F", F)
        print("G", end=" ")
        [print(Gi, end=" ") for Gi in G]
        print()
        
print(adjointPDRdown())