# EXAMPLE 23
S = [0,1,2,3]
P_DICT = {
    0 : {'a': {0: 1, 1: 0, 2: 0, 3: 0},
         'b': {0: 0, 1: 1/2, 2: 1/2, 3: 0}},
    1 : {'a': {0: 1/3, 1: 0, 2: 0, 3: 2/3}},
    2 : {'b': {0: 0, 1: 0, 2: 1, 3: 0}},
    3 : {'a': {0: 0, 1: 0, 2: 0, 3: 1}}}
def P(s,a,s_):
    return P_DICT[s][a][s_]
def available_actions(s):
    if s == 0:
        return ['a','b']
    elif s == 2:
        return ['b']
    else:
        return ['a']
        
B = {3}
PROP = [2/5,1,1,1]
ZETA = {0: 'a', 1: 'a', 2: 'b', 3: 'a'}
XI = {0: 'b', 1: 'a', 2: 'b', 3: 'a'}
zeta = lambda s : ZETA[s]
xi = lambda s : XI[s]
def possible_policies(): # TODO refactor to use arg max so you don't need this stupid function anymore.
    return [xi, zeta]
# END EXAMPLE 23