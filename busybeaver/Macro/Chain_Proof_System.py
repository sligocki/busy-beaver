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

def stripped_info(block):
  """Get an abstraction of a tape block. We try to prove rules between configuration which have the same abstraction."""
  if block.num == 1:
    return block.symbol, 1
  else:
    return block.symbol

class Proof_System(object):
  """Stores past information and runs automated proof finders when it finds patterns."""
  def __init__(self, machine, recursive=False, verbose=False, verbose_prefix=""):
    self.machine = machine
    self.recursive = recursive
    self.verbose = verbose  # Step-by-step state printing
    self.verbose_prefix = verbose_prefix
    # Hash of general forms of past configs
    self.past_configs = {}
    # Hash of general forms of proven meta-transitions
    self.proven_transitions = {}
    # Stat
    self.num_loops = 0
    self.num_uses_of_rule = {}
    self.num_recursive_rules = 0
    # TODO: Record how many steps are taken by recursive rules in simulator!
  
  def print_this(self, *args):
    """Print with prefix."""
    print self.verbose_prefix,
    for arg in args:
      print arg,
    print
  
  def print_rules(self):
    for (state, a, b, c), (init_tape, diff_tape, num_steps) in self.proven_transitions.items():
      print
      self.print_this(state, init_tape)
      self.print_this(diff_tape)
      self.print_this(num_steps)
      self.print_this(self.num_uses_of_rule[state, a, b, c])
  
  def log(self, tape, state, step_num, loop_num):
    """Log this configuration into the table and check if it is similar to a past one.
    Returned boolean answers question: General tape action applies?"""
    # Stores state, direction pointed, and list of sequences on tape.
    # Note: we ignore the number of repetitions of these sequences so that we
    #   can get a very general view of the tape.
    stripped_config = (state, tape.dir,
                       tuple(map(stripped_info, tape.tape[0])),
                       tuple(map(stripped_info, tape.tape[1])))
    full_config = (state, tape, step_num, loop_num)
    
    # If this config already has a proven meta-transition return it.
    if self.proven_transitions.has_key(stripped_config):
      is_good, res = self.applies(self.proven_transitions[stripped_config], full_config)
      if is_good:
        trans, bad_delta = res
        # a bad_delta is not recursable b/c e.g. (x + 3 // 2) is unresolvable
        if (not self.recursive  or  bad_delta) and self.past_configs is not None:
          self.past_configs = {}
        self.num_uses_of_rule[stripped_config] += 1
        return trans
      return False, None, None
    
    # If we are not trying to prove new rules, quit
    if self.past_configs is None:
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
    # ... but loops don't match up, save config again in hope for next time
    if loop_num - old_loop_num != delta_loop:
      delta_loop = loop_num - old_loop_num
      self.past_configs[stripped_config] = (times_seen + 1, ((state, tape.copy(), step_num, loop_num), loop_num, delta_loop))
      return False, None, None
    
    # ... and loops do match up, then try the proof!
    rule = self.compare(old_config, full_config)
    if rule:
      # Remember rule
      self.proven_transitions[stripped_config] = rule
      self.num_uses_of_rule[stripped_config] = 0
      # Clear our memory (couldn't use it anyway)
      self.past_configs = {}
      # Try to apply transition
      is_good, res = self.applies(rule, full_config)
      if is_good:
        trans, bad_delta = res
        self.num_uses_of_rule[stripped_config] += 1
        return trans
    return False, None, None
  
  def compare(self, old_config, new_config):
    """Test the generality of a suggested meta-transition."""
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
    gen_sim = Chain_Simulator.Simulator()
    gen_sim.machine = self.machine
    gen_sim.verbose = self.verbose
    gen_sim.verbose_prefix = self.verbose_prefix + "  "
    gen_sim.state = old_state
    gen_sim.step_num = Algebraic_Expression([], 0)
    gen_sim.num_loops = 0
    gen_sim.op_state = Turing_Machine.RUNNING
    
    # If prover can run recursively, we let it simulate with a lazy proof system.
    # That is, one that cannot prove new rules.
    if self.recursive:
      gen_sim.proof = copy.copy(self)
      gen_sim.proof.past_configs = None
      gen_sim.proof.verbose_prefix = gen_sim.verbose_prefix + "  "
    else:
      gen_sim.proof = None
    
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
    
    if is_recursive_rule:
      if self.verbose:
        self.print_this("** New recursive rule proven **")
      self.num_recursive_rules += 1

    if self.verbose:
      print
      self.print_this("** New rule proven **")
      self.print_this("Initial:", initial_tape)
      self.print_this("Diff:   ", diff_tape)
      self.print_this("In steps:", num_steps)
      print
    
    return initial_tape, diff_tape, num_steps
  
  def applies(self, rule, new_config):
    """Make sure that a meta-transion applies and provide important info"""
    ## Unpack input
    initial_tape, diff_tape, diff_num_steps = rule
    new_state, new_tape, new_step_num, new_loop_num = new_config
    
    if self.verbose:
      print
      self.print_this("++ Applying Rule ++")
      self.print_this("Loop:", new_loop_num, "Rule ID:", diff_num_steps)
      self.print_this("Rule:", rule)
      self.print_this("Config:", new_state, new_tape)
    
    ## Calculate number of repetitionss allowable and other tape-based info.
    num_reps = Chain_Tape.INF
    init_value = {}
    delta_value = {}
    bad_delta = False  # bad_delta == True  iff there is a negative delta != -1
    has_variable = False
    for dir in range(2):
      for init_block, diff_block, new_block in zip(initial_tape.tape[dir], diff_tape.tape[dir], new_tape.tape[dir]):
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
              bad_delta = True
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
      return True, ((Turing_Machine.INF_REPEAT, None, None), bad_delta)
    
    # Apply recursive transition once (Constant speed up).
    # TODO: Get function to apply repeatedly in tight loop.
    if has_variable:
      diff_steps = diff_num_steps.substitute(init_value)
      return_tape = new_tape.copy()
      for dir in range(2):
        for diff_block, return_block in zip(diff_tape.tape[dir], return_tape.tape[dir]):
          if return_block.num is not Chain_Tape.INF:
            if isinstance(diff_block.num, Algebraic_Expression):
              return_block.num += diff_block.num.substitute(init_value)
            else:  # Else it's an int hopefully
              return_block.num += diff_block.num
        return_tape.tape[dir] = [x for x in return_tape.tape[dir] if x.num != 0]
      if self.verbose:
        self.print_this("++ Applying variable deltas once ++")
        self.print_this("Resulting tape:", return_tape)
      return True, ((Turing_Machine.RUNNING, return_tape, diff_steps), bad_delta)
    
    # If we cannot even apply this transition once, we're done.
    if num_reps <= 0:
      if self.verbose:
        self.print_this("++ Cannot even apply transition once ++")
      return False, 3
    
    ## Evaluate number of steps taken by taking meta-transition.
    ##   This would be equivolent to summing the diff_num_steps over ...
    # TODO: Appear to break for num_reps an ALgebraic_Expression.
    # Effect of the constant factor:
    diff_steps = diff_num_steps.const * num_reps
    # Effects of each variable in the formula:
    for term in diff_num_steps.terms:
      assert len(term.vars) == 1
      coef = term.coef; x = term.vars[0].var
      # We don't factor out the coef, because it might make this work better for
      # some recursive rules.
      diff_steps += series_sum(coef * init_value[x], coef * delta_value[x], num_reps)
    
    ## Alter the tape to account for taking meta-transition.
    return_tape = new_tape.copy()
    for dir in range(2):
      for diff_block, return_block in zip(diff_tape.tape[dir], return_tape.tape[dir]):
        if return_block.num is not Chain_Tape.INF:
          return_block.num += num_reps * diff_block.num
      return_tape.tape[dir] = [x for x in return_tape.tape[dir] if x.num != 0]
    
    ## Return the pertinent info
    if self.verbose:
      self.print_this("++ Rule successfully applied ++")
      self.print_this("Times applied:", num_reps)
      self.print_this("Resulting tape:", return_tape)
      print
    return True, ((Turing_Machine.RUNNING, return_tape, diff_steps), bad_delta)

def series_sum(V0, dV, n):
  """Sums the arithmetic series V0, V0+dV, ... V0+(n-1)*dV."""
  # = sum(V0 + p*dV for p in range(n)) = V0*Sum(1) + dV*Sum(p) = V0*n + dV*(n*(n-1)/2)
  # TODO: The '/' acts as integer division, this is dangerous. It should
  # always work out because either n or n-1 is even. However, if n is an
  # Algebraic_Expression, this is more complicated. We don't want to use
  # __truediv__ because then we'd get a float output for ints.
  # TODO: Don't crash when we get NotImplemented exception from Algebraic_Expression.__div__.
  return V0*n + (dV*n*(n-1))/2

