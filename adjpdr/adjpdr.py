from heuristics import *
from copy import deepcopy
from examples import *

def assert_invariants(F, G, k, n, M: MDP, F_meet_conjuncts, do_propagate):
    for Fi in F: # No accidental regular lists
        assert type(Fi) == V
    
    
    if do_propagate: # The meet conjuncts are correct
        for j in range (len(F)-1):
            if not meet(F_meet_conjuncts[j]) == F[j]:
                print("conj", F_meet_conjuncts[j])
                print(F[j])
            assert meet(F_meet_conjuncts[j]) == F[j]

    assert len(F[0]) == 0 # I0
    assert 1 <= k and k <= n
    for j in range(len(F)-1):
        if len(F[j]) > 0:
            assert F[j] <= F[j+1]

    assert F[n-2] <= M.PROP
    assert M.Phi(F[j]) <= F[j+1] # P3

    if len(G) >= 1:
        # print("PROP", str_list(M.PROP))
        # print("Gn-1", G[len(G)-1])
        assert M.PROP in G[len(G)-1] # N1

        for i in range(len(G)-1): # N2
            # print("Comparing:")
            # print("Psi:", Psi(G[i+1], M))
            # print("G", G[i])
            assert M.Psi(G[i+1]) <= G[i]
    
        for j in range(len(F)-1): # PN
            if 0 <= j - k < len(G):
                Gj = G[j - k]
                assert F[j] not in Gj

    
    for j in range(len(F)-1):
        # A1a
        assert apply(M.Phi, j, []) <= F[j]
        
        if j >= 1:
            # A1b (F is an overapproximation of the positive chain.)
            assert F[j] in apply(M.Psi, n-1-j, downarrow([1 for _ in range(len(F[j]))]))

            # A2
            assert F[j-1] in apply(M.Psi, n-1-j, (downarrow(M.PROP)))
            
            # A3 (G is an overapproximation of the negative chain.)
            if 0 <= j - k < len(G):
                Gj = G[j - k]
                assert apply(M.Psi, n-1-j, downarrow(M.PROP)) <= Gj

def print_progress(iteration, F, G, k, n, M):
    print(f"\n{iteration}")
    print(f"n: {n}, k: {k}")
    [print(f"F{i}", Fi) for i, Fi in enumerate(F)]
    [print(f"G{i + n - len(G)}", Gi) for i, Gi in enumerate(G)]
    if len(G) == 0:
        print("G")
    else:
        print()
        print("F_k-1", F[k-1])
        #print("Phi(F_k-1)", str_list(Phi(F[k-1], M)))

def propagate(F, F_meet_conjuncts, M):
    for i in range(len(F)-2):
        for j in range(len(F_meet_conjuncts[i])):
            F_j_prime = F_meet_conjuncts[i][j]
            if len(F_j_prime) != 0:
                if M.Phi(F[i]) <= F_j_prime:
                    F[i+1] = meet([F[i+1], F_j_prime])
                    F_meet_conjuncts[i+1].append(F_j_prime)
    # We don't need to return, F is modified by reference.

