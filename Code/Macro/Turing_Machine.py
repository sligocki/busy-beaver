#
# Turing_Machine.py
#
"""
Abstract Turing Machine model with basic NxM TM and Macro-Machine derivatives
"""

from optparse import OptionParser, OptionGroup
import sys,string


def add_option_group(parser):
  """Add Turing_Machine options group to an OptParser parser object."""
  assert isinstance(parser, OptionParser)

  group = OptionGroup(parser, "Macro Machine options")

  group.add_option("-n", "--block-size", type=int, metavar="SIZE",
                   help="Block size to use in macro machine simulator "
                   "(default is to guess with the block_finder algorithm).")
  group.add_option("-b", "--no-backsymbol", dest="backsymbol",
                   action="store_false", default=True, 
                   help="Turn OFF backsymbol macro machine.")

  parser.add_option_group(group)


LEFT = 0
RIGHT = 1
STAY = 2

# Return Conditions:
RUNNING    = "Running"    # Machine still running normally
HALT       = "Halt"       # Machine halts in or directly after move
INF_REPEAT = "Inf_Repeat" # Machine proven not to halt within move
UNDEFINED  = "Undefined"  # Machine encountered undefined transition
TIME_OUT   = "Timeout"    # A timer expired


class Turing_Machine(object):
  """Abstract base for all specific Turing Machines

  Derived classes should define:
    Function: get_transition, eval_symbol, eval_state
    Constants: init_symbol, init_state, and init_dir, num_states, num_symbols"""
  def get_transition(self, symbol_in, state_in, dir_in):
    # Returns triple (condition, transition, stats)
    # Condition
    return NotImplemented

def make_machine(trans_table):
  """Generate a standard Turing Machine based on a transition table. Wraps any machine that has Stay with a macro machine."""
  machine = Simple_Machine(trans_table)
  # If there are any stay instructions, encapsulate this machine
  # TODO: There is a much more efficient rapper than block-1 macro machine.
  for row in trans_table:
    for state, dir, symbol in row:
      if dir == STAY:
        return Block_Macro_Machine(machine, 1)
  # Otherwise return the simple machine
  return machine


# Characters to use for states (end in "Z" so that halt is Z)
states = string.ascii_uppercase + string.ascii_lowercase + string.digits + "!@#$%^&*" + "Z"
symbols = string.digits + "-"
dirs = "LRS-"

def print_machine(machine):
  """
  Pretty-print the contents of the Turing machine.
  This method prints the state transition information
  (number to print, direction to move, next state) for each state
  but not the contents of the tape.
  """

  sys.stdout.write("\n")
  sys.stdout.write("Transition table:\n")
  sys.stdout.write("\n")

  TTable = machine.trans_table

  sys.stdout.write("       ")
  for j in xrange(len(TTable[0])):
    sys.stdout.write("+-----")
  sys.stdout.write("+\n")

  sys.stdout.write("       ")
  for j in xrange(len(TTable[0])):
    sys.stdout.write("|  %d  " % j)
  sys.stdout.write("|\n")

  sys.stdout.write("   +---")
  for j in xrange(len(TTable[0])):
    sys.stdout.write("+-----")
  sys.stdout.write("+\n")

  for i in xrange(len(TTable)):
    sys.stdout.write("   | %c " % states[i])
    for j in xrange(len(TTable[i])):
      sys.stdout.write("| ")
      if TTable[i][j][0] == -1 and \
         TTable[i][j][1] == -1 and \
         TTable[i][j][2] == -1:
        sys.stdout.write("--- ")
      else:
        sys.stdout.write("%c"   % symbols[TTable[i][j][0]])
        sys.stdout.write("%c"   % dirs   [TTable[i][j][1]])
        sys.stdout.write("%c "  % states [TTable[i][j][2]])
    sys.stdout.write("|\n")

    sys.stdout.write("   +---")
    for j in xrange(len(TTable[0])):
      sys.stdout.write("+-----")
    sys.stdout.write("+\n")

  sys.stdout.write("\n")

  sys.stdout.flush()


# Characters to use for states.
states = string.ascii_uppercase + string.ascii_lowercase + string.digits + "!@#$%^&*" + "Z"

class Simple_Machine_State(int):
  """Wrapper provides a pretty-printer for a Turing machine's integer state."""
  def print_with_dir(self, dir):
    return self.__str__()

  def __str__(self):
    return states[self]

  def __repr__(self):
    return states[self]

