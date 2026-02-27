from helpers import Frac, MDP
import stormpy
import stormvogel as sv

def example_21():
    S = [0,1,2,3]
    P_DICT = {
        0 : {'a': {0: 0, 1: 0.5, 2: 0.5, 3: 0},
            'b': {0: 1/3, 1: 0, 2: 2/3, 3: 0}},
        1 : {'a': {0: 1/2, 1: 0, 2: 0, 3: 1/2}},
        2 : {'b': {0: 1, 1: 0, 2: 0, 3: 0}},
        3 : {'a': {0: 0, 1: 0, 2: 0, 3: 1}}}
    def P(s,a,s_):
        return Frac(P_DICT[s][a][s_]).limit_denominator()
    
    def av(s):
        if s == 0:
            return ['a','b']
        elif s == 2:
            return ['b']
        else:
            return ['a']
        
    B = {3}
    PROP = [Frac(1, 4),Frac(1),Frac(1),Frac(1)]
    return MDP(S, P, av, B, PROP)

def example_23():
    S = [0,1,2,3]
    P_DICT = {
        0 : {'a': {0: 1, 1: 0, 2: 0, 3: 0},
            'b': {0: 0, 1: 1/2, 2: 1/2, 3: 0}},
        1 : {'a': {0: 1/3, 1: 0, 2: 0, 3: 2/3}},
        2 : {'b': {0: 0, 1: 0, 2: 1, 3: 0}},
        3 : {'a': {0: 0, 1: 0, 2: 0, 3: 1}}}
    def P(s,a,s_):
        return Frac(P_DICT[s][a][s_]).limit_denominator()
    def av(s):
        if s == 0:
            return ['a','b']
        elif s == 2:
            return ['b']
        else:
            return ['a']
    B = {3}
    PROP = [Frac(2, 5),Frac(1),Frac(1),Frac(1)]
    return MDP(S, P, av, B, PROP)

def from_stormvogel_mdp(sv_mdp):
    states = sv_mdp.get_states()
    S = [s.id for s in states]

    def av(s):
        state = sv_mdp.get_state_by_id(s)
        return state.available_actions()

    def P(s,a,s_):
        state = sv_mdp.get_state_by_id(s)
        state_ = sv_mdp.get_state_by_id(s_)
        if a not in state.available_actions():
            return Frac(0)
        outgoing = state.get_outgoing_transitions(a)
        p = sum([p for (p, s__) in outgoing if s__ == state_])
        res = Frac(p).limit_denominator(1000)
        return res
    return S, av, P

def monty_hall():
    sv_mdp: sv.Model = sv.examples.monty_hall.create_monty_hall_mdp()
    states = sv_mdp.get_states()
    S, av, P = from_stormvogel_mdp(sv_mdp)
    B = [state.id for state in states if "lost" in state.labels]
    LAMBDA = 0.99
    PROP = [Frac(LAMBDA).limit_denominator(1000)] + [Frac(1) for _ in range(len(S)-1)]
    res = MDP(S, P, av, B, PROP)
    return res

monty_hall()