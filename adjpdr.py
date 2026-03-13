from heuristics import *
from copy import deepcopy
from examples import *


def assert_invariants(F, G, k, n, M: MDP, F_meet_conjuncts):
    # The meet conjuncts are correct
    for j in range (len(F)-1):
        # print("j", j)
        # print("Fj", str_list(F[j]))
        # print("conjuncts")
        # for conj in F_meet_conjuncts[j]:
        #     print(str_list(conj))
        if not meet(F_meet_conjuncts[j]) == F[j]:
            print("conj", F_meet_conjuncts[j])
            print(F[j])
        assert meet(F_meet_conjuncts[j]) == F[j]

    assert len(F[0]) == 0 # I0
    assert 1 <= k and k <= n
    for j in range(len(F)-1):
        if len(F[j]) > 0:
            assert vector_leq(F[j], F[j+1])

    assert vector_leq(F[n-2], M.PROP)
    assert vector_leq(Phi(F[j], M), F[j+1]) # P3

    if len(G) >= 1:
        # print("PROP", str_list(M.PROP))
        # print("Gn-1", G[len(G)-1])
        assert M.PROP in G[len(G)-1] # N1

        for i in range(len(G)-1): # N2
            # print("Comparing:")
            # print("Psi:", Psi(G[i+1], M))
            # print("G", G[i])
            assert Psi(G[i+1], M) <= G[i]
    
        for j in range(len(F)-1): # PN
            if 0 <= j - k < len(G):
                Gj = G[j - k]
                assert F[j] not in Gj

    
    for j in range(len(F)-1):
        # A1a
        assert vector_leq(apply(Phi, j, [], M), F[j])
        
        if j >= 1:
            # A1b (F is an overapproximation of the positive chain.)
            assert F[j] in apply(Psi, n-1-j, downarrow([1 for _ in range(len(F[j]))]), M)

            # TODO A2 and A3, should refactor LowerSet first.
            
            # A3 (G is an overapproximation of the negative chain.)
            if 0 <= j - k < len(G):
                Gj = G[j - k]
                assert apply(Psi, n-1-j, downarrow(M.PROP), M) <= Gj

def print_progress(iteration, F, G, k, n, M):
    print(f"\n{iteration}")
    print(f"n: {n}, k: {k}")
    [print(f"F{i}", str_list(Fi)) for i, Fi in enumerate(F)]
    [print(f"G{i + n - len(G)}", Gi) for i, Gi in enumerate(G)]
    if len(G) == 0:
        print("G")
    else:
        print()
        print("F_k-1", str_list(F[k-1]))
        #print("Phi(F_k-1)", str_list(Phi(F[k-1], M)))

def propagate(F, F_meet_conjuncts, M):
    for i in range(len(F)-2):
        for j in range(len(F_meet_conjuncts[i])):
            F_j_prime = F_meet_conjuncts[i][j]
            if len(F_j_prime) != 0:
                if vector_leq(Phi(F[i], M), F_j_prime):
                    F[i+1] = meet([F[i+1], F_j_prime])
                    F_meet_conjuncts[i+1].append(F_j_prime)
    # We don't need to return, F is modified by reference.

