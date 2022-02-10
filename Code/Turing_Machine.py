#
# Turing_Machine.py
#
"""
Contains Busy Beaver Turing_Machine class.
"""

import sys, string

class Turing_Machine_Runtime_Error:
  """
  This exception class is raised if an error occurs while running/simulating a
  turing machine (currently done in c-code).
  """

  def __init__(self, value=None):
    self.value = value

  def __repr__(self):
    return `self.value`


class Filter_Unexpected_Return:
  """
  This exception class is raised if an unexpected value is returned from a
  filter.  This will generaly mean that an undefined cell was found.
  """

  def __init__(self, value=None):
    self.value = value

  def __repr__(self):
    return `self.value`


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


class Turing_Machine:
  """
  Class for creating and storing Busy Beaver Machines which may include blank
  or to-be-completed cells in their transition tables.
  """
  def __init__(self, *args):
    # Turing_Machine(ttable)
    if len(args) == 1:
      self.set_TTable(*args)
    # Turing_Machine(num_states, num_symbols)
    elif len(args) in (2, 3):
      self.empty_init(*args)
    else:
      raise ValueError, "Turing_Machine(args) - Takes 1 or 2 args"

  def empty_init(self, num_states, num_symbols, first_1rb=True):
    """
    Creates a machine with all but the first cell empty.
    """
    self.num_states  = num_states
    self.num_symbols = num_symbols

    self.trans_table = [None] * self.num_states
    for state in range(self.num_states):
      self.trans_table[state] = [(-1, 0, -1)] * num_symbols
    self.num_empty_cells = self.num_states * self.num_symbols
    self.max_state  = 0
    self.max_symbol = 0
    # Only allow one direction for the first trans.
    self.num_dirs_available = 1

    if first_1rb:
      self.set_cell(0, 0, 1, 1, 1)  # A1 -> 1RB
      self.trans_table[0][0] = (1, 1, 1)

  def __repr__(self):
    return "Turing_Machine(%s)" % repr(self.trans_table)

  def __str__(self):
    string = ""
    for state in self.trans_table:
      for symbol in state:
        string += "%-12s" % str(symbol)
      string += "\n"
    return string

  def get_TTable(self):
    """
    Returns the transition table in tuple format.
    """
    return self.trans_table

  def set_TTable(self, table):
    """
    Sets the transition table in tuple format and updates object to be
    consistent with transition table
    """
    self.trans_table = table

    self.num_states  = len(table)
    self.num_symbols = len(table[0])
    self.num_dirs_available = 2

    self.max_state  = -1
    self.max_symbol = -1

    self.num_empty_cells = 0

    for symbol_list in table:
      for element in symbol_list:
        if element[0] > self.max_symbol:
          self.max_symbol = element[0]

        if element[2] > self.max_state:
          self.max_state = element[2]

        if element[0] == -1:
          self.num_empty_cells += 1

  def get_num_states_available(self):
    # Returns state num of largest state available.
    # This will be the max(states_reached) + 1 unless we're already
    # Note: self.num_states - 1 is the largest possible state number.
    largest = self.num_states - 1
    if self.max_state < largest:
      return self.max_state + 1
    else:
      return largest

  def get_num_symbols_available(self):
    # Returns state num of largest state available.
    # This will be the max(states_reached) + 1 unless we're already
    # Note: self.num_symbols - 1 is the largest possible symbol number.
    largest = self.num_symbols - 1
    if self.max_symbol < largest:
      return self.max_symbol + 1
    else:
      return largest

  def is_cell_empty(self, state_in, symbol_in):
    # Empty (unset) cells are represented by symbol = -1.
    return (self.trans_table[state_in][symbol_in][0] == -1)

  def get_cell(self, state_in, symbol_in):
    return self.trans_table[state_in][symbol_in]

  def add_cell(self, *args):
    return self.set_cell(*args)
  def set_cell(self, state_in, symbol_in, state_out, symbol_out, direction_out):
    # If this cell was empty, decriment num_empty_cells
    if self.is_cell_empty(state_in, symbol_in):
      self.num_empty_cells -= 1
    # Actually add the cell information.
    self.trans_table[state_in][symbol_in] = (symbol_out, direction_out, state_out)
    # Update max value information.
    self.max_state = max(self.max_state, state_out)
    self.max_symbol = max(self.max_symbol, symbol_out)
    self.num_dirs_available = 2

  def set_halt(self, state_in, symbol_in):
    # Halt is canoncially represented as 1RZ (state = -1, symbol = 1).
    return self.set_cell(state_in, symbol_in, -1, 1, 1)
