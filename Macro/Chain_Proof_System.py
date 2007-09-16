"""
Proof System which observes and attempts to prove paterns in computation.
"""

import sys, copy
import Chain_Simulator, Turing_Machine, Chain_Tape

parent_dir = sys.path[0][:sys.path[0].rfind("/")] # pwd path with last directory removed
sys.path.insert(1, parent_dir)
from Numbers.Algebraic_Expression import Algebraic_Unknown, Algebraic_Expression

DEBUG = False

def stripped_info(block):
  if block.num == 1:
    return block.symbol, 1
  else:
    return block.symbol

class Proof_System:
  """Stores past information and runs automated proof finders when it finds patterns."""
  def __init__(self, machine, recursive=False):
    self.machine = machine
    self.recursive = recursive
    # Hash of general forms of past configs
    self.past_configs = {}
    # Hash of general forms of proven meta-transitions
    self.proven_transitions = {}
    # Stat
    self.num_loops = 0
  
  def print_rules(self):
    for (state, a, b, c), (init_tape, diff_tape, num_steps) in self.proven_transitions.items():
      print
      print state, init_tape
      print diff_tape
      print num_steps
  
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
    if DEBUG:
      print
      print "Trying configurations from these loop numbers:", old_loop_num, loop_num
    rule = self.compare(old_config, full_config)
    if rule:
      # Remember rule
      self.proven_transitions[stripped_config] = rule
      # Clear our memory (couldn't use it anyway)
      self.past_configs = {}
      # Try to apply transition
      is_good, res = self.applies(rule, full_config)
      if is_good:
        trans, bad_delta = res
        return trans
    return False, None, None
  
  def compare(self, old_config, new_config):
    """Test the generality of a suggested meta-transition."""
    # Unpack configurations
    old_state, old_tape, old_step_num, old_loop_num = old_config
    new_state, new_tape, new_step_num, new_loop_num = new_config
    # Create a new tape which we will use to simulate general situation.
    gen_tape = old_tape.copy()
    min_val = {} # Notes the minimum value exponents with each unknown take.
    for direction in range(2):
      for block in gen_tape.tape[direction]:
        # Generalize, eg. (abc)^5 -> (abc)^(n+5)
        # Blocks with one rep are not generalized, eg. (abc)^1 -> (abc)^1
        if block.num not in (Chain_Tape.INF, 1):
          x = Algebraic_Unknown()
          block.num += x
          min_val[x.unknown()] = block.num.const
    initial_tape = gen_tape.copy()
    # Create the serogate simulator with the apm only able to use proven trans.
    if self.recursive:
      aps = copy.copy(self)
      aps.past_configs = None
    else:
      aps = None
    gen_sim = Chain_Simulator.Simulator()
    gen_sim.machine = self.machine
    gen_sim.tape = gen_tape
    gen_sim.proof = aps
    gen_sim.state = old_state
    gen_sim.dir = gen_tape.dir
    gen_sim.step_num = Algebraic_Expression([], 0)
    gen_sim.num_loops = 0
    gen_sim.op_state = Turing_Machine.RUNNING

    if DEBUG:
      print
      print "-"*60
      print old_state, old_tape, old_step_num
      print new_state, new_tape, new_step_num
      #gen_sim.print_self()
      print
      print gen_sim.state, gen_sim.tape
      print "Steps:", gen_sim.step_num
      print "Num Nonzeros:", gen_sim.get_nonzeros()
      show = raw_input("Show this proof (Enter nothing for no)?")
    gen_sim.step()
    self.num_loops += 1
    if DEBUG and show:
      #gen_sim.print_self()
      print
      print gen_sim.state, gen_sim.tape
      print "Steps:", gen_sim.step_num
      print "Num Nonzeros:", gen_sim.get_nonzeros()

    # Run the simulator
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
      if DEBUG and show:
        #gen_sim.print_self()
        print
        print gen_sim.state, gen_sim.tape
        print "Steps:", gen_sim.step_num
        print "Num Nonzeros:", gen_sim.get_nonzeros()
        #raw_input()
      if gen_sim.op_state is not Turing_Machine.RUNNING:
        return False
      for dir in range(2):
        for block in gen_sim.tape.tape[dir]:
          if isinstance(block.num, Algebraic_Expression):
            if len(block.num.terms) == 1:
              x = block.num.unknown()
              min_val[x] = min(min_val[x], block.num.const)
            # If more than one variable is clumped into a single term, it will fail.
            elif len(block.num.terms) > 1:
              return False

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
#    diff_tape = new_tape.copy()
    diff_tape = gen_sim.tape.copy()
    for dir in range(2):
