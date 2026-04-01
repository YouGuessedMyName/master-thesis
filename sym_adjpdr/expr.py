from dataclasses import dataclass
from fractions import Fraction

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
        left = self.left.eval()
        right = self.right.eval()
        if isinstance(left, Const) and isinstance(right, Const):
            return Const(left.value / right.value)
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