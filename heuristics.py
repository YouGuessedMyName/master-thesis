from helpers import *
from operators import *
import cdd
from z3 import Real, Optimize, Sum

def candidate_heuristic(p):
    return downarrow(p)

def decide_heuristic(F_k_minus_1, Gk, M:MDP):
    # for number, policy in enumerate(M.possible_policies()):
    #     if PhiPolicy(policy, F_k_minus_1, M) not in Gk: # This is kind of stupid, just arg max in computing Phi, and you obtain your policy!
    #         # print("policy no.", number)
    #         return PsiPolicy(policy, Gk, M)
    # return set()
    policy = PhiPolicyArgMax(F_k_minus_1, M)
    #print("policy", policy)
    if PhiPolicy(policy, F_k_minus_1, M) not in Gk:
        return PsiPolicy(policy, Gk, M)
    return []

def generate_zk(F_k_minus_1, Gk, M):
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
    # print(mat)
    mat.rep_type = cdd.RepType.INEQUALITY
    poly = cdd.polyhedron_from_matrix(mat)
    generators_raw = cdd.copy_generators(poly).array
    # print(f"Gens raw: {generators_raw}")
    generators = [[Frac(x).limit_denominator(1000) for x in d[1:]] for d in generators_raw]
    #print(f"Gens: {generators}")
    #print(f"Phi(F_k_minus) {Phi(F_k_minus_1)}")
    Zk = [d for d in generators if vector_leq(Phi(F_k_minus_1, M), d)]
    return Zk

def conflict_heuristic_simple(F_k_minus_1, Gk, M):
    return Phi(F_k_minus_1, M)

def conflict_heuristic_zb(F_k_minus_1, Gk, M):
    L = len(F_k_minus_1)
    assert len(Gk) == 1
    row, r = Gk.eqs[0]
    #print("==================")
    Zk = generate_zk(F_k_minus_1, Gk, M)
    #print(f"Zk: {Zk}")
    meetZk = meet(Zk)
    # print(f"meet of Zk: {meetZk}")
    phi_applied = Phi(F_k_minus_1, M)
    #print("PHI:", phi_applied)
    res = []
    for s in M.S:
        if row[s] != 0 and len(Zk) != 0:
            res.append(meetZk[s])
        else:
            res.append(phi_applied[s])
    #print(f"Z: {res}")
    #print("==================")
    return [Frac(x).limit_denominator(1000) for x in res]

def conflict_heuristic_01(F_k_minus_1, Gk, M):
    assert len(Gk) == 1
    row, r = Gk.eqs[0]
    Zk = generate_zk(F_k_minus_1, Gk, M)
    zb = conflict_heuristic_zb(F_k_minus_1, Gk, M)
    #print("USED Gk", Gk)
    #return [ceil(zb[s]) if (row[s] == 0 and len(Zk) != 0) else zb[s] for s in M.S]
    return [ceil(zb[s]) if (row[s] == 0 and len(Zk) != 0) else zb[s] for s in M.S]

def conflict_heuristic_01_bad(F_k_minus_1, Gk, M):
    assert len(Gk) == 1
    row, r = Gk.eqs[0]
    Zk = generate_zk(F_k_minus_1, Gk, M)
    zb = conflict_heuristic_zb(F_k_minus_1, Gk, M)
    #print("USED Gk", Gk)
    #return [ceil(zb[s]) if (row[s] == 0 and len(Zk) != 0) else zb[s] for s in M.S]
    return [1 if (row[s] == 0 and len(Zk) != 0) else zb[s] for s in M.S]

def conflict_heuristic_opt(F_k_minus_1, Gk, M):
    assert len(Gk) == 1
    row, r = Gk.eqs[0]
    phi_applied = Phi(F_k_minus_1, M)

    vars_ = [Real(f"x_{i}") for i in range(len(F_k_minus_1))]
    reward = Real("reward")
    opt = Optimize()
    for x in vars_:
        opt.add(x >= 0)
        opt.add(x <= 1)
    opt.add(Sum([row[i] * vars_[i] for i in range(len(vars_)) if row[i] != 0]) <= r)
    opt.add([phi_applied[i] <= vars_[i] for i in range(len(vars_))])

    opt.add(reward == Sum(vars_))
    h = opt.maximize(reward)
    opt.check()
    opt.lower(h)
    model = opt.model()
    sol = [model[x].as_decimal(1000) for x in vars_]
    
    #print("PHI:", phi_applied)
    res = []
    for s in M.S:
        if row[s] != 0:
            #print("not zero!", sol[s], type(sol[s]))
            if sol[s][-1] != "?": # Wierd z3 shenenigans
                res.append(sol[s])
            else:
                res.append(sol[s][:-1])
        else:
            #print("zero...", phi_applied[s])
            res.append(phi_applied[s])
    #print(f"Z: {res}")
    #print("==================")
    return [Frac(float(x)).limit_denominator(1000) for x in res]

def conflict_heuristic_opt2(F_k_minus_1, Gk, M):
    assert len(Gk) == 1
    row, r = Gk.eqs[0]
    phi_applied = Phi(F_k_minus_1, M)

    vars_ = [Real(f"x_{i}") for i in range(len(F_k_minus_1))]
    reward = Real("reward")
    opt = Optimize()
    for x in vars_:
        opt.add(x >= 0)
        opt.add(x <= 1)
    opt.add(Sum([row[i] * vars_[i] for i in range(len(vars_)) if row[i] != 0]) <= r)
    opt.add([phi_applied[i] <= vars_[i] for i in range(len(vars_))])

    opt.add(reward == Sum(vars_))
    h = opt.minimize(reward)
    opt.check()
    opt.lower(h)
    model = opt.model()
    sol = [model[x].as_decimal(1000) for x in vars_]
    
    #print("PHI:", phi_applied)
    res = []
    for s in M.S:
        if row[s] != 0:
            #print("not zero!", sol[s], type(sol[s]))
            if sol[s][-1] != "?": # Wierd z3 shenenigans
                res.append(sol[s])
            else:
                res.append(sol[s][:-1])
        else:
            #print("zero...", phi_applied[s])
            res.append(phi_applied[s])
    #print(f"Z: {res}")
    #print("==================")
    return [Frac(float(x)).limit_denominator(1000) for x in res]

def conflict_heuristic_avg(F_k_minus_1, Gk, M):
    h1 = conflict_heuristic_opt(F_k_minus_1, Gk, M)
    h2 = conflict_heuristic_opt2(F_k_minus_1, Gk, M)
    return [(x1 + x2)/2 for x1, x2 in zip(h1, h2)]

