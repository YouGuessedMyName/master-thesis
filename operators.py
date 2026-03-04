from typing import Callable
from helpers import MDP, Frac, LowerSet, str_list, argmax

def PhiPolicy(policy: Callable, F: list[float], M: MDP):
    return [
        1 if s in M.B else
            (Frac(sum(M.P(s,policy(s),s_) * F[s_])).limit_denominator(1000) for s_ in M.S)
        for s in M.S
    ]

def Phi(F: list[float], M: MDP):
    if len(F) == 0:
        return []
    return [
        1 if s in M.B else
            max([Frac(sum(M.P(s,a,s_) * F[s_] for s_ in M.S)).limit_denominator(1000) 
                for a in M.av(s)])
        for s in M.S
    ]

def PhiPolicyArgMax(F: list[Frac], M: MDP):
    """Return the policy that maximizes Phi."""
    if len(F) == 0:
        return []
    return [
            argmax([Frac(sum(M.P(s,a,s_) * F[s_] for s_ in M.S))
                for a in M.av(s)], M.av(s))
        for s in M.S
    ]

def NextStepPolicy(policy: list[str], F: list[float], M: MDP):
    # print("NEXT")
    # print("F", str_list(F))
    # print("pol", policy)
    return [
        Frac(sum(M.P(s_,policy[s_],s) * F[s_] for s_ in M.S)).limit_denominator(1000)
        for s in M.S
    ]

def PhiPolicy(policy: list[str], F: list[float], M: MDP):
    return [
        1 if s in M.B else
            sum(M.P(s,policy[s],s_) * F[s_] for s_ in M.S)
        for s in M.S
    ]

def PsiPolicyEq(policy: list[str], row, r, M: MDP):
    next_step = NextStepPolicy(policy, row, M)
    #print("next step", str_list(next_step))
    # Now account for Phi setting bad states to 1
    deduct = 0
    for s in M.B:
        #print(s)
        deduct += next_step[s]
        next_step[s] = 0
    # print("r", r, "deduct", deduct)
    return next_step, r - deduct
        

def PsiPolicy(policy: Callable, G: LowerSet, M):
    res = LowerSet([PsiPolicyEq(policy, row, r, M) for (row, r) in G.eqs])
    for (_, r) in res.eqs:
        if r < 0:
            return []
    return res

def Psi(G: LowerSet, M):
    res = LowerSet([])
    for policy in M.possible_policies():
        res += PsiPolicy(policy, G, M)
    if len(res.eqs) == 0:
        return []
    return res

def downarrow(p):
    for i, entry in enumerate(p):
        if i != 0:
            assert entry == 1
    return LowerSet([([1 / Frac(p[0]).limit_denominator(1000)] + [0 for _ in range(len(p)-1)], Frac(1))])

