from sym_adjpdr.frames import *
from sym_adjpdr.model import *
from sym_adjpdr.heuristics import *

def print_progress(iteration, F, G, k, n, M):
    print(f"\n{iteration}")
    print(f"n: {n}, k: {k}")
    [print(f"F{i}", Fi) for i, Fi in enumerate(F)]
    [print(f"G{i + n - len(G)}", Gi) for i, Gi in enumerate(G)]
    if len(G) == 0:
        print("G")
    else:
        print()
        #print("F_k-1", F[k-1])
        #print("Phi(F_k-1)", str_list(Phi(F[k-1], M)))
    # We don't need to return, F is modified by reference.

def adjointPDRdown(M: Model, do_propagate: bool, heuristics: list, used_heuristic: Callable, print_ : bool = True, assert_: bool = True, loop_check: bool = True):
    assert used_heuristic in heuristics
    states_so_far = []
    heuristics_so_far = {}
    F = [Frame.empty(M.ctx, M.vars), Frame.zeroes(M.ctx, M.vars), Frame.ones(M.ctx, M.vars)]
    F_meet_conjuncts = [[Frame.empty(M.ctx, M.vars)], [Frame.zeroes(M.ctx, M.vars)], [Frame.ones(M.ctx, M.vars)]]
    G = []
    n = k = 3
    iteration = 0

    while True:
        # Administration, and assert the invariants.
        if loop_check:
            if (F,G) in states_so_far:
                print(f"Looped after {iteration} iterations")
                return None, states_so_far, heuristics_so_far
            states_so_far.append((F.copy(), G.copy()))
        n = len(F)
        k = n - len(G)
        Gk = G[0] if len(G) > 0 else None # index issues
        if print_:
            print_progress(iteration, F, G, k, n, M)
        # assert invariants TODO
        # if assert_ == "all":
        #     assert_invariants(F, G, k, n, M, F_meet_conjuncts, do_propagate)
        iteration += 1

        # POSITIVELY CONCLUSIVE
        for j in range(len(F)-1):
            #print(f"Fj {F[j]}, Fj+1 {F[j+1]}")
            #if len(F[j]) >= 1 and all([isclose(x, y, rel_tol=1e-4) for x, y in zip(F[j], F[j+1])]):
            #print(f"\t comparing: {F[j]} and {F[j+1]}")
            if not F[j].is_empty and F[j] == F[j+1]:
                if assert_:
                    assert M.Phi(F[j]) <= F[j] if assert_ else None
                print(f"After {iteration-1} iterations")
                print("Inducitive invariant:", F[j]) if print_ else None
                return True, states_so_far, heuristics_so_far
        # NEGATIVELY CONCLUSIVE
        if len(G) != 0 and G[0].is_empty():
            print(f"After {iteration-1} iterations")
            return False, states_so_far, heuristics_so_far
        # if Gk is not None:
        #     print("second", Phi(F[k-1], M) in Gk)

        # UNFLOLD (+ propagate)
        if len(G) == 0 and F[n-1] <= M.prop:
            print(f"\tFn-1 {F[n-1]} <= PROP ==> unfold") if print_ else None
            F.append(Frame.ones(M.ctx, M.vars))

            # Propagate TODO

        # CANDIDATE
        elif len(G) == 0 and not F[n-1] <= M.prop:
            print(f"\tFn-1 {F[n-1]} > PROP ==> candidate") if print_ else None
            ZZ = Ca(M)
            G = [ZZ]
            print("\tZZ", ZZ) if print_ else None
            if assert_:
                assert F[n-1] not in ZZ
                assert M.prop in ZZ
        
        # DECIDE
        elif len(G) > 0 and M.Phi(F[k-1]) not in Gk:
            print(f"\tPhi(F_k-1) {M.Phi(F[k-1])} NOT in Gk {Gk} ==> decide") if print_ else None
            # print("PHI: ", Phi(F[k-1]))
            # print('Gk: ', Gk)
            ZZ = De(F[k-1], Gk, M, print_)
            #ZZ = Psi(Gk, M)
            print("\tZZ", ZZ)  if print_ else None
            # print("Psi", M.Psi(Gk)) if print_ else None
            if assert_:
                assert F[k-1] not in ZZ
                #assert M.Psi(Gk) <= ZZ TODO

            G.insert(0, ZZ)

        # CONFLICT
        elif len(G) > 0 and M.Phi(F[k-1]) in Gk:
            print(f"\tPhi(F_k-1) {M.Phi(F[k-1])} IN Gk {Gk} ==> conflict") if print_ else None
            # print("PHI: ", Phi(F[k-1]))
            # print('Gk: ', Gk)
            z = None
            if loop_check:
                heuristics_so_far[iteration] = {}
            for heuristic in heuristics:
                zh = heuristic(F[k-1], Gk, M)
                if heuristic == used_heuristic:
                    z = zh
                print("\t" + heuristic.__name__, zh) if print_ else None
                if loop_check:
                    heuristics_so_far[iteration][heuristic.__name__] = zh
                if assert_:
                    assert zh in Gk
                    assert M.Phi(Frame.meet(F[k-1], zh)) <= zh
            
            F = ([Frame.meet(Fj, z) for (j, Fj) in enumerate(F) if j <= k]) + [F[j] for j in range(k+1, n)]
            if do_propagate:
                F_meet_conjuncts = [Fj_conjuncts + [z] for (j, Fj_conjuncts) in enumerate(F_meet_conjuncts) if j <= k] \
                                + [F_meet_conjuncts[j] for j in range(k+1, n)]
            G.pop(0)

def testAdjointPDRdown(M: Model, heuristics, used_heuristic, propagate_= False, print_=True, assert_=True, loop_check=True):
    if not used_heuristic in heuristics:
        heuristics.append(used_heuristic)
    print("Start")
    res, states_list, heuristics_list = adjointPDRdown(M, propagate_, heuristics, used_heuristic, print_, assert_, loop_check)
    assert res is not None
    
    if M.max_prob >= Fraction(M.module.expected_result):
        assert res
        print(f"lambda ({M.max_prob}) >= expected result ({M.module.expected_result}). res: {res}, correct.")
    else:
        assert not res
        print(f"lambda ({M.max_prob}) <= expected result ({M.module.expected_result}). res: {res}, correct.")
    return res, states_list, heuristics_list