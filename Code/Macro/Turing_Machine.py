#
# Turing_Machine.py
#
"""
Abstract Turing Machine model with basic NxM TM and Macro-Machine derivatives
"""

from functools import total_ordering
from optparse import OptionParser, OptionGroup
import sys
import string


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
GAVE_UP   = "Gave_Up"     # For some reason, we bailed on computation (maybe too many steps).


class Transition(object):
  """Class representing the result of a transition."""
  def __init__(self,
               condition,
               symbol_out, state_out, dir_out,
               num_base_steps, states_last_seen,
               condition_details = None):
    self.condition = condition
    self.condition_details = condition_details if condition_details else []
    self.symbol_out = symbol_out
    self.state_out = state_out
    self.dir_out = dir_out
    self.num_base_steps = num_base_steps
    self.states_last_seen = states_last_seen

  # TODO: Deprecate
  def to_legacy_tuple(self):
    """Return legacy tuple-form of transition."""
    return (tuple([self.condition] + self.condition_details),
            (self.symbol_out, self.state_out, self.dir_out),
            self.num_base_steps)

  def to_ttable_str(self):
    if self.condition == UNDEFINED:
      return "---"
    else:
      symbol = string.digits[self.symbol_out]
      dir = "LRS"[self.dir_out]
      # Note: We use Python magic to convert state -1 (Halt) into "Z".
      state = string.ascii_uppercase[self.state_out]
      return "%c%c%c" % (symbol, dir, state)


# TODO: Make max_loops configurable via command-line options.
def sim_limited(tm, state, start_tape, pos, dir, max_loops=10000):
  """Simulate TM on a limited tape segment.
  Can detect HALT and INF_REPEAT. Used by Macro Machines."""
  # num_base_steps in the bottom level Simple_Machine.
  num_base_steps = 0
  # num_loops is the # steps simulated in this function.
  num_loops = 0
  tape = list(start_tape)
  states_last_seen = {}

  # Once we run long enough use this to detect repeat-in-place.
  # If `old_config` is ever repeated, we know it will repeat forever.
  # Format: (state, dir, pos, tape)
  old_config = None
  # Arbitrarily start looking for repeats after ~100 steps (~0.1ms).
  next_config_save = 128

  # Simulate Machine on macro symbol
  while True:
    symbol = tape[pos]
    trans = tm.get_trans_object(symbol, state, dir)
    for state, base_last_seen in trans.states_last_seen.items():
      states_last_seen[state] = num_base_steps + base_last_seen
    num_base_steps += trans.num_base_steps
    num_loops += 1
    tape[pos] = trans.symbol_out
    state = trans.state_out
    dir = trans.dir_out
    if dir == RIGHT:
      pos += 1
    elif dir == LEFT:
      pos -= 1

    if (state, dir, pos, tape) == old_config:
      # Found a repeated config.
      condition = INF_REPEAT
      condition_details = [pos]
      break
    if num_loops >= next_config_save:
      # At various checkpoints we update old_config.
      # With the exponential growth of next_config_save we guarantee that for
      # any repeat which starts at `init_time` and has period `period`
      # we'll detect the repeat by step `2 * max(init_time, period)`.
      old_config = (state, dir, pos, list(tape))
      next_config_save *= 2

    if num_loops > max_loops:
      # Simulation ran too long, we give up.
      condition = GAVE_UP
      condition_details = [num_loops]
      break

    if trans.condition != RUNNING:
      # Base machine stopped running (HALT, INF_REPEAT, etc.)
      condition = trans.condition
      condition_details = trans.condition_details + [pos]
      break
    if not (0 <= pos < len(tape)):
      # We ran off one end of the macro symbol. We're done.
      condition = RUNNING
      condition_details = None
      break

  return Transition(
    condition=condition, condition_details=condition_details,
    # NOTE: We return the tape as `symbol_out` which is roughly right for
    # Block_Macro_Machine, but Backsymbol_Macro_Machine will need to modify
    # this and state_out.
    symbol_out=tape, state_out=state, dir_out=dir,
    num_base_steps=num_base_steps, states_last_seen=states_last_seen)


class Turing_Machine(object):
  """Abstract base for all specific Turing Machines

  Derived classes should define:
    Function: get_transition, eval_symbol, eval_state
    Constants: init_symbol, init_state, and init_dir, num_states, num_symbols"""

  # TODO: Deprecate
  def get_transition(self, symbol_in, state_in, dir_in):
    """Returns legacy tuple for now."""
    return self.get_trans_object(symbol_in, state_in, dir_in).to_legacy_tuple()

  def get_trans_object(self, symbol_in, state_in, dir_in):
    """Returns Transition object."""
    return NotImplemented

  def list_base_states(self):
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

