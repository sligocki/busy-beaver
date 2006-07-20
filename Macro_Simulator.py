#! /usr/bin/env python
#
# Turing Machine Simulator based on Heiner Marxen's Macro Machine design.
#

import copy
import math, time

# Constants
HALT_STATE = -1
INF = "Inf"
DEBUG = False
MAX_TTABLE_CELLS = 100000 # ~40 MB

# Useful Tool
def reverse(in_list):
  reversed_in_list = list(in_list)
  reversed_in_list.reverse()
  return reversed_in_list

class Macro_TTable:
  """Creates an on-the-fly or lazy-evaluation transition table for a macro machine.
  Can be indexed as if the entire table already existed in memory."""
  def __init__(self, TTable, macro_size):
    # Normal Machine's transition table
    # TTable: Q x S -> S x D x Q
    # Note: Q = set of states, S = set of symbols, D = set of directions
    self.TTable = TTable
    self.num_states = len(TTable)
    self.num_symbols = len(TTable[0])
    # Macro Machine's transition table (lazy evaluated)
    # macro_TTable: Q x S^m x D -> Q x S^m x D x Z
    # Where m is the size of the macro_symbols and the output Z is the number
    #   of micro steps taken.
    self.macro_TTable = {}
    # Statistical variables
    self.num_misses = 0
    self.num_single_steps = 0
  def __getitem__(self, item):
    """Accesses the macro transition table. item = state, symbol, dir."""
    # If we don't already have this input in the table, evaluate it.
    if not self.macro_TTable.has_key(item):
      # Keep memory use down in exteme situations
      if len(self.macro_TTable) >= MAX_TTABLE_CELLS:
        self.macro_TTable = {}
      self.macro_TTable[item] = self._run(*item)
      self.num_misses += 1
    return self.macro_TTable[item]
  def _run(self, macro_state_in, macro_symbol_in, macro_dir_in):
    """Evaluates macro_TTable[state, symbol, dir]"""
    # Set up machine
    num_steps = 0
    state_in = macro_state_in
    tape = list(macro_symbol_in)
    size = len(tape)
    if macro_dir_in:
      pos = 0
    else:
      pos = size - 1
    max_steps = size * self.num_states * self.num_symbols**size
    # Run machine
    while 0 <= pos < size:
      symbol_in = tape[pos]
      symbol_out, dir_out, state_out = self.TTable[state_in][symbol_in]
      state_in = state_out
      tape[pos] = symbol_out
      if dir_out:
        pos += 1
      else:
        pos -= 1
      num_steps += 1
      self.num_single_steps += 1
      # If we halt, immediately return.  We use dir_out as position.
      if state_in == HALT_STATE:
        return state_in, tuple(tape), pos, num_steps
      # If we've exceeded the maximum possible number of steps, we'll never halt.
      if num_steps > max_steps:
        if DEBUG:
          print "Infinite repeat within cell.", num_steps, tape, pos
        return INF, None, None, INF
    # Return critical info about machine if it's still running.
    macro_state_out = state_in
    macro_symbol_out = tuple(tape)
    if pos < 0:
      macro_dir_out = 0
    else:  # pos >= size
      macro_dir_out = 1
    return macro_state_out, macro_symbol_out, dir_out, num_steps

class Stack(list):
  """Generic Stack class based on built-in list."""
  def pop(self):
    return list.pop(self, 0)
  def push(self, item):
    self.insert(0, item)

class Tape_Slice:
  """Slice of tape of length macro_step with allowed repatitions."""
  def __init__(self, symbol, number_of_repetitions):
    self.symbol = symbol
    self.num = number_of_repetitions
  def __repr__(self):
    num = str(self.num)
    #if "+" in num:
    #  num = "("+num+")"
    if len(self.symbol) == 1:
      sym = self.symbol[0]
    else:
      sym = self.symbol
    return "%s^%s" % (str(sym), num)
  def copy(self):
    if isinstance(self.num, Algebraic_Expression):
      return Tape_Slice(self.symbol, self.num.copy())
    else:
      return Tape_Slice(self.symbol, self.num)

