"""
Proof System which observes and attempts to prove patterns in computation.
"""

import copy
from collections import defaultdict
import sys

import Simulator
import Tape
import Turing_Machine

parent_dir = sys.path[0][:sys.path[0].rfind("/")] # pwd path with last directory removed
sys.path.insert(1, parent_dir)
from Numbers.Algebraic_Expression import Algebraic_Expression, Variable, NewVariableExpression, VariableToExpression, ConstantToExpression, is_scalar

class Rule(object):
  """Base type for Proof_System rules."""
  def __str__(self):
    return "Rule %d" % self.num

class Diff_Rule(Rule):
  """A rule that specifies constant deltas for each tape block' repetition count."""
  def __init__(self, initial_tape, diff_tape, num_steps, num_loops, rule_num):
    # TODO: Use basic lists instead of tapes, we never use the symbols.
    # TODO: Have a variable list and a min list instead of packing both into init_tape.
    # TOOD: Or maybe we don't even need variables, we could just have the things that
    # depend on variables index directly into the tapes?
    # TODO: Actually, variables only appear in num_steps, so we don't even need them
    # if we are not computing steps.
    self.initial_tape = initial_tape
    self.diff_tape = diff_tape
    self.num_steps = num_steps
    self.num_loops = num_loops
    self.num = rule_num  # Unique identifier.
    self.num_uses = 0  # Number of times this rule has been applied.

class General_Rule(Rule):
  """A general rule that specifies any general end configuration."""
  def __init__(self, var_list, min_list, result_tape, num_steps, num_loops, rule_num):
    self.var_list = var_list  # List of variables (or None) to assign repetition counts to.
    self.min_list = min_list  # List of minimum values for variables.
    # TODO: result_list and force output tape to be the same stripped config as input tape.
    self.result_tape = result_tape
    self.result_list = [block.num for block in result_tape.tape[0] + result_tape.tape[1]]
    self.num_steps = num_steps
    self.num_loops = num_loops
    self.num = rule_num
    self.num_uses = 0
    
    # Is this an infinite rule?
    self.infinite = True
    for var, result in zip(self.var_list, self.result_list):
      if var:  # If this exponent changes in this rule (has a variable)
        # TODO: This is a bit heavy-handed, but we probably don't prove
        #   too many recursive rules :)
        if is_scalar(result) or not result.always_greater_than(VariableToExpression(var)):
          # If any exponent can decrease, this is not an infinite rule.
          self.infinite = False
          break

# TODO: Try out some other stripped_configs
def stripped_info(block):
  """Get an abstraction of a tape block. We try to prove rules between
  configuration which have the same abstraction.
  """
  if block.num == 1:
    return block.symbol, 1
  else:
    return block.symbol

def strip_config(state, dir, tape):
  """"Return a generalized configuration removing the non-1 repetition counts from the tape."""
  # Optimization: Strip off Infinity blocks before we run the map (see tape[x][1:]).
  # Turns out Infinity.__cmp__ is expensive when run millions of times.
  # It used to spend up to 25% ot time here.
  # TODO: This map is expensive upwards of 10% of time is spend here.
  return (state, dir, tuple(map(stripped_info, tape[0][1:])),
                      tuple(map(stripped_info, tape[1][1:])))

class Past_Config(object):
  """A record of info from past instances of a stripped_config."""
  def __init__(self):
    self.times_seen = 0
    self.last_loop_num = None
    self.delta_loop = None

  def __repr__(self):
    return repr(self.__dict__)

  def log_config(self, step_num, loop_num):
    """Decide whether we should try to prove a rule.

    Currently, we try to prove a rule we've seen happen twice consecutively
    with the same delta_loop.
    """
    # First time we see stripped_config, store loop_num.
    if self.last_loop_num == None:
      self.last_loop_num = loop_num
      self.times_seen += 1
      return False
    
    # Next store delta_loop. If we have a delta_loop but it hasn't repeated,
    # then update the new delta.
    # (Note: We can only prove rules that take the same number of loops each time.)
    if self.delta_loop == None or loop_num - self.last_loop_num != self.delta_loop:
      self.delta_loop = loop_num - self.last_loop_num
      self.last_loop_num = loop_num
      self.times_seen += 1
      return False
    
    # Now we can finally try a proof.
    return True