class Simple_Machine(Turing_Machine):
  """The most general Turing Machine based off of a transition table"""
  def __init__(self, trans_table):
    self.trans_table = trans_table
    self.num_states = len(trans_table)
    self.num_symbols = len(trans_table[0])
    self.init_state = Simple_Machine_State(0)
    self.init_dir = 1
    self.init_symbol = 0

  def eval_symbol(self, symbol):
    if symbol != self.init_symbol:
      return 1
    else:
      return 0

  def eval_state(self, state):
    return 0

  def get_transition(self, symbol_in, state_in, dir_in):
    # Historical ordering of transition table elements: (sym, dir, state)
    symbol_out, dir_out, state_out = self.trans_table[state_in][symbol_in]
    trans = symbol_out, Simple_Machine_State(state_out), dir_out
    # Historical signaling of undefined cell in transition table: (-1, 0, -1)
    if symbol_out == -1:
      # Treat an undefined cell as a halt, except note that it was undefined.
      return (UNDEFINED, (symbol_in, state_in)), (1, -1, 1), 1
    # Historical signaling of final cell (transition to halt): (1, 1, -1)
    elif state_out == -1:
      return (HALT,), trans, 1
    # Otherwise, the transition is normal
    else:
      return (RUNNING,), trans, 1

class Macro_Machine(Turing_Machine): pass

class Block_Symbol(tuple):
  """Wrapper for block symbols that defines a concise-printer."""
  def __repr__(self):
    # TODO: this assumes single digit sub-symbols
    return string.join((str(x) for x in self), "")

class Block_Macro_Machine(Macro_Machine):
  """A derivative Turing Machine which simulates another machine clumping k-symbols together into a block-symbol"""
  MAX_TTABLE_CELLS = 100000
  DUMMY_OFFSET_STATE = "Dummy_Offset_State"

  def __init__(self, base_machine, block_size, offset=None):
    assert block_size > 0
    self.block_size = block_size
    self.base_machine = base_machine
    self.num_states = base_machine.num_states
    self.num_symbols = base_machine.num_symbols ** block_size
    # A lazy evaluation hashed macro transition table
    self.trans_table = {}
    self.init_state = base_machine.init_state
    self.init_dir = base_machine.init_dir
    if offset:
      assert 0 < offset < block_size
      self.save = self.init_state, offset
      self.init_state = Block_Macro_Machine.DUMMY_OFFSET_STATE
    # initial symbol is (0, 0, 0, ..., 0) not just 0
    self.init_symbol = Block_Symbol((base_machine.init_symbol,) * block_size)
    # Maximum number of base-steps per macro-step evaluation w/o repeat
    # #positions * #states * #macro_symbols
    self.max_steps = block_size * self.num_states * self.num_symbols
    self.max_cells = Block_Macro_Machine.MAX_TTABLE_CELLS
    # Stat info
    self.num_loops = 0

  def eval_symbol(self, macro_symbol):
    return sum(map(self.base_machine.eval_symbol, macro_symbol))

  def eval_state(self, state):
    return self.base_machine.eval_state(state)

  def get_transition(self, *args):
    if args not in self.trans_table:
      if len(self.trans_table) >= self.max_cells:
        self.trans_table.clear()
      self.trans_table[args] = self.eval_trans(args)
    return self.trans_table[args]

  def eval_trans(self, (macro_symbol_in, macro_state_in, macro_dir_in)):
    # Set up machine
    num_steps = num_macro_steps = 0
    tape = list(macro_symbol_in)
    state = macro_state_in
    dir = macro_dir_in
    if macro_dir_in is RIGHT:
      pos = 0
    else:
      pos = self.block_size - 1
    # Deal with dummy offset case
    if state == Block_Macro_Machine.DUMMY_OFFSET_STATE:
      state, pos = self.save
    # Simulate Machine
    while 0 <= pos < self.block_size:
      symbol = tape[pos]
      cond, (symbol_out, state_out, dir_out), num_steps_out = \
            self.base_machine.get_transition(symbol, state, dir)
      num_steps += num_steps_out
      num_macro_steps += 1
      self.num_loops += 1
      tape[pos] = symbol_out
      state = state_out
      dir = dir_out
      if dir_out is RIGHT:
        pos += 1
      elif dir_out is LEFT:
        pos -= 1
      if cond[0] != RUNNING:
        return cond+(pos,), (Block_Symbol(tape), state, dir), num_steps
      if num_macro_steps > self.max_steps:
        return (INF_REPEAT, pos), (Block_Symbol(tape), state, dir), num_steps
    return (RUNNING,), (Block_Symbol(tape), state, dir), num_steps

