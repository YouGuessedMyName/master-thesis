from helpers import *
import cdd
from z3 import Real, Optimize, Sum

def candidate_heuristic(p: V) -> LowerSet:
    return downarrow(p)

def decide_heuristic(F:V, Gk:LowerSet, M:MDP) -> LowerSet:
    policy = M.PhiPolicyArgMax(F)
    return M.PsiPolicy(policy, Gk)

def conflict_heuristic_simple(F: V, _:LowerSet, M) -> V:
    return M.Phi(F)

# def generate_zk(F_k_minus_1, Gk, M):
#     # print(f"Fk-1: {F_k_minus_1}")
#     # print(f"Gk: {Gk}")
#     L = len(F_k_minus_1)
#     assert len(Gk) == 1
#     row, r = Gk.eqs[0]

#     # OLD, BUT DONT DE-LETE YET
#     # constraints_geq_0 = [([0] + [1 if v == w else 0 for w in range(L)]) for v in range(L) if row[v] == 0] # ???
#     # # constraints_geq_0 = [([0] + [1 if v == w else 0 for w in range(L)]) for v in range(L)] # ???
#     # constraints_leq_1 = [([1] + [-1 if v == w else 0 for w in range(L)]) for v in range(L)]
#     # #constraints_geq_0 = constraints_leq_1 = []
#     # constraints_eqs = [[r] + [-x for x in row]]

#     # NEW
#     constraints_leq_1 = [([1] + [-1 if v == w else 0 for w in range(L)]) for v in range(L)]
#     constraints_geq_0 = [([0] + [1 if v == w else 0 for w in range(L)]) for v in range(L)]
#     constraints_eqs = [[r] + [-x for x in row]]

#     mat = cdd.matrix_from_array(constraints_geq_0 + constraints_leq_1 + constraints_eqs)
#     # print(mat)
#     mat.rep_type = cdd.RepType.INEQUALITY
#     poly = cdd.polyhedron_from_matrix(mat)
#     generators_raw = cdd.copy_generators(poly).array
#     #print(f"Gens raw: {generators_raw}")
#     # print("d[0]", [d[0] for d in generators_raw])
#     # generators = [[Frac(x).limit_denominator(1000) for x in d[1:]] for d in generators_raw 
#     #               if d[0] == 1 and all([not (d[v+1] == 0 and row[v] != 0) for v in range(L)])]
#     generators = [[Frac(x).limit_denominator(1000) for x in d[1:]] for d in generators_raw if d[0] == 1]
#     generators = [d for d in generators if sum([di*ri for di,ri in zip(d,row)]) >= r]
#     print(f"Gens:", [str_list(g) for g in generators])
#     #print(f"Phi(F_k_minus) {str_list(Phi(F_k_minus_1, M))}")
#     Zk = [d for d in generators if vector_leq(F_k_minus_1, d)]
#     #print("Zk", [str_list(g) for g in Zk])
#     return Zk



# def compute_Zk_meet(F_k_minus_1, row, r, M):
#     # Returns a boolean whihch is true iff Zk is not empty, and the meet of Zk
#     L = len(F_k_minus_1)
#     result = [1 for _ in range(L)]
#     not_empty = False
#     phi_applied = Phi(F_k_minus_1,M)
#     for i in range(L):
#         generator_basis = [0 for _ in range(L)] # meet of all the generators with this particular extreme coordinate.
#         if row[i] > 0:
#             extreme_coordinate = Frac(r / row[i]).limit_denominator(1000)
#             # First
        
#     return not_empty,result

# def generate_Zk_new(F_k_minus_1, Gk, M):
#     assert len(Gk) == 1
#     r, r0 = Gk.eqs[0]
#     phi_applied = F_k_minus_1

#     n = len(r)
#     T = [i for i in range(n) if r[i] > 0] # Only non-zeroes
#     Z = [i for i in range(n) if r[i] <= 0] # Only zeroes

#     generators = []

#     for s_star in T:

#         others = [s for s in T if s != s_star]

#         for assign in product([0,1], repeat=len(others)):
#             d = [0]*n
#             sum_fixed = 0 # The sum that you get from the other linear factors already

#             for s,val in zip(others,assign):
#                 d[s] = val
#                 sum_fixed += r[s]*val

#             d_star = (r0 - sum_fixed)/r[s_star] # The maximum amount that you can still assign to s* to be within the cube.
#             print("d_star", d_star)
#             print("d", d)
#             if 0 <= d_star <= 1:
#                 d[s_star] = d_star
#                 if not d in generators:
#                     generators.append(d.copy())
#     # expand zero-coefficient coordinates
#     final = []
#     for g in generators:
#         for assign in product([0,1], repeat=len(Z)):
#             v = g.copy()
#             for s,val in zip(Z,assign):
#                 v[s] = val
#             final.append([Frac(vi).limit_denominator(1000) for vi in v])

#     return [d for d in final if vector_leq(phi_applied, d) and sum([di*ri for di,ri in zip(d,r)]) >= r0]

# def conflict_heuristic_zb_new(F_k_minus_1, Gk, M):
#     assert len(Gk) == 1
#     r, r0 = Gk.eqs[0]
#     phi_applied = F_k_minus_1

#     n = len(r)
#     T = [i for i in range(n) if r[i] > 0] # Only non-zeroes
#     Z = [i for i in range(n) if r[i] <= 0] # Only zeroes

#     generators = []

#     for s_star in T:

#         others = [s for s in T if s != s_star]

#         for assign in product([0,1], repeat=len(others)):
#             d = [0]*n
#             sum_fixed = 0

#             for s,val in zip(others,assign):
#                 d[s] = val
#                 sum_fixed += r[s]*val

