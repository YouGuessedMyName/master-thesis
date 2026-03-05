from helpers import Frac, MDP
import stormpy
import stormvogel as sv

def example_21(lambda_=1/4):
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
    PROP = [Frac(lambda_),Frac(1),Frac(1),Frac(1)]
    return MDP(S, P, av, B, PROP, 1)

def example_23(lambda_=2/5):
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
    PROP = [Frac(lambda_).limit_denominator(1000),Frac(1),Frac(1),Frac(1)]
    return MDP(S, P, av, B, PROP, Frac(2,5))

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

def from_stormvogel_dtmc(sv_dtmc: sv.Model):
    states = sv_dtmc.get_states()
    S = [s.id for s in states]

    def av(s):
        return ["a"]

    def P(s,_,s_):
        state = sv_dtmc.get_state_by_id(s)
        state_ = sv_dtmc.get_state_by_id(s_)
        outgoing = state.get_outgoing_transitions()
        p = sum([p for (p, s__) in outgoing if s__ == state_])
        res = Frac(p).limit_denominator(1000)
        return res
    return S, av, P

def from_stormvogel_problem(sv_model: sv.Model, lambda_, bad_label):
    """If lambda is higher than the result that Storm gives, then the result should be true else false."""
    states = sv_model.get_states()
    if sv_model.get_type() == sv.ModelType.DTMC:
        S, av, P = from_stormvogel_dtmc(sv_model)
    else:
        S, av, P = from_stormvogel_mdp(sv_model)
    B = [state.id for state in states if bad_label in state.labels]
    PROP = [Frac(lambda_).limit_denominator(1000)] + [Frac(1) for _ in range(len(S)-1)]
    EXPECTED_RESULT = sv.model_checking(sv_model, f'Pmax=? [F "{bad_label}"]').get_result_of_state(0)
    res = MDP(S, P, av, B, PROP, EXPECTED_RESULT)
    return res

def create_die_dtmc():
    # Create an initial state. States can be of any type. In this case we use integers.
    init = 0

    TRANSITIONS = {
        0: [(1 / 2, 1), (1 / 2, 2)],
        1: [(1 / 2, 3), (1 / 2, 4)],
        2: [(1 / 2, 5), (1 / 2, 6)],
        3: [(1 / 2, 1), (1 / 2, 7)],
        4: [(1 / 2, 8), (1 / 2, 9)],
        5: [(1 / 2, 10), (1 / 2, 11)],
        6: [(1 / 2, 2), (1 / 2, 12)],
    }


    # In the bird API, states are given implicitly. Any object can be a state and via the transition relation, we define reachable states.
    # This user-defined delta function encodes the transition relation. It takes as an argument a single state, and returns a
    # list of 2-tuples that encode the distribution over the successor states. More precisely, the first argument is a probability and the second elment is a state (a distribution).
    def delta(s):
        if s <= 6:
            return TRANSITIONS[s]
        return [(1, s)]


    # Labels is a function that tells the bird API what the label should be for a state.
    def labels(s):
            if s <= 6:
                return [str(s)]
            return [f"r{s-6}"]


    bird_die = sv.bird.build_bird(
        delta=delta, init=init, labels=labels, modeltype=sv.ModelType.DTMC
    )
    return bird_die

def create_study_mdp():
    mdp = sv.model.new_mdp()

    init = mdp.get_initial_state()
    study = mdp.action("study")
    not_study = mdp.action("don't study")

    pass_test = mdp.new_state("pass_test")
    fail_test = mdp.new_state("fail_test")
    end = mdp.new_state("end")

    init.set_choice(
        {
            study: [(9 / 10, pass_test), (1 / 10, fail_test)],
            not_study: [(4 / 10, pass_test), (6 / 10, fail_test)],
        }
    )

    pass_test.set_choice([(1, end)])
    fail_test.set_choice([(1, end)])

    mdp.add_self_loops()

    reward_model = mdp.new_reward_model("R")
    reward_model.set_state_action_reward(pass_test, sv.model.EmptyAction, 100)
    reward_model.set_state_action_reward(fail_test, sv.model.EmptyAction, 0)
    reward_model.set_state_action_reward(init, not_study, 15)
    reward_model.set_state_action_reward(init, study, 0)
    reward_model.set_unset_rewards(0)

    return mdp

def monty_hall(lambda_):
    return from_stormvogel_problem(sv.examples.monty_hall.create_monty_hall_mdp(), lambda_, "lost")

def study(lambda_):
    return from_stormvogel_problem(create_study_mdp(), lambda_, "fail_test")

def die(lambda_=1/6):
    return from_stormvogel_problem(create_die_dtmc(), lambda_, "r6")

def grid(lambda_=1/2):
    DELTA = {
        0: [(.5, 1), (.5, 2)],
        1: [(.5, 3), (.5, 6)],
        2: [(.5, 3), (.5, 4)],
        3: [(.5, 5), (.5, 7)],
    }
    def delta(s):
        return DELTA[s] if s in DELTA else [(1,s)]
    def labels(s):
        return ["bad"] if s in {4,5} else []
    model = sv.bird.build_bird(delta, init=0, labels=labels, modeltype=sv.ModelType.DTMC)
    problem = from_stormvogel_problem(model, lambda_=lambda_, bad_label="bad")
    return problem

def problematic(lambda_):
    DELTA = {
        0: [(1, 1)],
        1: [(0.3, 0), (0.3, 2), (0.4, 3)],
        2 : [(1,2)],
        3 : [(1,3)]
    }
    delta = lambda s : DELTA[s]
    labels = lambda s : ["bad"] if s == 2 else []
    model = sv.bird.build_bird(delta, init=0, labels=labels, modeltype=sv.ModelType.DTMC)
    problem = from_stormvogel_problem(model, lambda_=lambda_, bad_label="bad")
    return problem