def adjointPDRdown(M: MDP, do_propagate: bool, heuristics: list, used_heuristic: Callable):
    assert used_heuristic in heuristics
    q = len(M.S)
    states_so_far = []
    F = [V.empty(), V.zeroes(q), V.ones(q)]
    F_meet_conjuncts = [[V.empty()], [V.zeroes(q)], [V.ones(q)]]
    G = []
    n = k = 3
    iteration = 0

    while True:
        # Administration, and assert the invariants.
        if (F,G) in states_so_far:
            print("Looped")
            return None
        states_so_far.append((deepcopy(F),deepcopy(G)))
        n = len(F)
        k = n - len(G)
        Gk = G[0] if len(G) > 0 else None # index issues
        print_progress(iteration, F, G, k, n, M)
        assert_invariants(F, G, k, n, M, F_meet_conjuncts, do_propagate)
        iteration += 1

        # POSITIVELY CONCLUSIVE
        for j in range(len(F)-1):
            #print(f"Fj {F[j]}, Fj+1 {F[j+1]}")
            #if len(F[j]) >= 1 and all([isclose(x, y, rel_tol=1e-4) for x, y in zip(F[j], F[j+1])]):
            #print(f"\t comparing: {F[j]} and {F[j+1]}")
            if len(F[j]) >= 1 and all([x == y for x, y in zip(F[j], F[j+1])]):
                assert M.Phi(F[j]) <= F[j]
                print("Inducitive invariant:", F[j])
                return True
        # NEGATIVELY CONCLUSIVE
        if len(G) != 0 and G[0].is_empty():
            return False
        # if Gk is not None:
        #     print("second", Phi(F[k-1], M) in Gk)

        # UNFLOLD (+ propagate)
        if len(G) == 0 and F[n-1] <= M.PROP:
            print(f"Fn-1 {F[n-1]} <= PROP ==> unfold")
            F.append(V.ones(q))

            # Propagate
            if do_propagate:
                F_meet_conjuncts.append([V.ones(q)])
                old_F = [[deepcopy(y) for y in x] for x in F]
                propagate(F, F_meet_conjuncts, M)
                if F != old_F:
                    print("Old situation:")
                    [print(f"F{i}", Fi) for i, Fi in enumerate(old_F)]
                    print("Propagate did something!")
                    #assert False # Just to warn me
                    print()

        # CANDIDATE
        elif len(G) == 0 and not F[n-1] <= M.PROP:
            print(f"Fn-1 {F[n-1]} > PROP ==> candidate")
            ZZ = candidate_heuristic(M.PROP)
            G = [ZZ]
        
        # DECIDE
        elif len(G) > 0 and M.Phi(F[k-1]) not in Gk:
            print(f"Phi(F_k-1) {M.Phi(F[k-1])} NOT in Gk {Gk} ==> decide")
            # print("PHI: ", Phi(F[k-1]))
            # print('Gk: ', Gk)
            ZZ = decide_heuristic(F[k-1], Gk, M)
            #ZZ = Psi(Gk, M)
            print("ZZ", ZZ)
            print("Psi", M.Psi(Gk))
            assert F[k-1] not in ZZ
            assert M.Psi(Gk) <= ZZ

            G.insert(0, ZZ)

        # CONFLICT
        elif len(G) > 0 and M.Phi(F[k-1]) in Gk:
            print(f"Phi(F_k-1) {M.Phi(F[k-1])} IN Gk {Gk} ==> conflict")
            # print("PHI: ", Phi(F[k-1]))
            # print('Gk: ', Gk)
            for heuristic in heuristics:
                zh = heuristic(F[k-1], Gk, M)
                print(heuristic.__name__, zh)
                assert zh in Gk
                assert M.Phi(meet([F[k-1], zh])) <= zh
            
            z = used_heuristic(F[k-1], Gk, M)
            F = V([meet([Fj, z]) for (j, Fj) in enumerate(F) if j <= k]) + V([F[j] for j in range(k+1, n)])
            if do_propagate:
                F_meet_conjuncts = [Fj_conjuncts + [z] for (j, Fj_conjuncts) in enumerate(F_meet_conjuncts) if j <= k] \
                                + [F_meet_conjuncts[j] for j in range(k+1, n)]
            G.pop(0)

def testAdjointPDRdown(M: MDP, heuristics, used_heuristic):
    res = adjointPDRdown(M, False, heuristics, used_heuristic)
    assert res is not None
    LAMBDA = M.PROP[0].limit_denominator(1000)
    
    if LAMBDA >= Frac(M.EXPECTED_RESULT).limit_denominator(1000):
        assert res
        print(f"lambda ({LAMBDA}) >= expected result ({M.EXPECTED_RESULT}). res: {res}, correct.")
    else:
        assert not res
        print(f"lambda ({LAMBDA}) < expected result ({M.EXPECTED_RESULT}). res: {res}, correct.")

EXAMPLE = grid()
HEUR = [conflict_heuristic_simple]
USED = conflict_heuristic_simple 
testAdjointPDRdown(EXAMPLE, HEUR, USED)