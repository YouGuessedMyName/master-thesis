from sym_adjpdr.prism import *
from sym_adjpdr.model import *

PATH = "prism/line.prism"

with open(PATH, "r") as f:
    PRISM = f.read()

tree = prism_parser.parse(PRISM)
# print(tree.pretty())
module: Module = PrismTransformer().transform(tree)
print(module)
module.set_property()
module.set_expected_result(PATH)
module.clear_constants()
print(module)
model = Model(module)
