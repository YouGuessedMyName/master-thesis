from typing import Callable

from sym_adjpdr.frames import *
from sym_adjpdr.prism import *
import islpy as isl

# Convert each conjunct to an ISL string
def expr_to_isl_string(e: Expr, invert: bool) -> str:
    if isinstance(e, Var):
        return e.name
    elif isinstance(e, Const):
        return str(e.value)
    elif isinstance(e, Add):
        return f"({expr_to_isl_string(e.left, invert)} + {expr_to_isl_string(e.right, invert)})"
    elif isinstance(e, Sub):
        return f"({expr_to_isl_string(e.left, invert)} - {expr_to_isl_string(e.right, invert)})"
    elif isinstance(e, Mul):
        return f"({expr_to_isl_string(e.left, invert)} * {expr_to_isl_string(e.right, invert)})"
    elif isinstance(e, Div):
        return f"({expr_to_isl_string(e.left, invert)} / {expr_to_isl_string(e.right, invert)})"
    elif isinstance(e, Eq):
        if invert:
            return f"{expr_to_isl_string(e.left, invert)} != {expr_to_isl_string(e.right, invert)}"
        return f"{expr_to_isl_string(e.left, invert)} = {expr_to_isl_string(e.right, invert)}"
    elif isinstance(e, Lt):
        if invert:
            return f"{expr_to_isl_string(e.left, invert)} >= {expr_to_isl_string(e.right, invert)}"
        return f"{expr_to_isl_string(e.left, invert)} < {expr_to_isl_string(e.right, invert)}"
    else:
        raise NotImplementedError(f"Cannot convert {type(e)} to ISL")

def conjuncts_to_isl_set(vars: dict[str, tuple[int, int]], conjuncts: list[Expr], invert: bool) -> isl.Set:
    """
    Convert a list of conjunct expressions into an isl.Set over the variables.
    vars: dictionary mapping variable name -> (lower_bound_expr, upper_bound_expr)
    conjuncts: list of Expr objects (typically from Not(And([...])) )
    """
    # Build the list of variable names
    var_names = list(vars.keys())

    # Build the list of constraints
    constraints = []

    # Add variable bounds first
    for name, (lb, ub) in vars.items():
        constraints.append(f"{lb} <= {name}")
        constraints.append(f"{name} <= {ub}")

    # Add the conjunct expressions
    for c in conjuncts:
        constraints.append(expr_to_isl_string(c, invert))

    # Combine constraints with 'and'
    constraints_str = " and ".join(constraints)

    # Create the ISL set
    isl_set_str = f"{{[{','.join(var_names)}] : {constraints_str}}}"
    return isl.Set(isl_set_str)

class Model:
    # For now support only DTMC
    vars: Vars
    bad: Frame
    prop: Frame

    def __init__(self, module: Module):
        self.vars = module.variables
        # TODO for now we only support properties of the form Not (And [expr...])
        assert type(module.prop) == Not
        expr = module.prop.expr
        assert type(expr) == And
        conjuncts = expr.exprs
        self.bad = conjuncts_to_isl_set(module.variables, conjuncts, False)
        self.prop = conjuncts_to_isl_set(module.variables, conjuncts, True)

    def Phi(self, F: Frame) -> Frame:
        # TODO for now we don't support probabilistic choices, just substitution :DD
        for set,aff in F.pw.get_pieces():
            print("set", set, "aff", aff) # use isl.Map instead!
    
    def __str__(self) -> str:
        return f"""DTMC Model
  Prop: {self.prop}
  Bad: {self.bad}
  Vars: {self.vars}"""
        