def adjointPDRdown(M: MDP):
    states_so_far = []
    F = [[], [Frac(0) for _ in M.S], [Frac(1) for _ in M.S]]
    F_meet_conjuncts = [[[]], [[Frac(0) for _ in M.S]], [[Frac(1) for _ in M.S]]]
    G = []
    n = k = 3
    iteration = 0

    while True:
        
        #print("SSF", states_so_far)
        if (F,G) in states_so_far:
            print("Loopy")
            return None
        #print("Adding", F, G)
        states_so_far.append((deepcopy(F),deepcopy(G)))

        n = len(F)
        k = n - len(G)
        Gk = G[0] if len(G) > 0 else None # index issues
        print_progress(iteration, F, G, k, n, M)

        assert_invariants(F, G, k, n, M, F_meet_conjuncts)

        iteration += 1
        

        
        for j in range(len(F)-1):
            #print(f"Fj {F[j]}, Fj+1 {F[j+1]}")
            #if len(F[j]) >= 1 and all([isclose(x, y, rel_tol=1e-4) for x, y in zip(F[j], F[j+1])]):
            #print(f"\t comparing: {F[j]} and {F[j+1]}")
            if len(F[j]) >= 1 and all([x == y for x, y in zip(F[j], F[j+1])]):
                assert vector_leq(Phi(F[j], M), F[j])
                print("Inducitive invariant:", str_list(F[j]))
                return True
        if len(G) != 0 and len(G[0]) == 0:
            return False
        # if Gk is not None:
        #     print("second", Phi(F[k-1], M) in Gk)
        # Unfold
        if len(G) == 0 and vector_leq(F[n-1], M.PROP):
            print(f"Fn-1 {str_list(F[n-1])} <= PROP ==> unfold")
            F.append([1 for _ in M.S])
            F_meet_conjuncts.append([[1 for _ in M.S]])

            # PROPAGATE
            old_F = [[deepcopy(y) for y in x] for x in F]
            #propagate(F, F_meet_conjuncts, M)
            if F != old_F:
                print("Old situation:")
                [print(f"F{i}", str_list(Fi)) for i, Fi in enumerate(old_F)]
                print("Propagate did something!")
                #assert False # Just to warn me
                print()

        # Candidate
        elif len(G) == 0 and not vector_leq(F[n-1], M.PROP):
            print(f"Fn-1 {str_list(F[n-1])} > PROP ==> candidate")
            ZZ = candidate_heuristic(M.PROP)
            G = [ZZ]
        
        # Decide
        elif len(G) > 0 and Phi(F[k-1], M) not in Gk:
            print(f"Phi(F_k-1) {str_list(Phi(F[k-1], M))} NOT in Gk {Gk} ==> decide")
            # print("PHI: ", Phi(F[k-1]))
            # print('Gk: ', Gk)

            
            ZZ = decide_heuristic(F[k-1], Gk, M)
            #ZZ = Psi(Gk, M)
            print("ZZ", ZZ)
            print("Psi", Psi(Gk, M))
            assert F[k-1] not in ZZ
            assert Psi(Gk, M) <= ZZ

            G.insert(0, ZZ)

        # Conflict
        elif len(G) > 0 and Phi(F[k-1], M) in Gk:
            print(f"Phi(F_k-1) {str_list(Phi(F[k-1], M))} IN Gk {Gk} ==> conflict")
            # print("PHI: ", Phi(F[k-1]))
            # print('Gk: ', Gk)
            zs = conflict_heuristic_simple(F[k-1], Gk, M)
            # print("zs:", str_list(zs))
            zbnew = conflict_heuristic_zb_new(F[k-1], Gk, M)
            print("zbnew:", str_list(zbnew))
            zb = conflict_heuristic_zb(F[k-1], Gk, M)
            print("zb:", str_list(zb))
            #assert zb == zbnew
            # z01 = conflict_heuristic_01(F[k-1], Gk, M)
            # print("z01:", str_list(z01))
            # zbad = conflict_heuristic_01_bad(F[k-1], Gk, M)
            # print("zbad:", str_list(zbad))
            # zopt = conflict_heuristic_opt(F[k-1], Gk, M)
            # print("zopt", str_list(zopt))
            
            z = zbnew
            # print("Phi(z)", str_list(Phi(z, M)))
            # if vector_leq(Phi(z, M), z) and vector_leq(z, M.PROP):
            #     print("z was perfect.")
            #     return True
            assert z in Gk
            assert vector_leq(Phi(meet([F[k-1], z]), M), z)
            
            F = [meet([Fj, z]) for (j, Fj) in enumerate(F) if j <= k] + [F[j] for j in range(k+1, n)]
            F_meet_conjuncts = [Fj_conjuncts + [z] for (j, Fj_conjuncts) in enumerate(F_meet_conjuncts) if j <= k] + [F_meet_conjuncts[j] for j in range(k+1, n)]
            G.pop(0)
        else:
            print("OOPS")
            return None

def testAdjointPDRdown(M: MDP):
    res = adjointPDRdown(M)
    assert res is not None
    LAMBDA = M.PROP[0].limit_denominator(1000)
    
    if LAMBDA >= Frac(M.EXPECTED_RESULT).limit_denominator(1000):
        assert res
        print(f"lambda ({LAMBDA}) >= expected result ({M.EXPECTED_RESULT}). res: {res}, correct.")
    else:
        assert not res
        print(f"lambda ({LAMBDA}) < expected result ({M.EXPECTED_RESULT}). res: {res}, correct.")

#testAdjointPDRdown(example_21())
#testAdjointPDRdown(example_23())
#testAdjointPDRdown(study(5/10))    
testAdjointPDRdown(die(0.17))
#testAdjointPDRdown(grid(0.7))
#testAdjointPDRdown(two_d(0.5))