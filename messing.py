from sym_adjpdr.prism import *

e = Eq(left=Var(name='x'), right=Sub(left=Var(name='N'), right=Const(value=Fraction(1, 1))))

print([e])
e_ = e.substitute('N', 4)
print([e_])