from helpers import *
import cdd
from z3 import Real, Optimize, Sum
import spaces

def Ca(p: V) -> LowerSet:
    return downarrow(p)

def De(F:V, Gk:LowerSet, M: MDP) -> LowerSet:
    policy = M.PhiPolicyArgMax(F)
    return M.PsiPolicy(policy, Gk)

def Cs(F: V, _:LowerSet, M: MDP) -> V:
    return M.Phi(F)

def Cb_slow(F:V, Gk:LowerSet, M: MDP) -> V:
    assert len(Gk) == 1
    r, r0 = Gk.eqs[0]
    meetZk = spaces.meet_Zk_slow(r, r0, M.Phi(F))
    phi_applied = M.Phi(F)
    return V([
        meetZk[s] if r[s] != 0 and len(meetZk) != 0
        else phi_applied[s]
        for s in range(len(r))
    ])

def Cb(F:V, Gk:LowerSet, M: MDP, meetZk=None) -> V:
    assert len(Gk) == 1
    if meetZk == None:
        meetZk = []
    r, r0 = Gk.eqs[0]
    for w in spaces.meet_Zk_fast(r, r0, M.Phi(F)):
        meetZk.append(w)
    phi_applied = M.Phi(F)
    return V([
        meetZk[s] if r[s] != 0 and len(meetZk) != 0
        else phi_applied[s]
        for s in range(len(r))
    ])

def C01(F:V, Gk:LowerSet, M: MDP) -> V:
    assert len(Gk) == 1
    r, _ = Gk.eqs[0]
    meetZk = []
    cb = Cb(F, Gk, M, meetZk=meetZk) # Modify by reference to check if it was empty.
    phi_applied = M.Phi(F)
    return V([
        ceil(cb[s]) if r[s] == 0 and len(meetZk) != 0
        else cb[s]
        for s in range(len(r))
    ])

def COpt(F: V, Gk: LowerSet, M: MDP) -> V:
    assert len(Gk) == 1
    r, r0 = Gk.eqs[0]
    phi_applied = M.Phi(F)

    vars_ = [Real(f"x_{i}") for i in range(len(F))]
    reward = Real("reward")
    opt = Optimize()
    for x in vars_:
        opt.add(x >= 0)
        opt.add(x <= 1)
    opt.add(Sum([r[i] * vars_[i] for i in range(len(vars_)) if r[i] != 0]) <= r0)
    opt.add([vars_[i] >= phi_applied[i] for i in range(len(vars_))])
    opt.add(reward == Sum(vars_))
    h = opt.maximize(reward)
    opt.check()
    model = opt.model()
    sol = [model[x].as_fraction() for x in vars_]

    res = []
    for s in M.S:
        if r[s] != 0:
            res.append(sol[s])
        else:
            res.append(phi_applied[s])

    return V([Frac(x).limit_denominator(DENOM_LIMIT) for x in res])