#      for diff_block, old_block in zip(diff_tape.tape[dir], old_tape.tape[dir]):
      for diff_block, old_block in zip(diff_tape.tape[dir], initial_tape.tape[dir]):
        if diff_block.num != Chain_Tape.INF:
          diff_block.num -= old_block.num
          if isinstance(diff_block.num, Algebraic_Expression) and len(diff_block.num.terms) == 0:
            diff_block.num = diff_block.num.const
    replaces = []
    for dir in range(2):
      for init_block in initial_tape.tape[dir]:
        if isinstance(init_block.num, Algebraic_Expression):
          x = init_block.num.unknown()
          new_value = Algebraic_Unknown(x) - min_val[x] + 1
          init_block.num = init_block.num.substitute([ (x, new_value) ])
          replaces.append( (x, new_value) )
    num_steps = gen_sim.step_num.substitute(replaces)
    # Cast num_steps as an Algebraic Expression (if it somehow got through as simply an int)
    if not isinstance(num_steps, Algebraic_Expression):
      num_steps = Algebraic_Expression([], num_steps)
    if DEBUG:
      print
      print min_val
      print replaces
      print initial_tape
      print diff_tape, num_steps
      print "-"*60
      if show:
        raw_input()
    return initial_tape, diff_tape, num_steps
  
  def applies(self, rule, new_config):
    """Make sure that a meta-transion applies and provide important info"""
    if DEBUG:
      print
      print "Applying Rule"
      print rule
      print new_config
    ## Unpack input
    initial_tape, diff_tape, diff_num_steps = rule
    new_state, new_tape, new_step_num, new_loop_num = new_config
    ## Calculate number of reps allowable and other tape-based info
    num_reps = Chain_Tape.INF
    init_value = {}
    delta_value = {}
    bad_delta = False  # bad_delta == True  iff there is a negative delta != -1
    for dir in range(2):
      for init_block, diff_block, new_block in zip(initial_tape.tape[dir], diff_tape.tape[dir], new_tape.tape[dir]):
        # The constant term in init_block.num represents the minimum required value.
        if isinstance(init_block.num, Algebraic_Expression):
          # Calculate the initial and change in value for each variable.
          x = init_block.num.unknown()
          init_value[x] = new_block.num - init_block.num.const
          if init_value[x] < 0:
            if DEBUG:
              print "Fail 1 %s \t %s \t %s" % (init_block, diff_block, new_block)
            return False, 1
          delta_value[x] = diff_block.num
          # If this block's repetitions will be depleted during this transition,
          #   count the number of repetitions that it can allow while staying
          #   above the minimum requirement.
          if diff_block.num < 0:
            if diff_block.num != -1:
              bad_delta = True
            try:
              num_reps = min(num_reps, init_value[x] // -delta_value[x])
            except TypeError:
              if DEBUG:
                print "Fail 2 %s \t %s \t %s" % (num_reps, init_value[x], -delta_value[x])
              return False, 2
    # If none of the diffs are negative, this will repeat forever.
    if num_reps is Chain_Tape.INF:
      if DEBUG:
        print "Meta transition repeats forever", diff_tape
      return True, ((Turing_Machine.INF_REPEAT, None, None), bad_delta)
    # If we cannot even apply this transition once, we're done.
    if num_reps <= 0:
      if DEBUG:
        print "Fail 3", num_reps
      return False, 3
    ## Evaluate number of steps taken by taking meta-transition.
    ##   This would be equivolent to summing the diff_num_steps over ...
    # Effect of the constant factor:
    diff_steps = diff_num_steps.const * num_reps
    # Effects of each unknown in the formula:
    for term in diff_num_steps.terms:
      assert len(term.vars) == 1
      coef = term.coef; x = term.vars[0].var
      diff_steps += coef * series_sum(init_value[x], delta_value[x], num_reps)
    ## Alter the tape to account for taking meta-transition.
    return_tape = new_tape.copy()
    for dir in range(2):
      for diff_block, return_block in zip(diff_tape.tape[dir], return_tape.tape[dir]):
        if return_block.num is not Chain_Tape.INF:
          return_block.num += num_reps * diff_block.num
      #raise Exception, return_tape.tape
      return_tape.tape[dir] = [x for x in return_tape.tape[dir] if x.num != 0]
    ## Return the pertinent info
    return True, ((Turing_Machine.RUNNING, return_tape, diff_steps), bad_delta)

def series_sum(V0, dV, n):
  """Sums the arithmetic series V0, V0+dV, ... V0+(n-1)*dV."""
  # = Sum(V0 + p*dV, {p, 0, n-1}) = V0*Sum(1) + dV*Sum(p) = V0*n + dV*(n*(n-1)/2)
  #print V0, dV, n, "->",
  #r = V0*n + dV*(n*(n-1)/2)
  #print r
  return V0*n + (dV*n*(n-1))/2

