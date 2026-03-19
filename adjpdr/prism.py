from dataclasses import dataclass
from adjpdr.helpers import Frac

from lark import Lark, Transformer
import z3

with open("adjpdr/grammar.ebnf", "r") as f:
    GRAMMAR = f.read()

prism_parser = Lark(GRAMMAR, start="start")

@dataclass
class Update:
    variable: z3.Int
    new_val: z3.ArithRef

@dataclass
class Command:
    guards: set[z3.BoolRef]
    branches: set[tuple[Frac, Update]]

@dataclass
class Module:
    name: str
    constants: dict[str, int]
    variables: dict[z3.Int, tuple[z3.Int, z3.Int]]
    commands: set[Command]
    labels: dict[str, set[z3.BoolRef]]

class PrismTransformer(Transformer):
    def start(self, items):
        _model_type, constants, module, labels = items
        module.constants = constants
        module.labels = labels
        return module
    
    # Constants
    def constants(self, items):
        return {k:v for (k,v) in items}
    def constant(self, items):
        return (items[0], items[1])

    # Module
    def module(self, items):
        name, vars, commands = items
        return Module(name, {}, vars, commands, {})
    def vars(self, items):
        return {k:v for k,v in items}
    def var(self, items):
        name, lb, ub = items
        return name, (lb, ub)

    def commands(self, items):
        return items
    def command(self, items):
        guards, branches = items
        return Command(guards, branches)
    
    def guards(self, items):
        return items
    
    def branches(self, items):
        return items
    def branch(self, items):
        prob, updates = items
        return (Frac(prob), updates)

    def updates(self, items):
        return items
    def update(self, items):
        return Update(items[0], items[1])
    
    # Labels
    def labels(self, items):
        return {k:v for (k,v) in items}
    def label(self, items):
        name, expr = items
        return (name, expr)
    
    # Boolean terms
    def bool_term(self, items):
        return items
    def eq(self, items):
        return items[0] == items[1]
    def lt(self, items):
        return items[0] < items[1]

    # Expressions
    def NUMBER(self, t):
        return int(t)
    def INT(self, t):
        return int(t)
    def NAME(self, t):
        return z3.Int(t)
    def add(self, items):
        return items[0] + items[1]
    def sub(self, items):
        return items[0] - items[1]
    def mult(self, items):
        return items[0] * items[1]
    def div(self, items):
        return items[0] / items[1]

def print_ast(module: Module):
    print(module.name)
    print("Constants:", module.constants)
    print("Vars:", module.variables)
    print("Commands:")
    for command in module.commands:
        print(command)
    print("Labels", module.labels)