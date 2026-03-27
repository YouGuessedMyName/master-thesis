"""Parsing/lexing and AST for PRISM with custom expressions."""
from dataclasses import dataclass
from fractions import Fraction
import stormvogel as sv
import stormpy

type Vars = dict[str, tuple[int, int]] # Represents a variable with a name and a domain.

from lark import Lark, Transformer

with open("adjpdr/grammar.ebnf", "r") as f:
    GRAMMAR = f.read()

prism_parser = Lark(GRAMMAR, start="start")

# === Custom expression types ===
# === Custom expression types with pretty-printing ===
class Expr:
    def substitute(self, name: str, value):
        return self

    def __str__(self):
        return "<expr>"
    
    def eval(self):
        """Evaluate subexpressions with no free variables. Return simplified Expr."""
        return self

@dataclass
class Var(Expr):
    name: str

    def substitute(self, name: str, value):
        return value if self.name == name else self

    def __str__(self):
        return self.name

    def eval(self):
        # Cannot evaluate free variable
        return self

@dataclass
class Const(Expr):
    value: Fraction

    def __str__(self):
        return str(self.value)
    
    def eval(self):
        # Constant evaluates to itself
        return self

@dataclass
class Add(Expr):
    left: Expr
    right: Expr

    def substitute(self, name: str, value):
        return Add(self.left.substitute(name, value), self.right.substitute(name, value))

    def __str__(self):
        return f"({self.left} + {self.right})"
    
    def eval(self):
        left = self.left.eval()
        right = self.right.eval()
        if isinstance(left, Const) and isinstance(right, Const):
            return Const(left.value + right.value)
        return Add(left.eval(), right.eval())

@dataclass
class Sub(Expr):
    left: Expr
    right: Expr

    def substitute(self, name: str, value):
        new_left = self.left.substitute(name, value)
        new_right = self.right.substitute(name, value)
        return Sub(new_left, new_right)

    def __str__(self):
        return f"({self.left} - {self.right})"
    
    def eval(self):
        left = self.left.eval()
        right = self.right.eval()
        if isinstance(left, Const) and isinstance(right, Const):
            return Const(left.value - right.value)
        return Sub(left.eval(), right.eval())

@dataclass
class Mul(Expr):
    left: Expr
    right: Expr

    def substitute(self, name: str, value):
        return Mul(self.left.substitute(name, value), self.right.substitute(name, value))

    def __str__(self):
        return f"({self.left} * {self.right})"
    
    def eval(self):
        left = self.left.eval()
        right = self.right.eval()
        if isinstance(left, Const) and isinstance(right, Const):
            return Const(left.value - right.value)
        return Mul(left.eval(), right.eval())

@dataclass
class Div(Expr):
    left: Expr
    right: Expr

    def substitute(self, name: str, value):
        return Div(self.left.substitute(name, value), self.right.substitute(name, value))

    def __str__(self):
        return f"({self.left} / {self.right})"
    
    def eval(self):
        return Div(self.left.eval(), self.right.eval())

@dataclass
class Eq(Expr):
    left: Expr
    right: Expr

    def substitute(self, name: str, value):
        return Eq(self.left.substitute(name, value), self.right.substitute(name, value))

    def __str__(self):
        return f"({self.left} == {self.right})"
    
    def eval(self):
        return Eq(self.left.eval(), self.right.eval())

@dataclass
class Lt(Expr):
    left: Expr
    right: Expr

    def substitute(self, name: str, value):
        return Lt(self.left.substitute(name, value), self.right.substitute(name, value))

    def __str__(self):
        return f"({self.left} < {self.right})"
    
    def eval(self):
        return Lt(self.left.eval(), self.right.eval())

@dataclass
class Not(Expr):
    expr: Expr

    def substitute(self, name: str, value):
        return Not(self.expr.substitute(name, value))

    def __str__(self):
        return f"!( {self.expr} )"
    
    def eval(self):
        return Not(self.expr.eval())

@dataclass
class And(Expr):
    exprs: list[Expr]

    def substitute(self, name: str, value):
        return And([e.substitute(name, value) for e in self.exprs])

    def __str__(self):
        return " & ".join(f"({e})" for e in self.exprs)
    
    def eval(self):
        return And([e.eval() for e in self.exprs])

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
    expected_result: float

    def clear_constants(self):
        """Replace constants in variables, guards, branches, labels, and property."""
        for cname, cval in self.constants.items():
            const_expr = cval
            # Update variable bounds
            for name, (lb, ub) in self.variables.items():
                self.variables[name] = int(lb.substitute(cname, cval).eval().value), int(ub.substitute(cname, cval).eval().value)
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
                    new_branches.append((prob, new_updates))
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
        return "\n".join(lines)

# === Transformer ===
class PrismTransformer(Transformer):
    def start(self, items):
        _model_type, constants, module, labels = items
        module.constants = constants
        module.labels = labels
        return module

    # Constants
    def constants(self, items):
        return {k: v for k, v in items}

    def constant(self, items):
        return items[0], items[1]

    # Module
    def module(self, items):
        name, vars, commands = items
        return Module(name, None, vars, commands, None, None, None)

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
        return Div(items[0], items[1])
    