"""Parsing/lexing and AST for PRISM."""
from dataclasses import dataclass
from fractions import Fraction
import stormvogel as sv
import stormpy
from sym_adjpdr.frames import *
import islpy as isl

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
    branches: set[tuple[Fraction, list[Update]]]

@dataclass
class Module:
    name: str
    constants: dict[str, int]
    variables: Vars
    commands: set[Command]
    labels: dict[str, set[z3.BoolRef]]
    prop: z3.BoolRef
    expected_result: float

    def clear_constants(self):
        for cname, cval in self.constants.items():
            for name, (lb, ub) in self.variables.items():
                self.variables[name] = simpl_subst(lb, cname, cval), simpl_subst(ub, cname, cval)
            for c in self.commands:
                c.guards = set(simpl_subst(e, cname, cval) for e in c.guards)
                new_branches = []
                for val, updates in c.branches:
                    new_branches.append((val,
                        [Update(simpl_subst(update.variable, cname, cval), simpl_subst(update.new_val, cname, cval)) 
                            for update in updates]))
            for lname, guards in self.labels.items():
                self.labels[lname] = [simpl_subst(e, cname, cval) for e in guards]
            if self.prop is not None:
                self.prop = simpl_subst(self.prop,cname,cval)

    def set_property(self, bad_label: str = "bad"):
        self.prop = z3.Not(z3.And(self.labels[bad_label]))
        
    def set_expected_result(self, prism_path:str, bad_label: str = "bad"):
        prism_program = stormpy.parse_prism_program(prism_path)
        sv_model = sv.stormpy_utils.from_prism(prism_program)
        self.expected_result = sv.model_checking(sv_model, f'Pmax=? [F "{bad_label}"]').get_result_of_state(0)
        

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
        return Module(name, None, vars, commands, None, None, None)
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
        return (Fraction(prob), updates)

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
        return str(t)
    def VAR(self, t):
        return z3.Int(t[0])
    def add(self, items):
        return items[0] + items[1]
    def sub(self, items):
        return items[0] - items[1]
    def mult(self, items):
        return items[0] * items[1]
    def div(self, items):
        return items[0] / items[1]

def print_module(module: Module):
    print([module.name])
    print("Constants:", module.constants)
    print("Vars:", module.variables)
    print("Commands:")
    for command in module.commands:
        print(command)
    print("Labels", module.labels)
    print("Prop", module.prop)
    print("Expected result", module.expected_result)

