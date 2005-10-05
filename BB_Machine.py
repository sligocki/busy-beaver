"""
Contains Busy Beaver BB_Machine class.
"""

class BB_Machine:
  """
  Class for creating and storing Busy Beaver Machines which may include blank
  or to-be-completed cells in their transition tables.
  """
  def __init__(self, num_states, num_symbols):
    """
    Creates a machine with all but the first cell empty.
    """
    self.num_states  = num_states
    self.num_symbols = num_symbols

    self._TTable = [None] * self.num_states
    for state in range(self.num_states):
      self._TTable[state] = [(-1, 0, -1)] * num_symbols
    self._TTable[0][0] = (1, 1, 1)
    self.max_state  = 1
    self.max_symbol = 1
    self.num_empty_cells = self.num_states * self.num_symbols - 1

  def getTTable(self):
    """
    Returns the transition table in tuple format.
    """
    return self._TTable

  def setTTable(self, table):
    """
    Sets the transition table in tuple format.
    """
    self._TTable = table

  def getNumStatesAvailable(self):
    # self.num_states - 1 because that is the largest state number
    if self.max_state < self.num_states - 1:
      return self.max_state + 1
    else:
      return self.num_states - 1

  def getNumSymbolsAvailable(self):
    # self.num_symbol - 1 because that is the largest symbol number
    if self.max_symbol < self.num_symbols - 1:
      return self.max_symbol + 1
    else:
      return self.num_symbols - 1

  def AddCell(self, state_in, symbol_in, state_out, symbol_out, direction_out):
    if self._TTable[state_in][symbol_in][0] == -1:
      self.num_empty_cells -= 1
    self._TTable[state_in][symbol_in] = (symbol_out, direction_out, state_out)
    self.max_state = max(self.max_state, state_out)
    self.max_symbol = max(self.max_symbol, symbol_out)
