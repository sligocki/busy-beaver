"""
Class for managing direct simulations (non-chain tape).
"""

class DirectTape:
  def __init__(self, init_symbol, tape_increment=1000):
    self.init_symbol = init_symbol
    self.tape_increment = tape_increment

    # Internal storage
    self.tape = [self.init_symbol] * self.tape_increment
    self.index = len(self.tape) // 2

    # Exposed position relative to start position.
    # - is Left, + is Right.
    self.position = 0

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
      self.index += 1
      # Expand tape if necessary
      if self.index >= len(self.tape):
        self.tape += [self.init_symbol] * self.tape_increment
    else:  # Left
      self.position -= 1
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
    return new_tape

  def in_range(self, pos):
    index_pos_diff = self.index - self.position
    index = pos + index_pos_diff
    return (0 <= index < len(self.tape))


class DirectSimulator:
  def __init__(self, ttable):
    self.ttable = ttable

    self.state = 0  # Init state
    self.tape = DirectTape(init_symbol = 0)

    self.step_num = 0

  def step(self):
    state_in = self.state
    symbol_in = self.tape.read()
    symbol_out, dir_out, state_out = self.ttable[state_in][symbol_in]

    self.tape.write(symbol_out)
    self.tape.move(dir_out)
    self.state = state_out

    self.step_num += 1

  def seek(self, target_step_num):
    while self.step_num < target_step_num:
      self.step()