def machine_ttable_to_str(machine):
  """
  Pretty-print the contents of the Turing machine.
  This method prints the state transition information
  (number to print, direction to move, next state) for each state
  but not the contents of the tape.
  """

  result = ""

  result += "\n"
  result += "Transition table:\n"
  result += "\n"

  trans_table = machine.trans_table

  result += "       "
  for j in range(len(trans_table[0])):
    result += "+-----"
  result += "+\n"

  result += "       "
  for j in range(len(trans_table[0])):
    result += "|  %d  " % j
  result += "|\n"

  result += "   +---"
  for j in range(len(trans_table[0])):
    result += "+-----"
  result += "+\n"

  for i in range(len(trans_table)):
    result += "   | %c " % states[i]
    for j in range(len(trans_table[i])):
      result += "| "
      if trans_table[i][j].condition == UNDEFINED:
        result += "--- "
      else:
        result += "%c"   % symbols[trans_table[i][j].symbol_out]
        result += "%c"   % dirs   [trans_table[i][j].dir_out]
        result += "%c "  % states [trans_table[i][j].state_out]
    result += "|\n"

    result += "   +---"
    for j in range(len(trans_table[0])):
      result += "+-----"
    result += "+\n"

  result += "\n"

  return result


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

def ttable_to_transition(TTable, state_in, symbol_in):
  """Convert from historical TTable trans format tuple (sym, dir, state) to
  a Transition object."""
  # Historical ordering of transition table elements: (sym, dir, state)
  symbol_out, dir_out, state_out = TTable[state_in][symbol_in]

  # Historical signaling of undefined cell in transition table: (-1, 0, -1)
  if symbol_out == -1:
    # Treat an undefined cell as a halt, except note that it was undefined.
    condition = UNDEFINED
    condition_details = [(symbol_in, state_in)]
    symbol_out = 1; state_out = -1; dir_out = RIGHT
  # Historical signaling of final cell (transition to halt): (1, 1, -1)
  elif state_out == -1:
    condition = HALT
    condition_details = [(symbol_in, state_in)]
  # Otherwise, the transition is normal
  else:
    condition = RUNNING
    condition_details = None

  return Transition(
    condition=condition, condition_details=condition_details,
    symbol_out=symbol_out,
    state_out=Simple_Machine_State(state_out),
    dir_out=dir_out,
    # For base TMs, single trans is always 1 step and only uses one state.
    num_base_steps=1, states_last_seen={state_in: 0})

class Simple_Machine(Turing_Machine):
  """The most general Turing Machine based off of a transition table"""
  def __init__(self, TTable):
    self.num_states = len(TTable)
    self.num_symbols = len(TTable[0])
    self.init_state = Simple_Machine_State(0)
    self.init_dir = RIGHT
    self.init_symbol = 0

    # Convert from raw (historical) TTable to a table which returns
    # a Transition object.
    self.trans_table = [[None for _ in range(self.num_symbols)]
                        for _ in range(self.num_states)]
    for state_in in range(self.num_states):
      for symbol_in in range(self.num_symbols):
        self.trans_table[state_in][symbol_in] = \
          ttable_to_transition(TTable, state_in, symbol_in)

  def ttable_str(self):
    row_strs = []
    for row in self.trans_table:
      row_strs.append(" ".join(trans.to_ttable_str()
                               for trans in row))
    return "  ".join(row_strs)

  def eval_symbol(self, symbol):
    if symbol != self.init_symbol:
      return 1
    else:
      return 0

  def eval_state(self, state):
    return 0

  def list_base_states(self):
    return list(range(self.num_states))

  def get_trans_object(self, symbol_in, state_in, dir_in = None):
    # Note: Simple_Machine ignores dir_in.
    return self.trans_table[state_in][symbol_in]

class Macro_Machine(Turing_Machine): pass

