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

def other_dir(dir):
  if dir == LEFT:
    return RIGHT
  else:
    assert dir == RIGHT, dir
    return LEFT


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
      if self.condition == HALT:
        state = "Z"
      else:
        state = string.ascii_uppercase[self.state_out]
      return "%c%c%c" % (symbol, dir, state)

  def equals(self, other):
    # Note: We ignore metadata fields (num_base_steps, etc). This probably only
    # makes sense for use with Simple_Machines where those are trivial.
    return (self.condition == other.condition and
            self.symbol_out == other.symbol_out and
            self.state_out == other.state_out and
            self.dir_out == other.dir_out)


# TODO: Make max_loops configurable via command-line options.
def sim_limited(tm, state, start_tape, pos, dir, max_loops=10_000) -> Transition:
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
      # Brent's algorithm for loop detection:
      #   At various checkpoints we update old_config.
      #   With the exponential growth of next_config_save we guarantee that for
      #   any repeat which starts at `init_time` and has period `period`
      #   we'll detect the repeat by step `2 * max(init_time, period)`.
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


# Characters to use for states (end in "Z" so that halt is Z)
STATES = string.ascii_uppercase + string.ascii_lowercase + string.digits + "!@#$%^&*" + "Z"
SYMBOLS = string.digits + "-"
DIRS = "LRS-"

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
    result += "   | %c " % STATES[i]
    for j in range(len(trans_table[i])):
      result += "| "
      if trans_table[i][j].condition == UNDEFINED:
        result += "--- "
      else:
        result += "%c"   % SYMBOLS[trans_table[i][j].symbol_out]
        result += "%c"   % DIRS[trans_table[i][j].dir_out]
        result += "%c "  % STATES[trans_table[i][j].state_out]
    result += "|\n"

    result += "   +---"
    for j in range(len(trans_table[0])):
      result += "+-----"
    result += "+\n"

  result += "\n"

  return result


class Simple_Machine_State(int):
  """Wrapper provides a pretty-printer for a Turing machine's integer state."""
  def print_with_dir(self, dir):
    return self.__str__()

  def __str__(self):
    return STATES[self]

  def __repr__(self):
    return STATES[self]

class Simple_Machine(Turing_Machine):
  """The most general Turing Machine based off of a transition table"""
  def __init__(self, ttable, states, symbols):
    self.trans_table = ttable
    self.states = states
    self.symbols = symbols

    self.num_states = len(self.states)
    self.num_symbols = len(self.symbols)

    self.init_symbol = 0
    self.init_dir = RIGHT
    self.init_state = Simple_Machine_State(0)

  def get_trans_object(self, symbol_in, state_in, dir_in = None):
    # Note: Simple_Machine ignores dir_in.
    return self.trans_table[state_in][symbol_in]

  def ttable_str(self) -> str:
    row_strs = []
    for row in self.trans_table:
      row_strs.append("".join(trans.to_ttable_str()
                               for trans in row))
    return "_".join(row_strs)

  def eval_symbol(self, symbol):
    if symbol != self.init_symbol:
      return 1
    else:
      return 0

  def eval_state(self, state):
    return 0

  def list_base_states(self):
    return list(range(self.num_states))

