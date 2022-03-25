"""
Class for managing direct simulations (non-chain tape).
"""

import Common


class DirectTape:
  def __init__(self, init_symbol, tape_increment=10):
    self.init_symbol = init_symbol
    self.tape_increment = tape_increment

    # Internal storage
    self.tape = [self.init_symbol] * self.tape_increment
    self.index = len(self.tape) // 2

    # Exposed position relative to start position.
    # - is Left, + is Right.
    self.position = 0
    self.pos_min = 0
    self.pos_max = 0

  def read(self, pos=None):
    if pos == None:
      index = self.index
    else:
      index_pos_diff = self.index - self.position
      index = pos + index_pos_diff
    if 0 <= index < len(self.tape):
      return self.tape[index]
    else:
      return self.init_symbol

  def write(self, symbol):
    self.tape[self.index] = symbol

  def move(self, dir):
    if dir:  # Right
      self.position += 1
      self.pos_max = max(self.pos_max, self.position)
      self.index += 1
      # Expand tape if necessary
      if self.index >= len(self.tape):
        self.tape += [self.init_symbol] * self.tape_increment
    else:  # Left
      self.position -= 1
      self.pos_min = min(self.pos_min, self.position)
      self.index -= 1
      # Expand tape if necessary
      if self.index < 0:
        self.tape = [self.init_symbol] * self.tape_increment + self.tape
        self.index += self.tape_increment

  def copy(self):
    new_tape = DirectTape(self.init_symbol, self.tape_increment)
    new_tape.tape = self.tape[:]  # Copy tape
    new_tape.index = self.index
    new_tape.position = self.position
    new_tape.pos_min = self.pos_min
    new_tape.pos_max = self.pos_max
    return new_tape

  def in_range(self, pos):
    return (self.pos_min <= pos <= self.pos_max)

  def count_nonzero(self):
    return sum(1 for symb in self.tape if symb != self.init_symbol)


class DirectSimulator:
  def __init__(self, ttable, initialize = True,
               init_state = 0, init_symbol = 0):
    self.ttable = ttable

    if initialize:
      self.state = init_state
      self.halted = False
      self.tape = DirectTape(init_symbol = init_symbol)

      self.step_num = 0

  def copy(self):
    new_sim = DirectSimulator(self.ttable, initialize=False)
    new_sim.state = self.state
    new_sim.halted = self.halted
    new_sim.tape = self.tape.copy()
    new_sim.step_num = self.step_num
    return new_sim

  def step(self):
    if not self.halted:
      state_in = self.state
      symbol_in = self.tape.read()
      try:
        symbol_out, dir_out, state_out = self.ttable[state_in][symbol_in]
      except IndexError:
        print("Error", state_in, symbol_in, len(self.ttable), len(self.ttable[0]))
        raise

      self.tape.write(symbol_out)
      self.tape.move(dir_out)
      self.state = state_out
      if self.state == Common.HALT_STATE:
        self.halted = True
        self.halt_score = self.tape.count_nonzero()
        # Record which (state, symbol) -> Halt. Useful while enumerating TMs.
        self.halt_from_state = state_in
        self.halt_from_symbol = symbol_in

      self.step_num += 1

  def seek(self, target_step_num):
    while not self.halted and self.step_num < target_step_num:
      self.step()
