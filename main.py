from sym_adjpdr.prism import *
from sym_adjpdr.frames import *

PATH = "prism/line.prism"

with open(PATH, "r") as f:
    PRISM = f.read()

tree = prism_parser.parse(PRISM)
# print(tree.pretty())
module: Module = PrismTransformer().transform(tree)
module.set_property()
module.set_expected_result(PATH)
module.clear_constants()
# print_module(module)

ctx = isl.Context()
vars = {"x": (0, 5), "y": (1, 3)}
print(make_domain(isl.Context(), vars))