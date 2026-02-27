from heuristics import *
from copy import deepcopy
from examples import *

states_so_far = []

def assert_invariants(F, G, k, n, M: MDP):
    assert len(F[0]) == 0
    assert 1 <= k and k <= n
    for j in range(len(F)-1):
        if len(F[j]) > 0:
            assert vector_leq(F[j], F[j+1])

    assert vector_leq(F[n-2], M.PROP)
    assert vector_leq(Phi(F[j], M), F[j+1])

    # TODO
    

def adjointPDRdown(M: MDP):
    F = [[], [Frac(0,1) for _ in M.S], [Frac(1,1) for _ in M.S]]
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

        assert_invariants(F, G, k, n, M)

        # DEBUG
        iteration += 1
        print(f"\n{iteration}")
        print(f"n: {n}, k: {k}")
        # END DEBUG

        
        for j in range(len(F)-1):
            #print(f"Fj {F[j]}, Fj+1 {F[j+1]}")
            #if len(F[j]) >= 1 and all([isclose(x, y, rel_tol=1e-4) for x, y in zip(F[j], F[j+1])]):
            #print(f"\t comparing: {F[j]} and {F[j+1]}")
            if len(F[j]) >= 1 and all([x == y for x, y in zip(F[j], F[j+1])]):
                assert vector_leq(Phi(F[j], M), F[j])
                return True
        if len(G) != 0 and len(G[0]) == 0:
            return False

        # Unfold
        if len(G) == 0 and vector_leq(F[n-1], M.PROP):
            print("unfold")
            F.append([1 for _ in M.S])

        # Candidate
        elif len(G) == 0 and not vector_leq(F[n-1], M.PROP):
            print("candidate")
            ZZ = candidate_heuristic(M.PROP)
            G = [ZZ]
        
        # Decide
        elif len(G) > 0 and Phi(F[k-1], M) not in Gk:
            print("decide")
            # print("PHI: ", Phi(F[k-1]))
            # print('Gk: ', Gk)

            
            ZZ = decide_heuristic(F[k-1], Gk, M)
            assert F[k-1] not in ZZ
            # I don't know how to implement the other assert...
            G.insert(0, ZZ)

        # Conflict
        elif len(G) > 0 and Phi(F[k-1], M) in Gk:
            print("conflict")
            # print("PHI: ", Phi(F[k-1]))
            # print('Gk: ', Gk)
            zs = conflict_heuristic_simple(F[k-1], Gk, M)
            print("zs:", str_list(zs))
            # zb = conflict_heuristic_zb(F[k-1], Gk, M)
            # print("zb:", str_list(zb))
            # z01 = conflict_heuristic_01(F[k-1], Gk, M)
            # print("z01:", str_list(z01))
            # zbad = conflict_heuristic_01_bad(F[k-1], Gk, M)
            # print("zbad:", str_list(zbad))
            # zopt = conflict_heurisitic_opt(F[k-1], Gk, M)
            # print("zopt", str_list(zopt))
            z = zs
            # print("Phi(z)", str_list(Phi(z, M)))
            # if vector_leq(Phi(z, M), z) and vector_leq(z, M.PROP):
            #     print("z was perfect.")
            #     return True
            assert z in Gk
            assert vector_leq(Phi(meet([F[k-1], z]), M), z)
            
            F = [meet([Fj, z]) for (j, Fj) in enumerate(F) if j <= k] + [F[j] for j in range(k+1, n-1)]
            G.pop(0)
        else:
            print("OOPS")
            return None
        print("F", end=" ")
        [print(str_list(Fi), end=" ") for Fi in F]
        print()
        print("G", end=" ")
        [print(Gi, end=" ") for Gi in G]
        print()
        
#print(adjointPDRdown(example_21()))
print(adjointPDRdown(monty_hall()))