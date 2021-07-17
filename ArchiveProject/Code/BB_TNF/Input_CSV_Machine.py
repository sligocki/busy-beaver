import csv

from Macro import Turing_Machine

class String_Machine_State(str):
  def print_with_dir(self, dir):
    return str(self)

class General_Turing_Machine(Turing_Machine.Turing_Machine):
  """Like Simple Turing Machine, but allows non-integer states and symbols."""
  def __init__(self, ttable, symbols, states):
    self.ttable = ttable
    self.init_symbol = symbols[0]
    self.init_state = String_Machine_State(states[0])
    self.init_dir = Turing_Machine.RIGHT
    self.num_symbols = len(symbols)
    self.num_states = len(states)

  def eval_symbol(self, symbol):
    if symbol != self.init_symbol:
      return 1
    else:
      return 0

  def eval_state(self, state):
    return 0

  def get_transition(self, symbol_in, state_in, dir_in):
    # Re-arrange order of transition.
    symbol_out, dir_out, state_out = self.ttable[state_in, symbol_in]
    trans = symbol_out, String_Machine_State(state_out), dir_out
    if state_out == Turing_Machine.HALT:
      return (Turing_Machine.HALT,), trans, 1
    elif state_out == Turing_Machine.UNDEFINED:
      return (Turing_Machine.UNDEFINED, (symbol_in, state_in)), trans, 1
    else:
      return (Turing_Machine.RUNNING,), trans, 1

def read_csv_to_table(filename):
  """Read file and load csv table into a python table (list of lists)."""
  f = open(filename, "rb")
  return [list(row) for row in csv.reader(f)]

def convert_table_to_machine(table):
  """Convert a raw table to full Turing_Machine class."""
  assert not table[0][0], table
  symbols = table[0][1:]  # Symbols names
  states = [row[0] for row in table[1:]]  # State names

  ttable = {}
  for symbol_index, symbol in enumerate(symbols):
    for state_index, state in enumerate(states):
      cell = table[state_index + 1][symbol_index + 1]
      if not cell:
        new_symbol = None
        new_dir = None
        new_state = Turing_Machine.UNDEFINED
      elif cell == "Halt":
        new_symbol = symbols[1]
        new_dir = Turing_Machine.RIGHT
        new_state = Turing_Machine.HALT
      else:
        new_symbol, new_dir, new_state = cell.split()
        if new_dir == "L":
          new_dir = Turing_Machine.LEFT
        else:
          assert new_dir == "R"
          new_dir = Turing_Machine.RIGHT
      ttable[state, symbol] = (new_symbol, new_dir, new_state)
  return General_Turing_Machine(ttable, symbols, states)

if __name__ == "__main__":
  import sys

  table = read_csv_to_table(sys.argv[1])
  machine = convert_table_to_machine(table)
  print machine.__dict__
