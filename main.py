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
model = Model(module)
print(model)

ctx = isl.Context()
F = Frame.zero(ctx, model.vars, model.factor)
F = Frame.from_pieces(ctx, model.vars, [(isl.Set.read_from_str(ctx, "{ [x] : x = 2 }"), Fraction(model.factor))], model.factor)
Phi_F = model.Phi(F)
Phi_Phi_F = model.Phi(Phi_F)
print("F", F)
print("Phi(F)", Phi_F)
print("Phi(Phi(F))", Phi_Phi_F)