class Macro_Tape:
  """Stores the turing machine tape in Marxen-style macro-compression."""
  def __init__(self, macro_size, no_init=False):
    self.macro_size = macro_size
    if not no_init:
      self.dir = 1
      self.tape = [Stack(), Stack()]
      self.tape[0].push(Tape_Slice((0,)*macro_size, INF))
      self.tape[1].push(Tape_Slice((0,)*macro_size, INF))
  def __repr__(self):
    if self.dir:  dir = " -> "
    else:         dir = " <- "
    return `reverse(self.tape[0])`+dir+`self.tape[1]`
  def copy(self):
    #new = copy.deepcopy(self)
    new = Macro_Tape(self.macro_size, no_init=True)
    new.dir = self.dir
    s0 = Stack([x.copy() for x in self.tape[0]])
    s1 = Stack([x.copy() for x in self.tape[1]])
    new.tape = [s0, s1]
    return new
  def get_nonzeros(self):
    """Return number of nonzero symbols on the tape."""
    n = 0
    for dir in range(2):
      for block in self.tape[dir]:
        if block.num is not INF:
          for sym in block.symbol:
            if sym:
              n += block.num
    return n
  def get_top_symbol(self):
    """Simply returns the current symbol and direction."""
    return self.tape[self.dir][0], self.dir
  def apply_single_move(self, macro_symbol, dir):
    """Apply a single macro step.  del old symbol, push new one."""
    self.del_one()
    self.push_one(macro_symbol, not dir)
    self.dir = dir
  def apply_chain_move(self, macro_symbol):
    """Apply a chain macro step which replaces an entire string of symbols.
    Returns the number of macro symbols replaced."""
    # Pop off old sequence
    num = self.tape[self.dir][0].num
    if num is INF:
      if DEBUG:
        print "Infinite Chain", self.tape, macro_symbol
      return INF
    self.tape[self.dir].pop()
    # Push on new one behind us
    stack = self.tape[not self.dir]
    top = stack[0]
    if top.symbol == macro_symbol:
      if top.num is not INF:
        top.num += num
    else:
      stack.push(Tape_Slice(macro_symbol, num))
    return num
  def del_one(self):
    """Delete of the current macro symbol."""
    stack = self.tape[self.dir]
    top = stack[0]
    # Don't decriment infinity
    if top.num is not INF:
      top.num -= 1
      # If there are none left, remove from stack.
      if top.num == 0:
        stack.pop()
  def push_one(self, macro_symbol, dir):
    """Push a macro symbol in the direction specified."""
    stack = self.tape[dir]
    top = stack[0]
    # If it is identical to the top symbol, combine them.
    if top.symbol == macro_symbol:
      if top.num is not INF:
        top.num += 1
    # Otherwise, just add it seperately.
    else:
      stack.push(Tape_Slice(macro_symbol, 1))

from Algebraic_Expression import Algebraic_Unknown, Algebraic_Expression

def stripped_info(block):
  if block.num == 1:
    return block.symbol, 1
  else:
    return block.symbol

