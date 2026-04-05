"""Parsing/lexing and AST for PRISM with custom expressions."""
from dataclasses import dataclass
from fractions import Fraction
import stormvogel as sv
import stormpy
import math
from sym_adjpdr.expr import *

type Vars = dict[str, tuple[int, int]] # Represents a variable with a name and a domain.

from lark import Lark, Transformer

with open("sym_adjpdr/grammar.ebnf", "r") as f:
    GRAMMAR = f.read()

prism_parser = Lark(GRAMMAR, start="start")

# === AST structures ===
@dataclass
class Update:
    variable: Var
    new_val: Expr

@dataclass
class Command:
    guards: set[Expr]
    branches: set[tuple[Fraction, list[Update]]]

@dataclass
class Module:
    name: str
    constants: dict[str, Fraction]
    variables: Vars
    commands: set[Command]
    labels: dict[str, set[Expr]]
    prop: Expr
    lcm: int
    expected_result: float

    def clear_constants(self):
        """Replace constants in variables, guards, branches, labels, and property."""
        iterates = list(self.constants.items()) + [("undefined", -1)] if len(self.constants) == 0 else list(self.constants.items())
        for cname, cval in iterates: # TODO hack
            const_expr = cval
            # Update variable bounds
            for name, (lb, ub) in self.variables.items():
                try:
                    self.variables[name] = int(lb.substitute(cname, cval).eval().value), int(ub.substitute(cname, cval).eval().value)
                except:
                    pass # TODO we need to separate replacing from eval...
            # Update commands
            for c in self.commands:
                c.guards = [g.substitute(cname, cval).eval() for g in c.guards]
                new_branches = []
                for prob, updates in c.branches:
                    new_updates = [
                        Update(u.variable.substitute(cname, cval).eval(),
                               u.new_val.substitute(cname, cval).eval())
                        for u in updates
                    ]
                    new_branches.append((prob.eval().value, new_updates))
                c.branches = new_branches
            # Update labels
            for lname, guards in self.labels.items():
                self.labels[lname] = [g.substitute(cname, cval).eval() for g in guards]
            # Update property
            if self.prop is not None:
                self.prop = self.prop.substitute(cname, const_expr).eval()

    def set_property(self, bad_label: str = "bad"):
        self.prop = Not(And(list(self.labels[bad_label])))

    def set_expected_result(self, prism_path: str, bad_label: str = "bad"):
        prism_program = stormpy.parse_prism_program(prism_path)
        sv_model = sv.stormpy_utils.from_prism(prism_program)
        self.expected_result = sv.model_checking(sv_model, f'Pmax=? [F "{bad_label}"]').get_result_of_state(0)
    
    def __str__(self):
        lines = [f"Module: {self.name}"]
        if self.constants:
            lines.append("  Constants:")
            for k, v in self.constants.items():
                lines.append(f"    {k} = {v}")
        if self.variables:
            lines.append("  Variables:")
            for k, (lb, ub) in self.variables.items():
                lines.append(f"    {k} in [{lb}, {ub}]")
        if self.commands:
            lines.append("  Commands:")
            for c in self.commands:
                guards_str = " & ".join(str(g) for g in c.guards)
                lines.append(f"    Guards: {guards_str}")
                for prob, updates in c.branches:
                    updates_str = ", ".join(f"{u.variable} := {u.new_val}" for u in updates)
                    lines.append(f"      [{prob}] -> {updates_str}")
        if self.labels:
            lines.append("  Labels:")
            for lname, guards in self.labels.items():
                guards_str = " & ".join(str(g) for g in guards)
                lines.append(f"    {lname}: {guards_str}")
        if self.prop is not None:
            lines.append(f"  Property: {self.prop}")
        if self.expected_result is not None:
            lines.append(f"  Expected result: {self.expected_result}")
        lines.append(f"  LCM: {self.lcm}")
        return "\n".join(lines)

# === Transformer ===
class PrismTransformer(Transformer):
    denominators: list[int] = []

    def start(self, items):
        _model_type, constants, module, labels = items
        module.constants = constants
        module.labels = labels
        module.lcm = math.lcm(* self.denominators)
        return module

    # Constants
    def constants(self, items):
        return {k: v for k, v in items}

    def constant(self, items):
        return items[0], items[1]

    # Module
    def module(self, items):
        name, vars, commands = items
        return Module(name, None, vars, commands, None, None, 0, None)

    def vars(self, items):
        return {k: v for k, v in items}

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
        return prob, updates

    def updates(self, items):
        return items

    def update(self, items):
        return Update(items[0], items[1])

    # Labels
    def labels(self, items):
        return {k: v for k, v in items}

    def label(self, items):
        name, expr = items
        return name, expr

    # Boolean terms
    def bool_term(self, items):
        return items[0] if len(items) == 1 else And(items)

    def eq(self, items):
        return Eq(items[0], items[1])

    def lt(self, items):
        return Lt(items[0], items[1])

    # Expressions
    def NUMBER(self, t):
        return Const(Fraction(t))

    def INT(self, t):
        return Const(Fraction(t))

    def NAME(self, t):
        return str(t)

    def VAR(self, t):
        return Var(str(t))

    def add(self, items):
        return Add(items[0], items[1])

    def sub(self, items):
        return Sub(items[0], items[1])

    def mult(self, items):
        return Mul(items[0], items[1])

    def div(self, items):
        if type(items[1]) == Const:
            self.denominators.append(int(items[1].value))
        return Div(items[0], items[1])
    