def tm_from_quintuples(quints) -> Simple_Machine:
  # print("quints:", quints)
  # Load states and symbols in order.
  states = []
  symbols = []
  for (state_in, symbol_in, _, _, _) in quints:
    if state_in not in states:
      states.append(state_in)
    if symbol_in not in symbols:
      symbols.append(symbol_in)
  # print("states:", states)
  # print("symbols:", symbols)

  # Set all defined transitions.
  ttable = [[None for _ in symbols] for _ in states]
  for (state_in, symbol_in, symbol_out, dir_out, state_out) in quints:
    if symbol_out != None:
      # Convert all into integers
      state_in = states.index(state_in)
      symbol_in = symbols.index(symbol_in)
      symbol_out = symbols.index(symbol_out)

      if state_out < 0:
        condition = HALT
        condition_details = [(symbol_in, state_in)]
      else:
        condition = RUNNING
        condition_details = None
        state_out = states.index(state_out)

      ttable[state_in][symbol_in] = Transition(
        condition=condition, condition_details=condition_details,
        symbol_out=symbol_out,
        state_out=Simple_Machine_State(state_out),
        dir_out=dir_out,
        # For base TMs, single trans is always 1 step and only uses one state.
        num_base_steps=1, states_last_seen={state_in: 0})

  # Define "undefined" transitions (with metadata).
  for state_in in range(len(states)):
    for symbol_in in range(len(symbols)):
      if not ttable[state_in][symbol_in]:
        ttable[state_in][symbol_in] = Transition(
          condition = UNDEFINED,
          condition_details = [(symbol_in, state_in)],
          # Make all undefined transitions act like the default halt trans: 1RH
          symbol_out = 1,
          state_out = Simple_Machine_State(-1),
          dir_out = RIGHT,
          # For base TMs, single trans is always 1 step and only uses one state.
          num_base_steps=1, states_last_seen={state_in: 0})

  return Simple_Machine(ttable, states, symbols)


class Macro_Machine(Turing_Machine): pass

class Block_Symbol(tuple):
  """Wrapper for block symbols that defines a concise-printer."""
  def __repr__(self):
    # TODO: this assumes single digit sub-symbols
    return "".join((str(x) for x in self))

class OffsetStartState:
  """Dummy initial state for running block size with an offset (starting in
  the middle of a symbol)."""
  def __init__(self, state, offset):
    self.state = state
    self.offset = offset

class Block_Macro_Machine(Macro_Machine):
  """A derivative Turing Machine which simulates another machine clumping k-symbols together into a block-symbol"""
  MAX_TTABLE_CELLS = 100000

  def __init__(self, base_machine, block_size, offset=None,
               max_sim_steps_per_symbol=10_000):
    assert block_size > 0
    self.block_size = block_size
    self.base_machine = base_machine
    self.num_states = base_machine.num_states
    self.num_symbols = base_machine.num_symbols ** block_size
    # A lazy evaluation hashed macro transition table
    self.trans_table = {}
    self.init_dir = base_machine.init_dir
    # initial symbol is (0, 0, 0, ..., 0) not just 0
    self.init_symbol = Block_Symbol((base_machine.init_symbol,) * block_size)

    if offset:
      assert 0 < offset < block_size, offset
      self.init_state = OffsetStartState(base_machine.init_state, offset)
    else:
      self.init_state = base_machine.init_state

    # Maximum number of base-steps per macro-step evaluation w/o repeat
    # #positions (within block) * #states * #macro_symbols (base symbols ** block_size)
    self.max_steps = block_size * self.num_states * self.num_symbols
    self.max_cells = Block_Macro_Machine.MAX_TTABLE_CELLS
    self.max_sim_steps_per_symbol = max_sim_steps_per_symbol

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
    # One-off check for dealing with initial offset.
    if isinstance(macro_state_in, OffsetStartState):
      pos = macro_state_in.offset
      macro_state_in = macro_state_in.state

    elif macro_dir_in == RIGHT:
      pos = 0
    else:
      assert macro_dir_in == LEFT, macro_dir_in
      pos = self.block_size - 1

    trans = sim_limited(self.base_machine,
                        state=macro_state_in, dir=macro_dir_in,
                        start_tape=macro_symbol_in, pos=pos,
                        max_loops=self.max_sim_steps_per_symbol)

    # Convert symbol into the correct format.
    trans.symbol_out = Block_Symbol(trans.symbol_out)
    return trans


@total_ordering
class Backsymbol_Macro_Machine_State:
  def __init__(self, base_state, back_symbol):
    assert isinstance(base_state, (Simple_Machine_State, OffsetStartState)), base_state
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
  def __init__(self, base_machine, max_sim_steps_per_symbol = 1_000):
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
    self.max_sim_steps_per_symbol = max_sim_steps_per_symbol

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
                        start_tape=tape, pos=pos,
                        max_loops=self.max_sim_steps_per_symbol)

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
