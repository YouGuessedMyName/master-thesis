from sym_adjpdr.frames import *
from sym_adjpdr.model import *
from sym_adjpdr.heuristics import *
from sym_adjpdr.generalization import *
from sym_adjpdr.linear_generalization import *

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

def adjointPDRdown(M: Model, do_propagate: bool, heuristics, used_heuristic, generalizations, used_generalization, 
                   print_ : bool = True, assert_: bool = True, loop_check: bool = True):
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
            if not F[j].is_empty and F[j+1] <= F[j]:
                if assert_:
                    assert M.Phi(F[j]) <= F[j] and F[j] <= M.prop, "Algorithm terminated, but no inductive invariant..."
                if print_:
                    print(f"After {iteration-1} iterations")
                    print("Inducitive invariant:", F[j])
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
                if F[n-1] in ZZ:
                    F[n-1] in ZZ
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
                # print("F_k-1", F[k-1])
                # print("ZZ", ZZ)
                assert F[k-1] not in ZZ
                #assert M.Psi(Gk) <= ZZ TODO
                # What about exists n, s.t. Psi^n(Gk) <= ZZ??

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
                    # print("meet", Frame.meet(F[k-1], zh))
                    phi_meet = M.Phi(Frame.meet(F[k-1], zh))
                    # print("Phi meet", phi_meet)
                    # print("zh", zh)
                    le_set = phi_meet.pw.le_set(zh.pw)
                    # print("le set", le_set)
                    assert phi_meet <= zh
            
            z_ = None
            for gen in generalizations:
                if gen in [Phi_generalization, no_generalization]:
                    z_g = gen(F[k-1], Gk, z, M)
                else:
                    z_g = generalization_framework(F[k-1], Gk, z, M, gen)
                if gen == used_generalization:
                    z_ = z_g
            inv = Frame.meet(F[k], z_)
            print("\tz_: ", z_) if print_ else None
            print("\tinv: ", inv) if print_ else None
            if inv <= M.prop and M.Phi(inv) <= inv:
                if print_:
                    print(f"After {iteration-1} iterations")
                    print("Inducitive invariant:", inv)
                return True, states_so_far, heuristics_so_far
            
            if True: #if not inv in F:
                if assert_:
                    assert z_g in Gk
                    assert M.Phi(Frame.meet(F[k-1], z_g)) <= z_g
                F = [Frame.meet(Fj, z_) for (j, Fj) in enumerate(F) if j <= k] + [F[j] for j in range(k+1, n)]
            else: # Fallback
                print("Fallback") if print_ else None
                F = [Frame.meet(Fj, z) for (j, Fj) in enumerate(F) if j <= k] + [F[j] for j in range(k+1, n)]
            
            if do_propagate:
                F_meet_conjuncts = [Fj_conjuncts + [z] for (j, Fj_conjuncts) in enumerate(F_meet_conjuncts) if j <= k] \
                                + [F_meet_conjuncts[j] for j in range(k+1, n)]
            G.pop(0)

def testAdjointPDRdown(M: Model, heuristics, used_heuristic, generalizations, used_generalization, propagate_= False, generalization_=False, print_=True, assert_=True, loop_check=True):
    if not used_heuristic in heuristics:
        heuristics.append(used_heuristic)
    if not used_generalization in generalizations:
        generalizations.append(used_generalization)
    print("Start")
    print(M.module.expected_result)
    res, states_list, heuristics_list = adjointPDRdown(M, propagate_, heuristics, used_heuristic, generalizations, used_generalization, print_, assert_, loop_check)
    assert res is not None
    if M.module.expected_result:
        if M.max_prob >= Fraction(M.module.expected_result):
            assert res
            print(f"lambda ({M.max_prob}) >= expected result ({M.module.expected_result}). res: {res}, correct.")
        else:
            assert not res
            print(f"lambda ({M.max_prob}) <= expected result ({M.module.expected_result}). res: {res}, correct.")
        return res, states_list, heuristics_list
    else:
        print("No expected result set, res: ", res)