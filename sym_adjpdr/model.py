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

def to_indicator_function(s: isl.Set, domain: isl.Set, constant_val: int = 1) -> isl.PwAff:
    restricted_one = isl.PwAff.val_on_domain(s, isl.Val(constant_val))
    zeroes = isl.PwAff.zero_on_domain(s.space)
    res = restricted_one.union_add(zeroes).intersect_domain(domain)
    return res.coalesce()

class Model:
    # For now support only DTMC
    vars: Vars
    bad: isl.Set
    factor: int
    module: Module
    ctx: isl.Context
    prop: Frame
    isl_commands_phi: list[tuple[isl.Set, list[tuple[isl.Aff, isl.PwMultiAff]]]]
    # The Set is a guard, the Aff is a probability value, the PwMultiAff is the substitution itself.
    # Note that for the Phi operator, we explicitly exclude the bad states from the guards.
    isl_commands_theta: list[tuple[isl.Set, list[tuple[isl.Aff, bool, isl.PwAff | isl.PwMultiAff]]]]
    # Similarly here, the Set is a guard, the Aff is a probability value.
    # The boolean is true when it is a constant update and false when it is an invertible update.
    # If it is constant and u(s)=s', then the isl.PwAff maps s' to 1 and all else to 0.
    # Otherwise, the isl.MultiAff is a reversed update.
    domain: isl.Set
    bad_frame: Frame
    ctx: isl.Context
    max_prob: Fraction
    init: dict[str, int]
    good: isl.Set
    good_frame: Frame
    no_generalize_partitions: int = 1e4

    def __init__(self, ctx: isl.Context, module: Module, max_prob: Fraction, no_generalize_partitions: int = 1e4, initial_state: dict[str, Fraction] | None = None):
        self.init = initial_state
        self.max_prob = max_prob
        self.ctx = ctx
        self.vars = module.variables
        self.domain = make_domain(ctx, module.variables)
        # TODO for now we only support properties of the form Not (And [expr...])
        assert type(module.prop) == Not
        expr = module.prop.expr
        assert type(expr) == And
        conjuncts = expr.exprs
        self.bad = conjuncts_to_isl_set(module.variables, conjuncts, False)
        self.bad_frame = Frame(to_indicator_function(self.bad, self.domain), self.domain, self.vars)
        self.good = conjuncts_to_isl_set(module.variables, conjuncts, True)
        self.good_frame = Frame(to_indicator_function(self.good, self.domain), self.domain, self.vars)

        self.factor = module.lcm
        self.no_generalize_partitions =  no_generalize_partitions
        self.module = module

        self.ctx = ctx

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
                for v, update in zip(self.vars, updates):
                    assert v == update.variable.name
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
            guard = conjuncts_to_isl_set(self.vars, command.guards, False)
            isl_branch = []
            for p, updates in command.branches:
                assert len(updates) == len(self.vars)
                is_constant = any([type(update.new_val) == Const for update in updates])
                is_invertible = any([type(update.new_val) != Const for update in updates])
                assert not (is_constant and is_invertible), f'Invalid "mixed" update in {command.guards} -> {p} : {updates}.'
                isl_p = isl.Val(frac_to_isl(p))
                mulAff_p = isl.Aff.val_on_domain(guard.space, isl_p)
                if is_constant:
                    conditions = " and ".join([f"{v} = {u.new_val}" for v,u in zip(self.vars, updates)])
                    pwaff_string = "{ [" + ",".join(self.vars) + "] -> [1] : " + conditions + "; [" + ",".join(self.vars) + "] -> [0] }"
                    pwaff = isl.PwAff(pwaff_string)
                    isl_branch.append((mulAff_p, True, pwaff))
                else:
                    map_string = "{ [" + ",".join(self.vars) + "] -> "\
                        + "[" + ",".join([expr_to_isl_string(u.new_val) for u in updates ]) + "] }"
                    mp_rev = isl.Map(map_string).reverse()
                    pw_multi_aff_rev = mp_rev.as_pw_multi_aff().coalesce()
                    isl_branch.append((mulAff_p, False, pw_multi_aff_rev))
            self.isl_commands_theta.append((guard, isl_branch))

    @staticmethod
    def from_prism_file(ctx: isl.Context, path: str, max_prob: Fraction, set_expected_result: bool = True, no_generalization_partitions: int = 1e4, bad_label: str = "bad"):
        with open(path, "r") as f:
            prism_str = f.read()
        prism_parser = Lark(GRAMMAR, start="start")
        tree = prism_parser.parse(prism_str)
        module: Module = PrismTransformer().transform(tree)
        module.set_property(bad_label=bad_label)
        if set_expected_result:
            module.set_expected_result(path)
        module.clear_constants()
        return Model(ctx, module, max_prob, no_generalization_partitions, module.init)
    
    def Phi(self, F: Frame) -> Frame:
        # print("Phi")
        # print("space", F.pw.domain().get_space())
        # We do it slightly differently than described in the thesis for efficiency reasons.
        # We first take the sum of all updates that belong to phi, and only then intersect it with phi!
        phi_F = to_indicator_function(self.bad, F.domain)
        # print("phi_F", phi_F)
        for phi_set, isl_branch in self.isl_commands_phi:
            phi_i = isl.PwAff.zero_on_domain(F.domain.space)
            for p_ij, u in isl_branch:
                phi_ij = p_ij * F.pw.pullback_pw_multi_aff(u)
                # print("u", u)
                phi_i = phi_i.union_add(phi_ij)
            phi_i = phi_i.coalesce()
            
            guarded_phi_i = phi_i.intersect_domain(phi_set).coalesce()
            # print("guarded phi_i", guarded_phi_i)
            # print("guarded", guarded_phi_i)
            phi_F = phi_F.union_add(guarded_phi_i).coalesce()
        # print('PHI F', phi_F)
        return Frame(phi_F.intersect_domain(F.domain).coalesce(), F.domain, F.variables, F.factor)
    
    def Chi(self, F: Frame) -> Frame:
        one = self.Phi(F)
        two = self.Phi(one)
        eq_set = one.pw.eq_set(two.pw).intersect(one.pw.non_zero_set())
        eq_vals = one.pw.intersect_domain(eq_set)
        res = Frame.ones(isl.DEFAULT_CONTEXT, F.variables)
        res.pw = res.pw.union_min(eq_vals)
        # print("F", F)
        # print("one", one)
        # print("two", two)
        # print("res", res)
        return res
    
    def Theta(self, F: Frame) -> Frame:
        theta_F = isl.PwAff.zero_on_domain(F.domain.space)
        for phi_set, isl_branch in self.isl_commands_theta:
            phi = to_indicator_function(phi_set, F.domain)
            for p_ij, is_constant, u in isl_branch:
                if is_constant:
                    sat_phi = Frame(F.pw * phi, F.domain, F.variables).sum()
                    sat_phi_aff = isl.Aff.val_on_domain(F.domain.space, isl.Val(frac_to_isl(sat_phi)))
                    theta_ij = sat_phi_aff * u # In this case, u returns 1 on s' and 0 on all other states.
                    theta_F = theta_F.union_add(p_ij * theta_ij)
                else: # In this case, u is the reverted update.
                    update_ij = p_ij * (phi.pullback_pw_multi_aff(u) * F.pw.pullback_pw_multi_aff(u))
                    theta_F = theta_F.union_add(update_ij)
        res = theta_F.intersect_domain(F.domain).coalesce()
        return Frame(res, F.domain, F.variables, F.factor)

    def __PsiEq(self, W: Frame, r: Fraction) -> tuple[Frame, Fraction]:
        U = (self.good_frame * W)
        t = r - W.sum_over_region(self.bad)
        ThU = self.Theta(U)
        return ThU, t
    
    def Psi(self, G: FrameSet) -> FrameSet:
        return FrameSet([self.__PsiEq(W, r) for W,r in G.eqs], G.vars)
    
    def __str__(self) -> str:
        return f"""DTMC Model
  Prop: {self.prop}
  Bad: {self.bad}
  Vars: {self.vars}"""
        
