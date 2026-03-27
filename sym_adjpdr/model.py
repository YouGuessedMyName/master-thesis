from typing import Callable

from sym_adjpdr.frames import *
from sym_adjpdr.prism import *
import islpy as isl

def conjuncts_to_isl_set(vars: dict[str, tuple[Expr, Expr]], conjuncts: list[Expr]) -> isl.Set:
    """
    Convert a list of conjunct expressions into an isl.Set over the variables.
    vars: dictionary mapping variable name -> (lower_bound_expr, upper_bound_expr)
    conjuncts: list of Expr objects (typically from Not(And([...])) )
    """
    # Build the list of variable names
    var_names = list(vars.keys())
    
    # Convert each conjunct to an ISL string
    def expr_to_isl_string(e: Expr) -> str:
        if isinstance(e, Var):
            return e.name
        elif isinstance(e, Const):
            return str(e.value)
        elif isinstance(e, Add):
            return f"({expr_to_isl_string(e.left)} + {expr_to_isl_string(e.right)})"
        elif isinstance(e, Sub):
            return f"({expr_to_isl_string(e.left)} - {expr_to_isl_string(e.right)})"
        elif isinstance(e, Mul):
            return f"({expr_to_isl_string(e.left)} * {expr_to_isl_string(e.right)})"
        elif isinstance(e, Div):
            return f"({expr_to_isl_string(e.left)} / {expr_to_isl_string(e.right)})"
        elif isinstance(e, Eq):
            return f"{expr_to_isl_string(e.left)} = {expr_to_isl_string(e.right)}"
        elif isinstance(e, Lt):
            return f"{expr_to_isl_string(e.left)} < {expr_to_isl_string(e.right)}"
        else:
            raise NotImplementedError(f"Cannot convert {type(e)} to ISL")

    # Build the list of constraints
    constraints = []

    # Add variable bounds first
    for name, (lb, ub) in vars.items():
        constraints.append(f"{expr_to_isl_string(lb)} <= {name}")
        constraints.append(f"{name} <= {expr_to_isl_string(ub)}")

    # Add the conjunct expressions
    for c in conjuncts:
        constraints.append(expr_to_isl_string(c))

    # Combine constraints with 'and'
    constraints_str = " and ".join(constraints)

    # Create the ISL set
    isl_set_str = f"{{[{','.join(var_names)}] : {constraints_str}}}"
    return isl.Set(isl_set_str)

class Model:
    # For now support only DTMC
    vars: Vars
    phi: Callable[[Frame], Frame]
    prop: Frame

    def __init__(self, module: Module):
        self.vars = module.variables
        # TODO for now we only support properties of the form Not (And [expr...])
        assert type(module.prop) == Not
        expr = module.prop.expr
        assert type(expr) == And
        conjuncts = expr.exprs
        self.prop = conjuncts_to_isl_set(module.variables, conjuncts)

        # Now extract Phi, the hard part!
        
