from sym_adjpdr.prism import *
from sym_adjpdr.model import *

PATH = "prism/probline.prism"

with open(PATH, "r") as f:
    PRISM = f.read()

tree = prism_parser.parse(PRISM)
# print(tree.pretty())
module: Module = PrismTransformer().transform(tree)
module.set_property()
module.set_expected_result(PATH)
module.clear_constants()
print(module)
model = Model(module, max_prob=Fraction(9,10))
print(model)

ctx = isl.Context()
F = Frame.zero(ctx, model.vars)
F = Frame.from_pieces(ctx, model.vars, [
    (isl.Set.read_from_str(ctx, "{ [x] : x = 2 }"), Fraction(1)),
    (isl.Set.read_from_str(ctx, "{ [x] : x = 1 }"), Fraction(1,2))
    ])
Phi_F = model.Phi(F)
Phi_Phi_F = model.Phi(Phi_F)
print("F", F)
print("Phi(F)", Phi_F)
# print("Phi(Phi(F))", Phi_Phi_F)

def apply(f, n, arg):
    """Apply f n times to arg."""
    return arg if n <= 0 else f(apply(f, n-1, arg)) 