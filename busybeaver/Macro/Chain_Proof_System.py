"""
Proof System which observes and attempts to prove patterns in computation.
"""

import copy
import sys

import Chain_Simulator
import Chain_Tape
import Turing_Machine

parent_dir = sys.path[0][:sys.path[0].rfind("/")] # pwd path with last directory removed
sys.path.insert(1, parent_dir)
from Numbers.Algebraic_Expression import Algebraic_Unknown, Algebraic_Expression

class Rule(object):
  """Base type for Proof_System rules."""

class Diff_Rule(Rule):
  """A rule that specifies constant deltas for each tape block' repetition count."""
  def __init__(self, initial_tape, diff_tape, num_loops, num_steps, rule_num):
    self.initial_tape = initial_tape
    self.diff_tape = diff_tape
    self.num_loops = num_loops
    self.num_steps = num_steps
    self.num = rule_num
    self.num_uses = 0  # Number of times this rule has been applied.

class Gen_Rule(Rule):
  """A general rule that specifies some general end configuraton."""

# TODO: Try out some other stripped_configs
def stripped_info(block):
  """Get an abstraction of a tape block. We try to prove rules between
  configuration which have the same abstraction.
  """
  if block.num == 1:
    return block.symbol, 1
  else:
    return block.symbol

class Proof_System(object):
  """Stores past information, looks for patterns and tries to prove general
  rules when it finds patterns.
  """
  def __init__(self, machine, recursive, compute_steps, verbose, verbose_prefix):
    self.machine = machine
    self.recursive = recursive  # Should we try to prove recursive rules? (That is rules which use previous rules as steps.)
    self.compute_steps = compute_steps
    self.verbose = verbose  # Step-by-step state printing
    self.verbose_prefix = verbose_prefix
    # Memory of past stripped configurations with enough extra information to
    # try to prove rules. Set to None to disable proving new rules (for example
    # if this is a recursive proof system being used simply to apply rules).
    self.past_configs = {}
    # Colection of proven rules indexed by stripped configurations.
    self.rules = {}
    # Stat
    self.num_loops = 0
    self.num_recursive_rules = 0
    # TODO: Record how many steps are taken by recursive rules in simulator!
  
  def print_this(self, *args):
    """Print with prefix."""
    print self.verbose_prefix,
    for arg in args:
      print arg,
    print
  
  def print_rules(self):
    for rule in self.rules:
      print
      self.print_this(rule.num)
      self.print_this(rule.state, rule.init_tape)
      self.print_this(rule.diff_tape)
      self.print_this("Loops:", rule.num_loops, "Steps:", rule.num_steps)
      self.print_this(rule.num_times_applied)
  
  def log(self, tape, state, step_num, loop_num):
    """Log this configuration into the memory and check if it is similar to a past one.
    Returned boolean answers question: Rule applies?
    """
    # Stores state, direction pointed, and list of symbols on tape.
    # Note: we ignore the number of repetitions of these sequences so that we
    #   can get a very general view of the tape.
    stripped_config = (state, tape.dir,
                       tuple(map(stripped_info, tape.tape[0])),
                       tuple(map(stripped_info, tape.tape[1])))
    full_config = (state, tape, step_num, loop_num)
    
    ## If we're already proven a rule for this stripped_config, try to apply it.
    # TODO: stripped_config in self.rules.
    if self.rules.has_key(stripped_config):
      rule = self.rules[stripped_config]
      is_good, res = self.applies(rule, full_config)
      if is_good:
        trans, large_delta = res
        # Optimization: If we apply a rule and we are not trying to perform
        # recursive proofs, clear past configuration memory.
        # Likewise, even recursive proofs cannot use every subrule as a step.
        # Specifically, if there are any negative deltas other than -1, we cannot
        # apply the rule in a proof (yet) becuase e.g. (x + 3 // 2) is unresolvable
        # TODO: Enable Collatz proofs!
        if (not self.recursive  or  large_delta) and self.past_configs is not None:
          self.past_configs = {}
        rule.num_uses += 1
        return trans
      return False, None, None
    
    # If we are not trying to prove new rules, quit
    if self.past_configs is None:
      # TODO: Just return False for fail and object for success.
      return False, None, None
    
    # Otherwise
    # If this is the first time we see this stripped config, just store the loop number
    if not self.past_configs.has_key(stripped_config):
      self.past_configs[stripped_config] = (1, loop_num)
      return False, None, None
    
    times_seen, rest = self.past_configs[stripped_config]
    # If this is the second time, store more information for verification on third sighting
    if times_seen == 1:
      last_loop_num = rest
      delta_loop = loop_num - last_loop_num
      self.past_configs[stripped_config] = (2, ((state, tape.copy(), step_num, loop_num), loop_num, delta_loop))
      return False, None, None
    
    # If this is the third (or greater) time (i.e. config is stored) ...
    old_config, old_loop_num, delta_loop = rest
    # ... but loops don't match up, save config again in hope for next time.
    # (Note: We can only prove rules that take the same number of loops each time.)
    if loop_num - old_loop_num != delta_loop:
      delta_loop = loop_num - old_loop_num
      self.past_configs[stripped_config] = (times_seen + 1, ((state, tape.copy(), step_num, loop_num), loop_num, delta_loop))
      return False, None, None
    
    # ... and loops do match up, then try to prove it.
    rule = self.prove_rule(old_config, full_config)
    if rule:  # If we successfully proved a rule:
      # Remember rule
      self.rules[stripped_config] = rule
      # Clear our memory (couldn't use it anyway)
      self.past_configs = {}
      # Try to apply transition
      is_good, res = self.applies(rule, full_config)
      if is_good:
        trans, large_delta = res
        rule.num_uses += 1
        return trans
    return False, None, None
  
  def prove_rule(self, old_config, new_config):
    """Try to prove a general rule based upon specific example.
    
    Returns rule if successful or None.
    """
    if self.verbose:
      print
      self.print_this("** Testing new rule **")
      self.print_this("Example transition:")
      self.print_this("From:", old_config)
      self.print_this("To:  ", new_config)
    
    # Unpack configurations
    old_state, old_tape, old_step_num, old_loop_num = old_config
    new_state, new_tape, new_step_num, new_loop_num = new_config
    
    # Create the serogate simulator with the apm only able to use proven trans.
    gen_sim = Chain_Simulator.Simulator(self.machine,
                                        recursive=False,
                                        enable_prover=False,  # We'll create out own if needed.
                                        init_tape=False,
                                        compute_steps=self.compute_steps,
                                        verbose_simulator=self.verbose,
                                        verbose_prover=False,
                                        verbose_prefix=self.verbose_prefix + "  ")
    gen_sim.state = old_state
    gen_sim.step_num = Algebraic_Expression([], 0)
    
    # If prover can run recursively, we let it simulate with a lazy proof system.
    # That is, one that cannot prove new rules.
    if self.recursive:
      gen_sim.prover = copy.copy(self)
      gen_sim.prover.past_configs = None
      gen_sim.prover.verbose_prefix = gen_sim.verbose_prefix + "  "
    
    # Create a new tape which we will use to simulate general situation.
    gen_sim.tape = old_tape.copy()
    min_val = {} # Notes the minimum value exponents with each unknown take.
    for direction in range(2):
      for block in gen_sim.tape.tape[direction]:
        # Generalize, eg. (abc)^5 -> (abc)^(n+5)
        # Blocks with one rep are not generalized, eg. (abc)^1 -> (abc)^1
        if block.num not in (Chain_Tape.INF, 1):
          x = Algebraic_Unknown()
          block.num += x
          min_val[x.unknown()] = block.num.const
    initial_tape = gen_sim.tape.copy()
    gen_sim.dir = gen_sim.tape.dir
    
    # Run the simulator
    gen_sim.step()
    self.num_loops += 1
    #for i in xrange(new_loop_num - old_loop_num):
    while gen_sim.num_loops < (new_loop_num - old_loop_num):
      # We cannot step onto/over a block with 0 repetitions.
      block = gen_sim.tape.get_top_block()
      if isinstance(block.num, Algebraic_Expression) and block.num.const <= 0:
        # TODO: A more sophisticated system might try to make this block fixed sized.
        #       For now we just fail. It may be inificient/not worth it to impliment this anyway
        return False
      gen_sim.step()
      self.num_loops += 1
      
      if gen_sim.op_state is not Turing_Machine.RUNNING:
        return False
      # Update min_val for each expression.
      for dir in range(2):
        for block in gen_sim.tape.tape[dir]:
          if isinstance(block.num, Algebraic_Expression):
            if len(block.num.terms) == 1:
              x = block.num.unknown()
              min_val[x] = min(min_val[x], block.num.const)
            # If more than one variable is clumped into a single term, it will fail.
            elif len(block.num.terms) > 1:
              return False
    
    gen_sim.verbose_print()
    
    # Make sure finishing tape is the same as the end tape only general
    for dir in range(2):
      if len(gen_sim.tape.tape[dir]) != len(new_tape.tape[dir]):
        return False
      for init_block, gen_block, new_block in zip(initial_tape.tape[dir], gen_sim.tape.tape[dir], new_tape.tape[dir]):
        if isinstance(init_block.num, Algebraic_Expression):
          if (not isinstance(gen_block.num, Algebraic_Expression))  or  len(gen_block.num.terms) == 0:
            return False
          end_value = gen_block.num.const
        else:
          end_value = gen_block.num
        if new_block.num != end_value:
          return False
    
    # If machine has run delta_steps without error, it is a general rule.
    #diff_tape = new_tape.copy()
    diff_tape = gen_sim.tape.copy()
    for dir in range(2):
      #for diff_block, old_block in zip(diff_tape.tape[dir], old_tape.tape[dir]):
      for diff_block, old_block in zip(diff_tape.tape[dir], initial_tape.tape[dir]):
        if diff_block.num != Chain_Tape.INF:
          diff_block.num -= old_block.num
          if isinstance(diff_block.num, Algebraic_Expression) and len(diff_block.num.terms) == 0:
            diff_block.num = diff_block.num.const
    
    # Tighten up rule to be as general as possible (e.g. by replacing x+5 with x+1).
    replaces = {}
    for dir in range(2):
      for init_block in initial_tape.tape[dir]:
        if isinstance(init_block.num, Algebraic_Expression):
          x = init_block.num.unknown()
          new_value = Algebraic_Unknown(x) - min_val[x] + 1
          init_block.num = init_block.num.substitute({x: new_value})
          replaces[x] = new_value
    is_recursive_rule = False
    # Fix diff_tape.
    for dir in range(2):
      for diff_block in diff_tape.tape[dir]:
        if isinstance(diff_block.num, Algebraic_Expression):
          is_recursive_rule = True  # Recursive rules have variables in diff.
          diff_block.num = diff_block.num.substitute(replaces)
    # Fix num_steps.
    # TODO: Steps are not coming out right.
    num_steps = gen_sim.step_num.substitute(replaces)
    
    # Cast num_steps as an Algebraic Expression (if it somehow got through as simply an int)
    if not isinstance(num_steps, Algebraic_Expression):
      num_steps = Algebraic_Expression([], num_steps)
    
    if self.verbose:
      print
      self.print_this("** New rule proven **")
      self.print_this("Initial:", initial_tape)
      self.print_this("Diff:   ", diff_tape)
      self.print_this("In steps:", num_steps)
      print
    
    if is_recursive_rule:
      if self.verbose:
        self.print_this("** New recursive rule proven **")
      self.num_recursive_rules += 1
      # TODO: rule = Gen_Rule()
      rule = Diff_Rule(initial_tape, diff_tape, gen_sim.num_loops, num_steps, len(self.rules))
    else:
      rule = Diff_Rule(initial_tape, diff_tape, gen_sim.num_loops, num_steps, len(self.rules))
    
    return rule
  
  def applies(self, rule, start_config):
    """Make sure that a meta-transion applies and provide important info"""
    ## Unpack input
    new_state, new_tape, new_step_num, new_loop_num = start_config
    
    if self.verbose:
      print
      self.print_this("++ Applying Rule ++")
      self.print_this("Loop:", new_loop_num, "Rule ID:", rule.num)
      self.print_this("Rule:", rule)
      self.print_this("Config:", new_state, new_tape)
    
    ## Calculate number of repetitionss allowable and other tape-based info.
    num_reps = Chain_Tape.INF
    init_value = {}
    delta_value = {}
    # large_delta == True  iff there is a negative delta != -1
    # We keep track because even recursive proofs cannot contain rules with large_deltas.
    large_delta = False
    has_variable = False
    for dir in range(2):
      for init_block, diff_block, new_block in zip(rule.initial_tape.tape[dir], rule.diff_tape.tape[dir], new_tape.tape[dir]):
        # The constant term in init_block.num represents the minimum required value.
        if isinstance(init_block.num, Algebraic_Expression):
          # Calculate the initial and change in value for each variable.
          x = init_block.num.unknown()
          init_value[x] = new_block.num - init_block.num.const
          if init_value[x] < 0:
            if self.verbose:
              self.print_this("++ Current config is below rule minimum ++")
              self.print_this("Config block:", new_block)
              self.print_this("Rule initial block:", init_block)
            return False, 1
          delta_value[x] = diff_block.num
          # We can't apply non-constant deltas ... yet.
          # But, if all deltas are possitive, it is infinite.
          if isinstance(delta_value[x], Algebraic_Expression):
            has_variable = True
          # If this block's repetitions will be depleted during this transition,
          #   count the number of repetitions that it can allow while staying
          #   above the minimum requirement.
          if delta_value[x] < 0:
            if delta_value[x] != -1:
              large_delta = True
            try:
              # As long as init_value[x] >= 0 we can apply proof
              num_reps = min(num_reps, (init_value[x] // -delta_value[x])  + 1)
            except TypeError as e:
              if self.verbose:
                self.print_this("++ TypeError ++")
                self.print_this(e)
                self.print_this("From: num_reps = min(%r, (%r // -%r)  + 1)" % (num_reps, init_value[x], delta_value[x]))
              return False, 2
    
    # If none of the diffs are negative, this will repeat forever.
    if num_reps is Chain_Tape.INF:
      if self.verbose:
        self.print_this("++ Rules applies infinitely ++")
      return True, ((Turing_Machine.INF_REPEAT, None, None), large_delta)
    
    # Apply recursive transition once (Constant speed up).
    # TODO: Get function to apply repeatedly in tight loop.
    if has_variable:
      diff_steps = rule.num_steps.substitute(init_value)
      return_tape = new_tape.copy()
      for dir in range(2):
        for diff_block, return_block in zip(rule.diff_tape.tape[dir], return_tape.tape[dir]):
          if return_block.num is not Chain_Tape.INF:
            if isinstance(diff_block.num, Algebraic_Expression):
              return_block.num += diff_block.num.substitute(init_value)
            else:  # Else it's an int hopefully
              return_block.num += diff_block.num
        return_tape.tape[dir] = [x for x in return_tape.tape[dir] if x.num != 0]
      if self.verbose:
        self.print_this("++ Applying variable deltas once ++")
        self.print_this("Resulting tape:", return_tape)
      return True, ((Turing_Machine.RUNNING, return_tape, diff_steps), large_delta)
    
    # If we cannot even apply this transition once, we're done.
    if num_reps <= 0:
      if self.verbose:
        self.print_this("++ Cannot even apply transition once ++")
      return False, 3
    
    ## Determine number of base steps taken by applying rule.
    if self.compute_steps:
      # Effect of the constant factor:
      diff_steps = rule.num_steps.const * num_reps
      # Effects of each variable in the formula:
      for term in rule.num_steps.terms:
        assert len(term.vars) == 1
        coef = term.coef; x = term.vars[0].var
        # We don't factor out the coef, because it might make this work better for
        # some recursive rules.
        diff_steps += series_sum(coef * init_value[x], coef * delta_value[x], num_reps)
    else:
      diff_steps = 0 # TODO: Make it None instead of a lie
    
    ## Alter the tape to account for taking meta-transition.
    return_tape = new_tape.copy()
    for dir in range(2):
      for diff_block, return_block in zip(rule.diff_tape.tape[dir], return_tape.tape[dir]):
        if return_block.num is not Chain_Tape.INF:
          return_block.num += num_reps * diff_block.num
      return_tape.tape[dir] = [x for x in return_tape.tape[dir] if x.num != 0]
    
    ## Return the pertinent info
    if self.verbose:
      self.print_this("++ Rule successfully applied ++")
      self.print_this("Times applied:", num_reps)
      self.print_this("Resulting tape:", return_tape)
      print
    return True, ((Turing_Machine.RUNNING, return_tape, diff_steps), large_delta)

def series_sum(V0, dV, n):
  """Sums the arithmetic series V0, V0+dV, ... V0+(n-1)*dV."""
  # = sum(V0 + p*dV for p in range(n)) = V0*Sum(1) + dV*Sum(p) = V0*n + dV*(n*(n-1)/2)
  # TODO: The '/' acts as integer division, this is dangerous. It should
  # always work out because either n or n-1 is even. However, if n is an
  # Algebraic_Expression, this is more complicated. We don't want to use
  # __truediv__ because then we'd get a float output for ints.
  # TODO: Don't crash when we get NotImplemented exception from Algebraic_Expression.__div__.
  return V0*n + (dV*n*(n-1))/2

