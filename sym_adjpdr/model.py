from typing import Callable

from sym_adjpdr.frames import *
from sym_adjpdr.prism import *
import islpy as isl

# Convert each conjunct to an ISL string
def expr_to_isl_string(e: Expr, invert: bool = False) -> str:
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
    elif isinstance(e, And):
        if invert:
            raise NotImplementedError(f"Cannot convert {type(e)} to ISL")
        return " and ".join(expr_to_isl_string(e_) for e_ in e.exprs)
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

def join_maps_with_priority(map1: isl.Map, map2: isl.Map) -> isl.Map:
    """
    Combine two isl.Maps giving priority to map1.
    Any inputs in map1 will override map2.
    """
    # Remove inputs already in map1
    map2_only = map2.intersect_domain(map1.domain().complement())
    
    # Union with map1 (which has priority)
    combined = map1.union(map2_only).coalesce()
    return combined

class Model:
    # For now support only DTMC
    vars: Vars
    bad: Frame
    prop: Frame
    map: isl.PwMultiAff
    factor: int

    def __init__(self, module: Module, bad_label: str = "bad"):
        self.vars = module.variables
        # TODO for now we only support properties of the form Not (And [expr...])
        assert type(module.prop) == Not
        expr = module.prop.expr
        assert type(expr) == And
        conjuncts = expr.exprs
        self.bad = conjuncts_to_isl_set(module.variables, conjuncts, False)
        self.prop = conjuncts_to_isl_set(module.variables, conjuncts, True)
        self.map = self.__create_map(module, bad_label)
        self.factor = module.lcm
    
    # @staticmethod
    # def __create_map(module: Module) -> isl.Map:
    #     var_part = "[" + ",".join(module.variables) + "] -> "
    #     pieces = []
    #     for m in module.commands:
    #         guard = m.guards[0]
    #         guard_pieces = []
    #         for i in range(len(module.variables)):
    #             i_updates_strings = []
    #             for p,us in m.branches:
    #                 assert len(us) == len(module.variables)
    #                 u = us[i]
    #                 updates_str = str(p*module.lcm) + " * " + expr_to_isl_string(u.new_val)
    #                 i_updates_strings.append(updates_str)
    #             i_updates_str = " + ".join(i_updates_strings)
    #             guard_pieces.append(i_updates_str)
    #         updates_str = ", ".join(guard_pieces)
    #         isl_guard = expr_to_isl_string(guard, False)
    #         isl_subst = var_part + "[" + updates_str + "]"
    #         map_part = isl_subst + " : " + isl_guard
    #         pieces.append(map_part)
    #     res = "{ " + "; ".join(pieces) + " }"
    #     mp = isl.Map(res).as_pw_multi_aff().coalesce()
    #     return mp

    @staticmethod
    def __create_commands_map_string(module: Module, commands):
        lhs_variables = "[" + ",".join(module.variables) + "] -> "
        map_pieces = []
        for command in module.commands:
            for guard_expr in command.guards:
                # Convert the guard expression to ISL string
                isl_guard_str = expr_to_isl_string(guard_expr)

                # Build update expressions for all variables
                update_expressions = []
                for var_index, var_name in enumerate(module.variables):
                    branch_updates = []
                    for probability, updates in command.branches:
                        assert len(updates) == len(module.variables), "Mismatch in number of updates"
                        update = updates[var_index]
                        branch_expr_str = f"{probability * module.lcm} * {expr_to_isl_string(update.new_val)}"
                        branch_updates.append(branch_expr_str)

                    # Combine all branches for this variable
                    combined_var_update = " + ".join(branch_updates)
                    update_expressions.append(combined_var_update)

                # Form the update vector for this guard
                updates_vector_str = ", ".join(update_expressions)
                map_piece_str = f"{lhs_variables}[{updates_vector_str}] : {isl_guard_str}"
                map_pieces.append(map_piece_str)
        return "{ " + "; ".join(map_pieces) + "} "
    
    @staticmethod
    def __create_map(module: Module, bad_label: str) -> isl.Map:
        """
        Build an isl.Map representing all updates of a PRISM module.
        
        Each command may have multiple guards. Each guard is converted to a piecewise mapping:
            [x1, x2, ...] -> [update_x1, update_x2, ...] : guard
        Probabilistic branches are weighted by module.lcm.
        """
        # Construct the left-hand side variable vector: [x1, x2, ...]
        lhs_variables = "[" + ",".join(module.variables) + "] -> "
        bad_expression = And(module.labels[bad_label])
        
        bad_label_str = "{" + f"{lhs_variables}[{module.lcm}] : {expr_to_isl_string(bad_expression)}" + "}"
        bad_label_map = isl.Map(bad_label_str)
        transition_str = Model.__create_commands_map_string(module, module.commands)
        transition_map = isl.Map(transition_str)

        isl_map = join_maps_with_priority(bad_label_map, transition_map)
        final_map = isl_map.as_pw_multi_aff().coalesce()
        return isl_map.as_pw_multi_aff().coalesce()

    def Phi(self, F: Frame) -> Frame:
        assert F.factor == self.factor
        new_frame = Frame(F.pw.pullback_pw_multi_aff(self.map).intersect_domain(F.domain).coalesce(), F.domain, F.variables, F.factor)
        return new_frame
    
    def __str__(self) -> str:
        return f"""DTMC Model
  Prop: {self.prop}
  Bad: {self.bad}
  Vars: {self.vars}"""
        