#             d_star = (r0 - Frac(sum_fixed).limit_denominator(1000))/r[s_star]

#             if 0 <= d_star <= 1:
#                 d[s_star] = d_star
#                 if vector_leq(phi_applied, d) and not d in generators:
#                     generators.append(d.copy())
#     mt = meet(generators)
#     res = []
#     for s in M.S:
#         if r[s] != 0 and len(generators) != 0:
#             res.append(mt[s])
#         else:
#             res.append(phi_applied[s])
#     return res
    
# def conflict_heuristic_zb(F_k_minus_1, Gk, M):
#     L = len(F_k_minus_1)
#     assert len(Gk) == 1
#     row, r = Gk.eqs[0]
#     #print("==================")
#     Zk = generate_zk(F_k_minus_1, Gk, M)
#     #print(f"Zk: {Zk}")
#     meetZk = meet(Zk)
#     #print(f"OLD meet Zk: {str_list(meetZk)}")
#     phi_applied = F_k_minus_1
#     #print("PHI:", phi_applied)
#     res = []
#     for s in M.S:
#         if row[s] != 0 and len(Zk) != 0:
#             res.append(meetZk[s])
#         else:
#             res.append(phi_applied[s])
#     #print(f"Z: {res}")
#     #print("==================")
#     return [Frac(x).limit_denominator(1000) for x in res]

# def conflict_heuristic_01(F_k_minus_1, Gk, M):
#     assert len(Gk) == 1
#     row, r = Gk.eqs[0]
#     Zk = generate_zk(F_k_minus_1, Gk, M)
#     zb = conflict_heuristic_zb(F_k_minus_1, Gk, M)
#     #print("USED Gk", Gk)
#     #return [ceil(zb[s]) if (row[s] == 0 and len(Zk) != 0) else zb[s] for s in M.S]
#     return [ceil(zb[s]) if (row[s] == 0 and len(Zk) != 0) else zb[s] for s in M.S]

# def conflict_heuristic_01_bad(F_k_minus_1, Gk, M):
#     assert len(Gk) == 1
#     row, r = Gk.eqs[0]
#     Zk = generate_zk(F_k_minus_1, Gk, M)
#     zb = conflict_heuristic_zb(F_k_minus_1, Gk, M)
#     #print("USED Gk", Gk)
#     #return [ceil(zb[s]) if (row[s] == 0 and len(Zk) != 0) else zb[s] for s in M.S]
#     return [1 if (row[s] == 0 and len(Zk) != 0) else zb[s] for s in M.S]

# def conflict_heuristic_opt(F_k_minus_1, Gk, M):
#     assert len(Gk) == 1
#     row, r = Gk.eqs[0]
#     phi_applied = Phi(F_k_minus_1, M)

#     vars_ = [Real(f"x_{i}") for i in range(len(F_k_minus_1))]
#     reward = Real("reward")
#     opt = Optimize()
#     for x in vars_:
#         opt.add(x >= 0)
#         opt.add(x <= 1)
#     opt.add(Sum([row[i] * vars_[i] for i in range(len(vars_)) if row[i] != 0]) <= r)
#     opt.add([phi_applied[i] <= vars_[i] for i in range(len(vars_))])

#     opt.add(reward == Sum(vars_))
#     h = opt.maximize(reward)
#     opt.check()
#     opt.lower(h)
#     model = opt.model()
#     sol = [model[x].as_decimal(1000) for x in vars_]
    
#     #print("PHI:", phi_applied)
#     res = []
#     for s in M.S:
#         if row[s] != 0:
#             #print("not zero!", sol[s], type(sol[s]))
#             if sol[s][-1] != "?": # Wierd z3 shenenigans
#                 res.append(sol[s])
#             else:
#                 res.append(sol[s][:-1])
#         else:
#             #print("zero...", phi_applied[s])
#             res.append(phi_applied[s])
#     #print(f"Z: {res}")
#     #print("==================")
#     return [Frac(float(x)).limit_denominator(1000) for x in res]

# def conflict_heuristic_opt2(F_k_minus_1, Gk, M):
#     assert len(Gk) == 1
#     row, r = Gk.eqs[0]
#     phi_applied = Phi(F_k_minus_1, M)

#     vars_ = [Real(f"x_{i}") for i in range(len(F_k_minus_1))]
#     reward = Real("reward")
#     opt = Optimize()
#     for x in vars_:
#         opt.add(x >= 0)
#         opt.add(x <= 1)
#     opt.add(Sum([row[i] * vars_[i] for i in range(len(vars_)) if row[i] != 0]) <= r)
#     opt.add([phi_applied[i] <= vars_[i] for i in range(len(vars_))])

#     opt.add(reward == Sum(vars_))
#     h = opt.minimize(reward)
#     opt.check()
#     opt.lower(h)
#     model = opt.model()
#     sol = [model[x].as_decimal(1000) for x in vars_]
    
#     #print("PHI:", phi_applied)
#     res = []
#     for s in M.S:
#         if row[s] != 0:
#             #print("not zero!", sol[s], type(sol[s]))
#             if sol[s][-1] != "?": # Wierd z3 shenenigans
#                 res.append(sol[s])
#             else:
#                 res.append(sol[s][:-1])
#         else:
#             #print("zero...", phi_applied[s])
#             res.append(phi_applied[s])
#     #print(f"Z: {res}")
#     #print("==================")
#     return [Frac(float(x)).limit_denominator(1000) for x in res]

# def conflict_heuristic_avg(F_k_minus_1, Gk, M):
#     h1 = conflict_heuristic_opt(F_k_minus_1, Gk, M)
#     h2 = conflict_heuristic_opt2(F_k_minus_1, Gk, M)
#     return [(x1 + x2)/2 for x1, x2 in zip(h1, h2)]

