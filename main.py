from adjpdr.prism import *

with open("prism/grid.prism", "r") as f:
    PRISM = f.read()

tree = prism_parser.parse(PRISM)
# print(tree.pretty())
ast = PrismTransformer().transform(tree)
print_ast(ast)