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

def to_indicator_function(s: isl.Set, constant_val: int = 1) -> isl.PwAff:
    restricted_one = isl.PwAff.val_on_domain(s, isl.Val(constant_val))
    zeroes = isl.PwAff.zero_on_domain(s.space)
    res = zeroes.union_add(restricted_one)
    return res

class Model:
    # For now support only DTMC
    vars: Vars
    bad: isl.Set
    factor: int
    module: Module
    ctx: isl.Context
    prop: Frame
    isl_commands_phi: list[tuple[isl.Set, list[isl.Aff, isl.PwMultiAff]]]
    # The Set is a guard, the Aff is a probability value, the Map is the substitution itself.
    isl_commands_theta: list[tuple[isl.Set, list[isl.Aff, isl.MultiAff, isl.MultiAff]]]
    # Forward and backward substitutions.

    def __init__(self, module: Module, max_prob: Fraction, initial_state: dict[str, Fraction] | None = None):
        
        self.vars = module.variables
        # TODO for now we only support properties of the form Not (And [expr...])
        assert type(module.prop) == Not
        expr = module.prop.expr
        assert type(expr) == And
        conjuncts = expr.exprs
        self.bad = conjuncts_to_isl_set(module.variables, conjuncts, False)
        
        self.factor = module.lcm
        self.module = module

        self.ctx = isl.Context()

        #self.bad_frame = Frame.from_pieces(self.ctx, self.vars, [(self.bad, Fraction(1))])
        if initial_state is None:
            initial_state = {v: Fraction(0) for v in module.variables}
        initial_state_set = isl.Set.read_from_str(self.ctx, "{ [" + ",".join(k + "=" +  str(v) for k,v in initial_state.items()) + "] }")
        self.prop = Frame.from_pieces(self.ctx, self.vars, [(initial_state_set, max_prob)], default_val=Fraction(1))
        self.__initialize_isl_commands_phi()
        self.__initialize_isl_commands_theta()

    def __initialize_isl_commands_phi(self):
        self.isl_commands_phi = []
        for command in self.module.commands:
            guard = conjuncts_to_isl_set(self.vars, command.guards, False).subtract(self.bad)
            isl_branch = []
            for p, updates in command.branches:
                assert len(updates) == len(self.vars)
                update_strs = []
                for update in updates:
                    update_strs.append(expr_to_isl_string(update.new_val))
                update_str = ",".join(update_strs)
                final_map_str = "{ [" + ",".join(self.vars) + "] -> [" + update_str + "] }" 
                mp = isl.Map(final_map_str).as_pw_multi_aff().coalesce()
                isl_p = isl.Val(frac_to_isl(p))
                mulAff_p = isl.Aff.val_on_domain(guard.space, isl_p)
                isl_branch.append((mulAff_p, mp))
            self.isl_commands_phi.append((guard, isl_branch))

    def __initialize_isl_commands_theta(self):
        # This will only work if constants are properly folded!!!
        self.isl_commands_theta = []
        for command in self.module.commands:
            guard = conjuncts_to_isl_set(self.vars, command.guards, False).subtract(self.bad)
            isl_branch_rev = []
            for p, updates in command.branches:
                assert len(updates) == len(self.vars)
                update_strs = []
                for update in updates:
                    update_strs.append(expr_to_isl_string(update.new_val))
                update_str = ",".join(update_strs)
                final_map_str = "{ [" + ",".join(self.vars) + "] -> [" + update_str + "] }"
                # original
                mp = isl.Map(final_map_str).as_pw_multi_aff().coalesce()
                isl_p = isl.Val(frac_to_isl(p))
                mulAff_p = isl.Aff.val_on_domain(guard.space, isl_p)
                # reversed
                mp_rev = isl.Map(final_map_str).reverse().as_pw_multi_aff().coalesce()
                isl_p_rev = isl.Val(frac_to_isl(p))
                isl_branch_rev.append((mulAff_p, mp, mp_rev))
            self.isl_commands_theta.append((guard, isl_branch_rev))

    @staticmethod
    def from_prism_file(path: str, max_prob: Fraction, set_expected_result: bool = True):
        with open(path, "r") as f:
            prism_str = f.read()
        tree = prism_parser.parse(prism_str)
        module: Module = PrismTransformer().transform(tree)
        module.set_property()
        if set_expected_result:
            module.set_expected_result(path)
        module.clear_constants()
        return Model(module, max_prob)
    
    def Phi(self, F: Frame) -> Frame:
        result_pwaff = to_indicator_function(self.bad)
        for isl_guard, isl_branch in self.isl_commands_phi:
            guard_update_pwaff = None
            for mulAff_p, mp in isl_branch:
                mappedF = F.pw.pullback_pw_multi_aff(mp).intersect_domain(F.domain).coalesce()
                multid = mappedF.mul(mulAff_p)
                guard_update_pwaff = multid if guard_update_pwaff is None else guard_update_pwaff.union_add(multid)
                # TODO should I use union add here or not?
            
            guarded_update_pwaff = guard_update_pwaff.intersect_domain(isl_guard)
            result_pwaff = result_pwaff.union_add(guarded_update_pwaff)
                
        return Frame(result_pwaff.intersect_domain(F.domain).coalesce(), F.domain, F.variables, F.factor)
    
    def Theta(self, F: Frame) -> Frame:
        result_pwaff = isl.PwAff.zero_on_domain(F.domain.space)
        for isl_guard, isl_branch in self.isl_commands_theta:
            guard_update_pwaff = None
            for mulAff_p, mp, mp_rev in isl_branch:
                mappedF = F.pw.pullback_pw_multi_aff(mp_rev).intersect_domain(F.domain).coalesce()
                multid = mappedF.mul(mulAff_p)
                guard_update_pwaff = multid if guard_update_pwaff is None else guard_update_pwaff.union_add(multid)
                print()
            # We need to intersect with the substituted guard?
            # Yes, but the phi way...
            substituted_guard = isl_guard.apply(mp.as_map())
            guarded_update_pwaff = guard_update_pwaff.intersect_domain(substituted_guard)
            result_pwaff = result_pwaff.union_add(guarded_update_pwaff)
            print()
        return Frame(result_pwaff.intersect_domain(F.domain).coalesce(), F.domain, F.variables, F.factor)
    
    def __str__(self) -> str:
        return f"""DTMC Model
  Prop: {self.prop}
  Bad: {self.bad}
  Vars: {self.vars}"""
        
