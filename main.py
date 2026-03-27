from sym_adjpdr.prism import *
from sym_adjpdr.model import *

PATH = "prism/line.prism"

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
F = Frame.zero(ctx, model.vars)
F = Frame.from_pieces(ctx, model.vars, [(isl.Set.read_from_str(ctx, "{ [x] : x = 2 }"), Fraction(1))])
print("F", F)
print("Phi(F)", model.Phi(F))