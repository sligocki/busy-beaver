#
# Turing_Machine_Sim_Py.py
#
"""
Contains a Python Turing Machine Simulation class as well as a Tape class used
by the sim.
"""

import copy

class Turing_Machine_Sim:
  """
  Class for simulating Turing Machines.
  Initialized by a Turing Machine and an initial tape.
  """
  def __init__(self, machine, tape = None, position = 0, state = 0):
    # Set read-only attributes which describe initial values of system.
    self.machine = machine
    if not tape:
      tape = Tape()
    self.initial_tape = tape
    self.initial_position = position
    self.initial_state = state
    # Set mutable attributes which will be altered as machine is progressed.
    self.restart()

  def __repr__(self):
    return "Turing_Machine_Sim(%s)" % repr((self.machine, self.tape,
                                            self.position, self.state))

  def restart(self):
    """Restarts Turing Machine to initial conditions."""
    self.tape = copy.deepcopy(self.initial_tape)
    self.position = self.initial_position
    self.state = self.initial_state
    self.symbol = self.tape[self.position]
    self.step_num = 0

  def seek(self, step_num):
    """Seeks a given step number in TM run."""
    if step_num >= self.step_num:
      self.run(step_num - self.step_num)
    elif step_num >= 0:
      self.restart()
      self.run(step_num)
    else:
      raise ValueError("Turing_Machine_Sim.seek -- step_num (%d) must not be negative" % step_num)

  def run(self, steps, pos_return = None):
    """
    Runs Turing Machine n steps further, until pos_return is reached or until
    machine halts whichever comes first.
    
    If pos_return is reached returns True, otherwise returns None.
    """
    if steps < 0:
      self.seek(self.step_num - steps)
    else:
      for i in range(steps):
        if not self.step():
          return
        if self.position == pos_return:
          return True

  def step(self):
    """Applies a single step in running the TM."""
    if self.state == -1:
      return False
    symbol, direction, state = self.get_current_cell()
    # Write symbol.
    self.tape[self.position] = symbol
    # Move one step in given direction.
    if direction:
      self.position += 1
    else:
      self.position -= 1
    # Update symbol
    self.symbol = self.tape[self.position]
    # Change state.
    self.state = state
    # Increment number of steps taken
    self.step_num += 1

  def get_current_cell(self):
    """
    Gets the current cell from TM.
    """
    return self.machine.get_cell(self.state, self.symbol)

class Tape:
  """Class for a turing machine's tape."""
  def __init__(self, start = 0, stop = 0, val = []):
    self.tape = {}
    self[start:stop] = val
  def left(self):
    """Return index of left-most non-zero item."""
    try:
      return min(self.tape.keys())
    except ValueError:
      return None
  def right(self):
    """Return index of right-most non-zero item."""
    try:
      return max(self.tape.keys())
    except ValueError:
      return None
  def __repr__(self):
    left  = self.left()
    right = self.right()
    if None in [left, right]:
      return "Tape()"
    else:
      return "Tape(%d, %d, %s)" % (left, right+1, repr(self[left : right+1]))
  def __cmp__(self, tape2):
    """Good for == and !=, but relatively meaningless for <, >, etc."""
    for key in self.tape:
      if self[key] != tape2[key]:
        return self[key] - tape2[key]
    return 0
  def __getitem__(self, pos):
    """Read symbol on tape at position.  Tape is assumed to have 0's
    everywhere not yet defined/set."""
    return self.tape.get(pos, 0)
  def __setitem__(self, pos, val):
    """Write symbol on tape at position."""
    if type(pos) in [int, int]:
      if val != 0:
        self.tape[pos] = val
      # if val == 0 and tape[pos] != 0
      elif pos in self.tape:
        del self.tape[pos]
    else:
      raise ValueError("Tape.__setitem__ -- index (%s) must be an integer." % repr(pos))
  def __delitem__(self, pos):
    self[pos] = 0
  def __getslice__(self, start, stop):
    """Read symbols on slice of tape."""
    return [self[i] for i in range(start, stop)]
  def __setslice__(self, start, stop, val):
    """Write symbols to slice of tape."""
    if len(val) != stop - start:
      raise ValueError("Slices must be replaced by lists of the same length")
    else:
      for i in range(stop - start):
        self[i + start] = val[i]
  def __len__(self):
    """Defined so that slices and negative indeces will work correctly."""
    return 0
