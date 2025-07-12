import copy

from Macro import Turing_Machine


def blank_tm_enum(num_states : int, num_symbols : int,
                  *, first_1rb : bool, allow_no_halt : bool,
                  max_transitions : int | None = None):
  quints = []
  if first_1rb:
    quints.append((0, 0, 1, 1, 1))  # A1 -> 1RB

  tm = Turing_Machine.tm_from_quintuples(quints, states = list(range(num_states)),
                                         symbols = list(range(num_symbols)))
  return TM_Enum(tm, allow_no_halt=allow_no_halt, max_transitions=max_transitions)

class TM_Enum:
  """Collection of TM (Turing_Machine.Simple_Machine) and enumeration
  information (config and state needed to perform Brady's TNF algorithm)."""

  def __init__(self, tm : Turing_Machine.Simple_Machine,
               *, allow_no_halt : bool, max_transitions : int | None = None):
    self.tm = tm
    # Options
    if max_transitions:
      self.max_transitions = max_transitions
    elif allow_no_halt:
      self.max_transitions = tm.num_states * tm.num_symbols
    else:
      self.max_transitions = tm.num_states * tm.num_symbols - 1

  def set_trans(self, *, state_in, symbol_in, symbol_out, dir_out, state_out):
    self.tm.trans_table[state_in][symbol_in] = Turing_Machine.Transition(
      condition=Turing_Machine.RUNNING, condition_details=None,
      symbol_out = symbol_out, dir_out = dir_out,
      state_out = Turing_Machine.Simple_Machine_State(state_out),
      # For base TMs, single trans is always 1 step and only uses one state.
      num_base_steps=1, states_last_seen={state_in: 0})

  def set_halt_trans(self, *, state_in, symbol_in):
    # Standard halt transition is -> 1RZ
    self.tm.trans_table[state_in][symbol_in] = Turing_Machine.Transition(
      condition=Turing_Machine.HALT, condition_details=[(symbol_in, state_in)],
      symbol_out=1, dir_out=Turing_Machine.RIGHT,
      state_out=Turing_Machine.Simple_Machine_State(-1),  # Halt
      # For base TMs, single trans is always 1 step and only uses one state.
      num_base_steps=1, states_last_seen={state_in: 0})

  def enum_children(self, state_in, symbol_in):
    """Enumerate TM_Enum "children" of this node by filling in all possible
    values for transition `state_in` `symbol_in` allowed by TNF."""
    # Evaluate a few metrics
    max_state = 0
    max_symbol = 0
    num_def_trans = 0
    for state in range(self.tm.num_states):
      for symbol in range(self.tm.num_symbols):
        trans = self.tm.get_trans_object(state_in = state,
                                         symbol_in = symbol)
        if trans.condition != Turing_Machine.UNDEFINED:
          num_def_trans += 1
          max_state = max(max_state, trans.state_out)
          max_symbol = max(max_symbol, trans.symbol_out)

    if num_def_trans > 0:
      num_dirs = 2
    else:
      # If no transitions are defined yet, always force first trans to be to
      # the RIGHT.
      num_dirs = 1

    # TNF algorithm allows us to use up to 1 more than the max state (and symbol)
    # seen so far (maxing out at the total number of states/symbols for this TM).
    num_states = min(self.tm.num_states, max_state + 2)
    num_symbols = min(self.tm.num_symbols, max_symbol + 2)

    # Enumerate
    # If this is the last undefined transition (and not allow_no_halt) then
    # there's nothing left to do, this trans can only be a halting trans.
    if num_def_trans < self.max_transitions:
      for state_out in range(num_states):
        for symbol_out in range(num_symbols):
          # If only one dir available, default to RIGHT.
          for dir_out in range(2 - num_dirs, 2):
            new_tm_enum = copy.deepcopy(self)
            new_tm_enum.set_trans(
              state_in = state_in, symbol_in = symbol_in,
              symbol_out = symbol_out, dir_out = dir_out, state_out = state_out)
            yield new_tm_enum