class Block_Symbol(tuple):
  """Wrapper for block symbols that defines a concise-printer."""
  def __repr__(self):
    # TODO: this assumes single digit sub-symbols
    return "".join((str(x) for x in self))

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
    # #positions (within block) * #states * #macro_symbols (base symbols ** block_size)
    self.max_steps = block_size * self.num_states * self.num_symbols
    self.max_cells = Block_Macro_Machine.MAX_TTABLE_CELLS

  def eval_symbol(self, macro_symbol):
    return sum(map(self.base_machine.eval_symbol, macro_symbol))

  def eval_state(self, state):
    return self.base_machine.eval_state(state)

  def list_base_states(self):
    return self.base_machine.list_base_states()

  def get_trans_object(self, *args):
    if args not in self.trans_table:
      if len(self.trans_table) >= self.max_cells:
        self.trans_table.clear()
      self.trans_table[args] = self.eval_trans(*args)
    return self.trans_table[args]

  def eval_trans(self, macro_symbol_in, macro_state_in, macro_dir_in):
    if macro_dir_in == RIGHT:
      pos = 0
    else:
      assert macro_dir_in == LEFT, macro_dir_in
      pos = self.block_size - 1

    trans = sim_limited(self.base_machine,
                        state=macro_state_in, dir=macro_dir_in,
                        start_tape=macro_symbol_in, pos=pos)

    # Convert symbol into the correct format.
    trans.symbol_out = Block_Symbol(trans.symbol_out)
    return trans


@total_ordering
class Backsymbol_Macro_Machine_State:
  def __init__(self, base_state, back_symbol):
    assert isinstance(base_state, Simple_Machine_State), base_state
    self.base_state  = base_state
    self.back_symbol = back_symbol

  def print_with_dir(self, dir):
    if dir == LEFT:
      return "%s (%s)" % (self.base_state.print_with_dir(dir),self.back_symbol)
    else:
      return "(%s) %s" % (self.back_symbol,self.base_state.print_with_dir(dir))

  def __repr__(self):
    return "(%s,%s)" % (self.base_state,self.back_symbol)

  # These must be defined so that we can check that two states are equal,
  # not equal, or use them as keys into a dictionary.
  def __eq__(self, other):
    return (self.base_state == other.base_state and
            self.back_symbol == other.back_symbol)

  # Define __lt__ so that we can sort backstates.
  def __lt__(self, other):
    return (self.base_state, self.back_symbol) < (other.base_state, other.back_symbol)

  def __hash__(self):
    return hash((self.base_state, self.back_symbol))

class Backsymbol_Macro_Machine(Macro_Machine):
  MAX_TTABLE_CELLS = 100000
  def __init__(self, base_machine):
    self.base_machine = base_machine
    self.num_states = base_machine.num_states
    self.num_symbols = base_machine.num_symbols
    # A lazy evaluation hashed macro transition table
    self.trans_table = {}
    # States of macro machine are old states and symbol behind state
    self.init_state = Backsymbol_Macro_Machine_State(base_machine.init_state,
                                                     base_machine.init_symbol)
    self.init_dir = base_machine.init_dir
    self.init_symbol = base_machine.init_symbol
    # Maximum number of base-steps per macro-step evaluation w/o repeat
    # #positions (2) * #states * #symbols_in_front * #symbols_behind
    self.max_steps = 2 * self.num_states * self.num_symbols**2
    self.max_cells = Backsymbol_Macro_Machine.MAX_TTABLE_CELLS

  def eval_symbol(self, symbol):
    return self.base_machine.eval_symbol(symbol)

  def eval_state(self, backsymbol_macro_machine_state):
    return self.base_machine.eval_state(backsymbol_macro_machine_state.base_state) + self.base_machine.eval_symbol(backsymbol_macro_machine_state.back_symbol)

  def list_base_states(self):
    return self.base_machine.list_base_states()

  def get_trans_object(self, *args):
    if args not in self.trans_table:
      if len(self.trans_table) >= self.max_cells:
        self.trans_table.clear()
      self.trans_table[args] = self.eval_trans(*args)
    return self.trans_table[args]

  def eval_trans(self, macro_symbol_in, macro_state_in, macro_dir_in):
    if macro_dir_in == RIGHT:
      tape = [macro_state_in.back_symbol, macro_symbol_in]
      pos = 1
    else:
      assert macro_dir_in == LEFT, macro_dir_in
      tape = [macro_symbol_in, macro_state_in.back_symbol]
      pos = 0

    trans = sim_limited(self.base_machine,
                        state=macro_state_in.base_state, dir=macro_dir_in,
                        start_tape=tape, pos=pos)

    # sim_limited just leaves the final tape in `trans.symbol_out`, we
    # need to split out the backsymbol and printed_symbol ourselves.
    final_tape = trans.symbol_out

    if trans.dir_out == RIGHT:
      # [0, 1], A, RIGHT -> 0 (1)A>
      symbol_out, backsymbol = final_tape
    else:
      # [0, 1], A, LEFT -> <A(0) 1
      assert trans.dir_out == LEFT, trans.dir_out
      backsymbol, symbol_out = final_tape

    # Update symbol_out and state_out to be backsymbol-style.
    trans.symbol_out = symbol_out
    trans.state_out = Backsymbol_Macro_Machine_State(trans.state_out,
                                                     backsymbol)

    return trans