class Backsymbol_Macro_Machine_State:
  def __init__(self,base_state,back_symbol):
    self.base_state  = base_state
    self.back_symbol = back_symbol

  def print_with_dir(self, dir):
    if dir == 0:
      return "%s (%s)" % (self.base_state.print_with_dir(dir),self.back_symbol)
    else:
      return "(%s) %s" % (self.back_symbol,self.base_state.print_with_dir(dir))
    return self.__repr__()

  def __repr__(self):
    return "(%s,%s)" % (self.base_state,self.back_symbol)

  # These must be defined so that we can check that two states are equal,
  # not equal, or use them as keys into a dictionary.
  def __cmp__(self, other):
    return cmp((self.base_state, self.back_symbol),
               (other.base_state, other.back_symbol))

  def __hash__(self):
    return hash((self.base_state, self.back_symbol))

def backsymbol_get_trans(tape, state, dir):
  backsymbol = tape[dir]
  return_symbol = tape[1 - dir]
  return return_symbol, Backsymbol_Macro_Machine_State(state, backsymbol), dir

class Backsymbol_Macro_Machine(Macro_Machine):
  MAX_TTABLE_CELLS = 100000
  def __init__(self, base_machine):
    self.base_machine = base_machine
    self.num_states = base_machine.num_states
    self.num_symbols = base_machine.num_symbols
    # A lazy evaluation hashed macro transition table
    self.trans_table = {}
    # States of macro machine are old states and symbol behind state
    self.init_state = Backsymbol_Macro_Machine_State(base_machine.init_state, base_machine.init_symbol)
    self.init_dir = base_machine.init_dir
    self.init_symbol = base_machine.init_symbol
    # Maximum number of base-steps per macro-step evaluation w/o repeat
    # #positions * #states * #symbols_in_front * #symbols_behind
    self.max_steps = 2 * self.num_states * self.num_symbols**2
    self.max_cells = Backsymbol_Macro_Machine.MAX_TTABLE_CELLS
    # Stats
    self.num_loops = 0

  def eval_symbol(self, symbol):
    return self.base_machine.eval_symbol(symbol)

  def eval_state(self, backsymbol_macro_machine_state):
    return self.base_machine.eval_state(backsymbol_macro_machine_state.base_state) + self.base_machine.eval_symbol(backsymbol_macro_machine_state.back_symbol)

  def get_transition(self, *args):
    if args not in self.trans_table:
      if len(self.trans_table) >= self.max_cells:
        self.trans_table.clear()
      self.trans_table[args] = self.eval_trans(args)
    return self.trans_table[args]

  def eval_trans(self, (macro_symbol_in, macro_state_in, macro_dir_in)):
    # Set up machine
    num_steps = num_macro_steps = 0
    state = macro_state_in.base_state
    back_macro_symbol = macro_state_in.back_symbol
    dir = macro_dir_in
    if macro_dir_in is RIGHT:
      tape = [back_macro_symbol, macro_symbol_in]
      pos = 1
    else:
      tape = [macro_symbol_in, back_macro_symbol]
      pos = 0
    # Simulate Machine
    while 0 <= pos < 2:
      symbol = tape[pos]
      cond, (symbol_out, state_out, dir_out), num_steps_out = \
            self.base_machine.get_transition(symbol, state, dir)
      num_steps += num_steps_out
      num_macro_steps += 1
      self.num_loops += 1
      tape[pos] = symbol_out
      state = state_out
      dir = dir_out
      if dir_out is RIGHT:
        pos += 1
      elif dir_out is LEFT:
        pos -= 1
      if cond[0] != RUNNING:
        trans = backsymbol_get_trans(tape, state, dir)
        return cond+(pos,), trans, num_steps
      if num_macro_steps > self.max_steps:
        trans = backsymbol_get_trans(tape, state, dir)
        return (INF_REPEAT, pos), trans, num_steps
    # If we just ran off of the tape, we are still running
    trans = backsymbol_get_trans(tape, state, dir)
    return (RUNNING,), trans, num_steps