class Proof_System(object):
  """Stores past information, looks for patterns and tries to prove general
  rules when it finds patterns.
  """
  def __init__(self, machine, recursive, compute_steps, verbose, verbose_prefix):
    self.machine = machine
    # Should we try to prove recursive rules? (Rules which use previous rules as steps.)
    self.recursive = recursive
    # Allow Collatz-style recursive rules. These are rules which depend upon
    # the parity (or remainder mod n) of exponents.
    # E.g. 1^(2k+1) 0 2 B>  -->  1^(3k+3) 0 2 B>
    # Note: Very experimental, may well break your simulation.
    self.allow_collatz = False
    self.compute_steps = compute_steps
    self.verbose = verbose  # Step-by-step state printing
    self.verbose_prefix = verbose_prefix
    # Memory of past stripped configurations with enough extra information to
    # try to prove rules. Set to None to disable proving new rules (for example
    # if this is a recursive proof system being used simply to apply rules).
    self.past_configs = defaultdict(Past_Config)
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
    for key, rule in self.rules.items():
      print
      self.print_this("Rule", rule.num)
      state = key[0]
      self.print_this("Initial:", state, rule.initial_tape)
      self.print_this("Diff:", rule.diff_tape)
      self.print_this("Loops:", rule.num_loops, "Steps:", rule.num_steps)
      self.print_this("Num uses:", rule.num_uses)
  
  def log(self, tape, state, step_num, loop_num):
    """Log this configuration into the memory and check if it is similar to a past one.
    Returned boolean answers question: Rule applies?
    """
    # Stores state, direction pointed, and list of symbols on tape.
    # Note: we ignore the number of repetitions of these sequences so that we
    #   can get a very general view of the tape.
    stripped_config = strip_config(state, tape.dir, tape.tape)
    full_config = (state, tape, step_num, loop_num)
    
    ## If we're already proven a rule for this stripped_config, try to apply it.
    # TODO: stripped_config in self.rules.
    if stripped_config in self.rules:
      rule = self.rules[stripped_config]
      is_good, res = self.apply_rule(rule, full_config)
      if is_good:
        trans, large_delta = res
        # Optimization: If we apply a rule and we are not trying to perform
        # recursive proofs, clear past configuration memory.
        # Likewise, even recursive proofs cannot use every subrule as a step.
        # Specifically, if there are any negative deltas other than -1,
        # we cannot apply the rule in a proof (yet) becuase
        # e.g. (x + 3 // 2) is unresolvable
        # TODO: Enable Collatz proofs!
        if not self.recursive  or  (large_delta and not self.allow_collatz):
          if self.past_configs is not None:
            self.past_configs.clear()
        rule.num_uses += 1
        return trans
      return False, None, None
    
    # If we are not trying to prove new rules, quit
    if self.past_configs is None:
      # TODO: Just return False for fail and object for success.
      return False, None, None
    
    # Otherwise log it into past_configs and see if we should try and prove a new rule.
    past_config = self.past_configs[stripped_config]
    if past_config.log_config(step_num, loop_num):
      # We see enough of a pattern to try and prove a rule.
      rule = self.prove_rule(stripped_config, full_config, past_config.delta_loop)
      if rule:  # If we successfully proved a rule:
        # Remember rule
        self.rules[stripped_config] = rule
        # Clear our memory (couldn't use it anyway).
        self.past_configs.clear()
        # Try to apply transition
        is_good, res = self.apply_rule(rule, full_config)
        if is_good:
          trans, large_delta = res
          rule.num_uses += 1
          return trans
    return False, None, None
  
  def prove_rule(self, stripped_config, full_config, delta_loop):
    """Try to prove a general rule based upon specific example.
    
    Returns rule if successful or None.
    """
    if self.verbose:
      print
      self.print_this("** Testing new rule **")
      self.print_this("From: ", full_config)
      self.print_this("Loops:", delta_loop)
    
    # Unpack configurations
    new_state, new_tape, new_step_num, new_loop_num = full_config
    
    # Create the serogate simulator with the apm only able to use proven trans.
    gen_sim = Simulator.Simulator(self.machine,
                                  recursive=False,
                                  # We'll create our own prover if needed.
                                  enable_prover=False,
                                  init_tape=False,
                                  compute_steps=self.compute_steps,
                                  verbose_simulator=self.verbose,
                                  verbose_prover=False,
                                  verbose_prefix=self.verbose_prefix + "  ")
    gen_sim.state = new_state
    gen_sim.step_num = ConstantToExpression(0)
    
    # If prover can run recursively, we let it simulate with a lazy proof system.
    # That is, one that cannot prove new rules.
    if self.recursive:
      gen_sim.prover = copy.copy(self)
      gen_sim.prover.past_configs = None
      gen_sim.prover.verbose_prefix = gen_sim.verbose_prefix + "  "
    
    # Create a new tape which we will use to simulate general situation.
    gen_sim.tape = new_tape.copy()
    min_val = {} # Notes the minimum value exponents with each unknown take.
    for direction in range(2):
      for block in gen_sim.tape.tape[direction]:
        # Generalize, eg. (abc)^5 -> (abc)^(n+5)
        # Blocks with one rep are not generalized, eg. (abc)^1 -> (abc)^1
        if block.num not in (Tape.INF, 1):
          x = Variable()
          x_expr = VariableToExpression(x)
          block.num += x_expr
          min_val[x] = block.num.const
    initial_tape = gen_sim.tape.copy()
    gen_sim.dir = gen_sim.tape.dir
    
    # Run the simulator
    gen_sim.step()
    self.num_loops += 1
    #for i in xrange(delta_loop):
    while gen_sim.num_loops < (delta_loop):
      # We cannot step onto/over a block with 0 repetitions.
      block = gen_sim.tape.get_top_block()
      if isinstance(block.num, Algebraic_Expression) and block.num.const <= 0:
        # TODO: A more sophisticated system might try to make this block fixed sized.
        # For now we just fail. It may not be worth implimenting this anyway
        if self.verbose:
          print
          self.print_this("** Failed: Exponent below min **")
          self.print_this(gen_sim.tape)
        return False
      gen_sim.step()
      self.num_loops += 1
      # TODO(shawn): Perhaps we should check in applying a rule failed this
      # step and if so cancel the proof?
      
      if gen_sim.op_state is not Turing_Machine.RUNNING:
        if self.verbose:
          print
          self.print_this("** Failed: Machine stopped running **")
          self.print_this(gen_sim.op_state)
        return False
      # Update min_val for each expression.
      # TODO: We only need to update for the blocks on each side of head.
      # TODO: Better yet, build these checks into the data type!
      for dir in range(2):
        for block in gen_sim.tape.tape[dir]:
          if isinstance(block.num, Algebraic_Expression):
            if len(block.num.terms) == 1:
              x = block.num.unknown()
              min_val[x] = min(min_val[x], block.num.const)
            # If more than one variable is clumped into a single term, it will fail.
            elif len(block.num.terms) > 1:
              if self.verbose:
                print
                self.print_this("** Failed: Multiple vars in one term **")
                self.print_this(gen_sim.tape)
              return False
    
    gen_sim.verbose_print()
    
    # Make sure finishing tape has the same stripped config as original.
    gen_stripped_config = strip_config(gen_sim.state, gen_sim.tape.dir, gen_sim.tape.tape)
    if gen_stripped_config != stripped_config:
      if self.verbose:
        print
        self.print_this("** Failed: Config mismatch **")
        self.print_this(gen_sim.tape)
        self.print_this(gen_stripped_config)
        self.print_this(stripped_config)
      return False
        
    # If machine has run delta_steps without error, it is a general rule.
    # Compute the diff_tape and find out if this is a recursive rule.
    # TODO: There should be a better way to find out if this is recursive.
    is_recursive_rule = False
    #diff_tape = new_tape.copy()
    diff_tape = gen_sim.tape.copy()
    for dir in range(2):
      for diff_block, initial_block in zip(diff_tape.tape[dir], initial_tape.tape[dir]):
        if diff_block.num != Tape.INF:
          diff_block.num -= initial_block.num
          if isinstance(diff_block.num, Algebraic_Expression):
            if len(diff_block.num.terms) == 0:
              diff_block.num = diff_block.num.const
            else:
              is_recursive_rule = True
    
    if is_recursive_rule:
      # TODO: Don't do all the work above if we not going to use it
      # Get everything in the right form for a General_Rule.
      var_list = []
      min_list = []
      assignment = {}
      for init_block in initial_tape.tape[0]+initial_tape.tape[1]:
        if isinstance(init_block.num, Algebraic_Expression):
          x = init_block.num.unknown()
          var_list.append(x)
          min_list.append(init_block.num.const - min_val[x] + 1)
          # Hackish: If exponent was x + 5 we want to replace all x with x - 5.
          # TODO: Make nicer.
          assignment[x] = init_block.num - 2*init_block.num.const
        else:
          var_list.append(None)
          min_list.append(init_block.num)
      
      # TODO: result_list = []
      result_tape = gen_sim.tape
      # Fix up result_tape to by applying variable substitution.
      for result_block in result_tape.tape[0]+result_tape.tape[1]:
        if isinstance(result_block.num, Algebraic_Expression):
          result_block.num = result_block.num.substitute(assignment)
      
      # Fix num_steps.
      if self.compute_steps:
        num_steps = gen_sim.step_num.substitute(assignment)
      else:
        num_steps = 0
      
      if self.verbose:
        print
        self.print_this("** New recursive rule proven **")
        self.print_this("Variables:", var_list)
        self.print_this("Minimums:", min_list)
        self.print_this("Result: ", result_tape)
        self.print_this("In steps:", num_steps)
        print
      self.num_recursive_rules += 1
      return General_Rule(var_list, min_list, result_tape, num_steps, gen_sim.num_loops, len(self.rules))
    
    # Else if a normal diff rule:
    # Tighten up rule to be as general as possible (e.g. by replacing x+5 with x+1).
    replaces = {}
    for dir in range(2):
      for init_block in initial_tape.tape[dir]:
        if isinstance(init_block.num, Algebraic_Expression):
          x = init_block.num.unknown()
          new_value = VariableToExpression(x) - min_val[x] + 1
          init_block.num = init_block.num.substitute({x: new_value})
          replaces[x] = new_value
    # Fix diff_tape.  # TODO: rm, only happens for recursive_rules
    for dir in range(2):
      for diff_block in diff_tape.tape[dir]:
        if isinstance(diff_block.num, Algebraic_Expression):
          diff_block.num = diff_block.num.substitute(replaces)
    # Fix num_steps.
    if self.compute_steps:
      num_steps = gen_sim.step_num.substitute(replaces)
    else:
      num_steps = 0
    
    # Cast num_steps as an Algebraic Expression (if it somehow got through as simply an int)
    if not isinstance(num_steps, Algebraic_Expression):
      num_steps = ConstantToExpression(num_steps)
    
    if self.verbose:
      print
      self.print_this("** New rule proven **")
      self.print_this("Initial:", initial_tape)
      self.print_this("Diff:   ", diff_tape)
      self.print_this("In steps:", num_steps)
      print
    
    return Diff_Rule(initial_tape, diff_tape, num_steps, gen_sim.num_loops, len(self.rules))
  
  def apply_rule(self, rule, start_config):
    """Try to apply a rule to a given configuration."""
    # TODO: Currently this returns a new tape and does not mutate the input.
    # Is that necessary, would it be worth it to mutate the input config in-place?
    if self.verbose:
      start_state, start_tape, start_step_num, start_loop_num = start_config
      print
      self.print_this("++ Applying Rule ++")
      self.print_this("Loop:", start_loop_num, "Rule ID:", rule.num)
      self.print_this("Rule:", rule)
      self.print_this("Config:", start_state, start_tape)
    
    if isinstance(rule, Diff_Rule):
      return self.apply_diff_rule(rule, start_config)
    if isinstance(rule, General_Rule):
      return self.apply_general_rule(rule, start_config)
    
  def apply_diff_rule(self, rule, start_config):
    ## Unpack input
    new_state, new_tape, new_step_num, new_loop_num = start_config
    
    ## Calculate number of repetitions allowable and other tape-based info.
    num_reps = None
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
          if (not isinstance(init_value[x], Algebraic_Expression) and
              init_value[x] < 0):
            if self.verbose:
              self.print_this("++ Current config is below rule minimum ++")
              self.print_this("Config block:", new_block)
              self.print_this("Rule initial block:", init_block)
              self.print_this("")
            return False, 1
          delta_value[x] = diff_block.num
          assert(isinstance(delta_value[x], (int, long)))
          # If this block's repetitions will be depleted during this transition,
          #   count the number of repetitions that it can allow while staying
          #   above the minimum requirement.
          if delta_value[x] < 0:
            if delta_value[x] != -1:
              large_delta = True
            try:
              if num_reps is None:
                # First one is safe.
                # For example, if we have a rule:
                #   Initial: 0^Inf 2^(d + 1)  (0)B>  2^(f + 2) 0^Inf 
                #   Diff:    0^Inf 2^1  (0)B>  2^-1 0^Inf 
                # then:
                #   0^Inf 2^3  (0)B> 2^(s + 11) 0^Inf
                # goes to:
                #   0^Inf 2^(s + 12)  (0)B> 2^2 0^Inf
                num_reps = (init_value[x] // -delta_value[x])  + 1
              else:
                if not isinstance(init_value[x], Algebraic_Expression):
                  # As long as init_value[x] >= 0 we can apply proof
                  num_reps = min(num_reps, (init_value[x] // -delta_value[x])  + 1)
                else:
                  # Example Rule:
                  #   Initial: 0^Inf 2^a+1 0^1 1^b+3 B> 0^1 1^c+1 0^Inf
                  #   Diff:    0^Inf 2^-1  0^0 1^+2  B> 0^0 1^-1  0^Inf
                  # Applied to tape:
                  #   0^Inf 2^d+5 0^1 1^3 B> 0^1 1^e+3 0^Inf
                  # We shoud apply the rule either d+4 or e+2 times depending
                  # on which is smaller. Too complicated, we fail.
                  if self.verbose:
                    self.print_this("++ Multiple negative diffs for expressions ++")
                    self.print_this("Config block:", new_block)
                    self.print_this("Rule initial block:", init_block)
                    self.print_this("Rule diff block:", diff_block)
                    self.print_this("")
                  return False, "Init_Expression"
            except TypeError, e:
              if self.verbose:
                self.print_this("++ TypeError ++")
                self.print_this(e)
                self.print_this("From: num_reps = min(%r, (%r // -%r)  + 1)" % (num_reps, init_value[x], delta_value[x]))
              return False, 2
    
    # If none of the diffs are negative, this will repeat forever.
    if num_reps is None:
      if self.verbose:
        self.print_this("++ Rules applies infinitely ++")
      return True, ((Turing_Machine.INF_REPEAT, None, None), large_delta)
    
    # If we cannot even apply this transition once, we're done.
    if (not isinstance(num_reps, Algebraic_Expression) and
        num_reps <= 0):
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
        try:
          diff_steps += series_sum(coef * init_value[x], coef * delta_value[x], num_reps)
        except TypeError:
          if self.verbose:
            self.print_this("++ Cannot divide expression by 2 ++")
          return False, 4
    else:
      diff_steps = 0 # TODO: Make it None instead of a lie
    
    ## Alter the tape to account for applying rule.
    return_tape = new_tape.copy()
    for dir in range(2):
      for diff_block, return_block in zip(rule.diff_tape.tape[dir], return_tape.tape[dir]):
        if return_block.num is not Tape.INF:
          return_block.num += num_reps * diff_block.num
      return_tape.tape[dir] = [x for x in return_tape.tape[dir] if x.num != 0]
    
    ## Return the pertinent info
    if self.verbose:
      self.print_this("++ Rule successfully applied ++")
      self.print_this("Times applied:", num_reps)
      self.print_this("Resulting tape:", return_tape)
      print
    return True, ((Turing_Machine.RUNNING, return_tape, diff_steps), large_delta)

  # Diff rules can be applied any number of times in a single evaluation.
  # But we can only apply a general rule once at a time.
  # TODO: Get function to apply repeatedly in tight loop.
  def apply_general_rule(self, rule, start_config):
    # Unpack input
    start_state, start_tape, start_step_num, start_loop_num = start_config

    large_delta = True  # TODO: Does this make sense? Should we rename this?
    # Current list of all block exponents. We will update it in place repeatedly
    # rather than creating new tapes.
    current_list = [block.num for block in start_tape.tape[0] + start_tape.tape[1]]
    
    # If this recursive rule is infinite.
    if rule.infinite and config_is_above_min(rule.var_list, rule.min_list,
                                             current_list):
      if self.verbose:
        self.print_this("++ Rules applies infinitely ++")
      return True, ((Turing_Machine.INF_REPEAT, None, None), large_delta)
    
    # Keep applying rule till we fail can't any more
    # TODO: Maybe we can use some intelligence when all negative rules are constants
    # becuase, then we know how many time we can apply the rule.
    success = False  # If we fail before doing anything, return false
    num_reps = 0
    diff_steps = 0
    # Get variable assignments for this case and check minimums.
    assignment = {}
    while config_is_above_min(rule.var_list, rule.min_list,
                              current_list, assignment):
      if self.verbose:
        self.print_this(num_reps, current_list)
      # Apply variable assignment to update number of steps and tape config.
      if self.compute_steps:
        diff_steps += rule.num_steps.substitute(assignment)
      # Stop using substitute and make this a tuple-to-tuple function?
      current_list = [val.substitute(assignment) if isinstance(val, Algebraic_Expression) else val for val in rule.result_list]
      num_reps += 1
      success = True
      assignment = {}
    
    # We cannot apply rule any more.
    # Make sure there are no zero's in tape exponents.
    if success:
      tape = start_tape.copy()
      for block, current_val in zip(tape.tape[0] + tape.tape[1], current_list):
        block.num = current_val
      # TODO: Perhaps do this in one step?
      for dir in range(2):
        tape.tape[dir] = [x for x in tape.tape[dir] if x.num != 0]
      if self.verbose:
        self.print_this("++ Recursive rule applied ++")
        self.print_this("Times applied", num_reps)
        self.print_this("Resulting tape:", tape)
      return True, ((Turing_Machine.RUNNING, tape, diff_steps), large_delta)
    else:
      if self.verbose:
        self.print_this("++ Current config is below rule minimum ++")
        self.print_this("Config tape:", start_tape)
        self.print_this("Rule min vals:", min_list)
      return False, 1

def config_is_above_min(var_list, min_list, current_list, assignment={}):
  """Tests if current_list is above min_list setting assignment along the way"""
  for var, min_val, current_val in zip(var_list, min_list, current_list):
    if current_val < min_val:
      return False
    assignment[var] = current_val
  return True

def series_sum(V0, dV, n):
  """Sums the arithmetic series V0, V0+dV, ... V0+(n-1)*dV."""
  # = sum(V0 + p*dV for p in range(n)) = V0*Sum(1) + dV*Sum(p) = V0*n + dV*(n*(n-1)/2)
  # TODO: The '/' acts as integer division, this is dangerous. It should
  # always work out because either n or n-1 is even. However, if n is an
  # Algebraic_Expression, this is more complicated. We don't want to use
  # __truediv__ because then we'd get a float output for ints.
  # TODO: Don't crash when we get NotImplemented exception from Algebraic_Expression.__div__.
  return V0*n + (dV*n*(n-1))/2