class Automated_Proof_Maker:
  """Stores past information and runs automated proof finders when it finds patterns."""
  def __init__(self, mtt, recursive=True):
    self.mtt = mtt
    self.recursive = recursive
    # Hash of general forms of past configs
    self.past_configs = {}
    # Hash of general forms of proven meta-transitions
    self.proven_transitions = {}
  def print_rules(self):
    for (state, a, b, c), (init_tape, diff_tape, num_steps) in self.proven_transitions.items():
      print
      print state, init_tape
      print diff_tape
      print num_steps
  def log(self, tape, state, step_num):
    """Log this configuration into the table and check if it is similar to a past one.
    Returned boolean answers question: General tape action applies?"""
    # Stores state, direction pointed, and list of sequences on tape.
    # Note: we ignore the number of repetitions of these sequences so that we
    #   can get a very general view of the tape.
    stripped_config = (state, tape.dir,
                       tuple(map(stripped_info, tape.tape[0])),
                       tuple(map(stripped_info, tape.tape[1])))
    full_config = (state, tape, step_num)
    # If this config already has a proven meta-transition return it.
    if self.proven_transitions.has_key(stripped_config):
      trans = self.applies(self.proven_transitions[stripped_config], full_config)
      if trans:
        if not self.recursive or isinstance(trans[-1], (int, long)) or len(trans[-1].terms()) == 0:
          self.past_configs = {}
        return trans
      return False
    # If there is a compatible config on record, see if a proof can be
    #   auto-generated to develope a meta-transition.
    if self.past_configs is not None:
      if self.past_configs.has_key(stripped_config):
        rule = self.compare(self.past_configs[stripped_config], full_config)
        if rule:
          self.proven_transitions[stripped_config] = rule
          self.past_configs = {}
          trans = self.applies(rule, full_config)
          if trans:
            return trans
          return False
      # If no other compatible configs on record, simply log this one.
      state, tape, step_num = full_config
      self.past_configs[stripped_config] = (state, tape.copy(), step_num)
    return False
  def compare(self, old_config, new_config):
    """Test the generality of a suggested meta-transition."""
    # Unpack configurations
    old_state, old_tape, old_step_num = old_config
    new_state, new_tape, new_step_num = new_config
    # Create a new tape which we will use to simulate general situation.
    gen_tape = old_tape.copy()
    min_val = {} # Notes the minimum value exponents with each unknown take.
    for direction in range(2):
      for block in gen_tape.tape[direction]:
        # Generalize, eg. (abc)^5 -> (abc)^(n+5)
        # Blocks with one rep are not generalized, eg. (abc)^1 -> (abc)^1
        if block.num not in (INF, 1):
          x = Algebraic_Unknown()
          block.num += x
          min_val[x.unknown()] = block.num.const()
    initial_tape = gen_tape.copy()
    # Create the serogate simulator with the apm only able to use proven trans.
    if self.recursive:
      apm = copy.copy(self)
      apm.past_configs = None
    else:
      apm = None
    gen_sim = Macro_Simulator(gen_tape, self.mtt, apm, old_state,
                              Algebraic_Expression(0))
    if DEBUG:
      print
      print "-"*60
      print old_state, old_tape, old_step_num
      print new_state, new_tape, new_step_num
      gen_sim.print_self()
      show = raw_input("Show this proof?")
    gen_sim.step()
    if DEBUG and show:
      gen_sim.print_self()
    # Run the simulator
    while gen_sim.cur_step_num.const() < (new_step_num - old_step_num):
      # We cannot step onto/over a block with 0 repetitions.
      block, dir = gen_sim.tape.get_top_symbol()
      if isinstance(block.num, Algebraic_Expression) and block.num.const() <= 0:
        # TODO: A more sophisticated system might try to not make this block fixed sized.  For now we just fail.
        return False
      gen_sim.step()
      if DEBUG and show:
        gen_sim.print_self()
        raw_input()
      if gen_sim.state in (HALT_STATE, INF):
        return False
      for dir in range(2):
        for block in gen_sim.tape.tape[dir]:
          if isinstance(block.num, Algebraic_Expression):
            if len(block.num.expr.terms) == 1:
              x = block.num.unknown()
              min_val[x] = min(min_val[x], block.num.const())
            # If more than one variable is clumped into a single term, it will fail.
            elif len(block.num.expr.terms) > 1:
              return False
    # Make sure finishing tape is the same as the end tape only general
    for dir in range(2):
      if len(gen_sim.tape.tape[dir]) != len(new_tape.tape[dir]):
        return False
      for init_block, gen_block, new_block in zip(initial_tape.tape[dir], gen_sim.tape.tape[dir], new_tape.tape[dir]):
        if isinstance(init_block.num, Algebraic_Expression):
          if not isinstance(gen_block.num, Algebraic_Expression) or \
             len(gen_block.num.terms()) == 0:
            return False
          end_value = gen_block.num.const()
        else:
          end_value = gen_block.num
        if new_block.num != end_value:
          return False
    # If machine has run delta_steps without error, it is a general rule.
    diff_tape = new_tape.copy()
    for dir in range(2):
      for diff_block, old_block in zip(diff_tape.tape[dir], old_tape.tape[dir]):
        if diff_block.num is not INF:
          diff_block.num -= old_block.num
    replaces = []
    for dir in range(2):
      for init_block in initial_tape.tape[dir]:
        if isinstance(init_block.num, Algebraic_Expression):
          x = init_block.num.unknown()
          new_value = Algebraic_Unknown(x) - min_val[x] + 1
          init_block.num = init_block.num.substitute([ (x, new_value) ])
          replaces.append( (x, new_value) )
    num_steps = gen_sim.cur_step_num.substitute(replaces)
    if DEBUG:
      print
      print min_val
      print replaces
      print initial_tape
      print diff_tape, num_steps
      print "-"*60
    return initial_tape, diff_tape, num_steps
  def applies(self, rule, new_config):
    """Make sure that a meta-transion applies and provide important info"""
    if DEBUG:
      print
      print rule
      print new_config
    ## Unpack input
    initial_tape, diff_tape, diff_num_steps = rule
    new_state, new_tape, new_step_num = new_config
    ## Calculate number of reps allowable and other tape-based info
    num_reps = INF
    init_value = {}
    delta_value = {}
    for dir in range(2):
      for init_block, diff_block, new_block in zip(initial_tape.tape[dir], diff_tape.tape[dir], new_tape.tape[dir]):
        # The constant term in init_block.num represents the minimum required value.
        if isinstance(init_block.num, Algebraic_Expression):
          if init_block.num.const() > new_block.num:
            return False
          # Calculate the initial and change in value for each variable.
          x = init_block.num.unknown()
          init_value[x] = new_block.num - init_block.num.const()
          delta_value[x] = diff_block.num
          # If this block's repetitions will be depleted during this transition,
          #   count the number of repetitions that it can allow while staying
          #   above the minimum requirement.
          if diff_block.num < 0:
            try:
              #print num_reps, init_value[x], -delta_value[x], init_value[x] // -delta_value[x]
              num_reps = min(num_reps, init_value[x] // -delta_value[x])
              #print num_reps
            except TypeError:
              return False
    # If none of the diffs are negative, this will repeat forever.
    if num_reps is INF:
      if DEBUG:
        print "Meta transition repeats forever", diff_tape
      return INF, INF
    # If we cannot even apply this transition once, we're done.
    if num_reps <= 0:
      return False
    ## Evaluate number of steps taken by taking meta-transition.
    ##   This would be equivolent to summing the diff_num_steps over ...
    # Effect of the constant factor:
    diff_steps = diff_num_steps.const() * num_reps
    # Effects of each unknown in the formula:
    for coef, x in diff_num_steps.terms():
      diff_steps += coef * series_sum(init_value[x], delta_value[x], num_reps)
    ## Alter the tape to account for taking meta-transition.
    return_tape = new_tape.copy()
    for dir in range(2):
      for diff_block, return_block in zip(diff_tape.tape[dir], return_tape.tape[dir]):
        if return_block.num is not INF:
          return_block.num += num_reps * diff_block.num
      return_tape.tape[dir] = Stack([x for x in return_tape.tape[dir] if x.num != 0])
    ## Return the pertinent info
    return return_tape, diff_steps

def series_sum(V0, dV, n):
  """Sums the arithmetic series V0, V0+dV, ... V0+(n-1)*dV."""
  # = Sum(V0 + p*dV, {p, 0, n-1}) = V0*Sum(1) + dV*Sum(p) = V0*n + dV*(n*(n-1)/2)
  #print V0, dV, n, "->",
  #r = V0*n + dV*(n*(n-1)/2)
  #print r
  return V0*n + dV*(n*(n-1)/2)

class Macro_Simulator:
  def __init__(self, tape=None, mtt=None, apm=None, state=None, cur_step_num=0):
    self.tape = tape
    self.mtt = mtt
    self.apm = apm
    self.state = state
    self.cur_step_num = cur_step_num
    self.reset_stat_vars()
  def init_new(self, TTable, macro_size, level=4):
    """Run to initialize a new simulator to a trans_table and macro_size."""
    self.tape = Macro_Tape(macro_size)
    self.mtt = Macro_TTable(TTable, macro_size)
    if level < 3:
      self.apm = None
    elif level == 3:
      self.apm = Automated_Proof_Maker(self.mtt, recursive=False)
    elif level == 4:
      self.apm = Automated_Proof_Maker(self.mtt, recursive=True)
    self.state = 0
    self.cur_step_num = 0
    self.reset_stat_vars()
  def reset_stat_vars(self):
    """Sets or resets the statistical variables which count the impacts of
    different step types."""
    self.num_macro_steps = self.num_steps_from_macro = 0
    self.num_chain_steps = self.num_steps_from_chain = 0
    self.num_meta_steps = self.num_steps_from_meta = 0
  def run(self, num_steps):
    """Run num_steps further"""
    self.seek(self.cur_step_num + num_steps)
  def seek(self, step_num):
    """Seek step_num steps or further (Does not run backwards)"""
    while self.cur_step_num < step_num and self.state not in (HALT_STATE, INF):
      self.step()
  def step(self):
    """Take a single step.  Note that a single step may be a quite long chain
    step or an even longer meta-step from the APM."""
    if self.state in (HALT_STATE, INF):
      return
    if self.apm:
      # Document this tape configuration and see if a similar one has been seen
      #   in the past.  If so, run an Automated Proof Maker.
      trans = self.apm.log(self.tape, self.state, self.cur_step_num)
      if trans:
        new_tape, num_steps = trans
        if num_steps is INF:
          self.state = INF
          #self.cur_step_num = INF
          self.num_steps_from_meta = INF
        else:
          self.tape = new_tape
          self.cur_step_num += num_steps
          self.num_steps_from_meta += num_steps
        # Stats
        self.num_meta_steps += 1
        return
    # Get info from tape
    block, dir = self.tape.get_top_symbol()
    # Lookup transition
    new_state, new_symbol, new_dir, this_num_steps \
      = self.mtt[self.state, block.symbol, dir]
    # Apply transition
    if new_state == HALT_STATE:
      self.state = HALT_STATE
      self.tape.apply_single_move(new_symbol, 1)
      self.cur_step_num += this_num_steps
      return
    elif this_num_steps is INF:
      self.state = INF
      #self.cur_step_num = INF
      self.num_macro_steps += 1
      self.num_steps_from_macro = INF
      return
    # If direction and state are unchanged after transition, then the transition
    #   will be repeated across an entire chain of equivolent macro symbols.
    elif new_state == self.state and new_dir == dir:
      num_reps = self.tape.apply_chain_move(new_symbol)
      if num_reps is not INF:
        self.cur_step_num += this_num_steps * num_reps
        self.num_steps_from_chain += this_num_steps * num_reps
      else:
        self.state = INF
        #self.cur_step_num = INF
        self.num_steps_from_chain = INF
      # Stats
      self.num_chain_steps += 1
      return
    # Otherwise, it was a normal transition, just apply it.
    else:
      self.state = new_state
      self.tape.apply_single_move(new_symbol, new_dir)
      self.cur_step_num += this_num_steps
      # Stats
      self.num_macro_steps += 1
      self.num_steps_from_macro += this_num_steps
      return
  def print_self(self):
    print
    print "Total Steps: ", with_power(self.cur_step_num)
    print "Single Steps:", with_power(self.mtt.num_single_steps)
    print "Macro Steps: ", with_power(self.num_steps_from_macro), self.num_macro_steps, "Macro transitions defined:", len(self.mtt.macro_TTable)
    print "Chain Steps: ", with_power(self.num_steps_from_chain), self.num_chain_steps
    if self.apm:
      print "Meta Steps:  ", with_power(self.num_steps_from_meta), self.num_meta_steps, "Meta transitions proved:", len(self.apm.proven_transitions)
    print "Time:", time.clock()
    print self.state, self.tape, self.tape.get_nonzeros()

def with_power(value):
  if value is INF:
    r = "10^Inf  "
  elif value == 0:
    r = "10^-Inf "
  else:
    try:
      r = "10^%-4.1f " % math.log10(value)
    except:
      r = "        "
  value = str(value)
  if len(value) < 60:
    r += str(value)
  return r

def run(macro_size, filename, line_num=1, level=4):
  import IO
  global sim
  TTable = IO.load_TTable_filename(filename, line_num)
  sim = Macro_Simulator()
  sim.init_new(TTable, macro_size, level)
  extent = 1
  try:
    while sim.state not in (HALT_STATE, INF):
      sim.seek(extent)
      sim.print_self()
      extent *= 10
      #extent **= 2
      #extent += 10
  finally:
    sim.print_self()
  if sim.state == HALT_STATE:
    print
    print "TM Halted!"
    print "Steps:    ", with_power(sim.cur_step_num)
    print "Non-Zeros:", with_power(sim.tape.get_nonzeros())

if __name__ == "__main__":
  import sys

  # No recursive flag
  if "-a" in sys.argv:
    sys.argv.remove("-a")
    level = 2
  elif "-r" in sys.argv:
    sys.argv.remove("-r")
    level = 3
  else:
    level = 4
  # Debug flag
  if "-d" in sys.argv:
    sys.argv.remove("-d")
    DEBUG = True

  if len(sys.argv) > 3:
    num = int(sys.argv[3])
  else:
    num = 1

  run(int(sys.argv[1]), sys.argv[2], num, level)
