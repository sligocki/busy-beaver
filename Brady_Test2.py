#! /usr/bin/env python
# Store tape as runs (i.e. ...0011121222200... -> 0^inf 1^3 2^1 1^1 2^4 0^inf)
# Input or hard-code rules on runs (inferece rules)

from Turing_Machine import Turing_Machine

class Turing_Machine_Sim:
  """
  Class for simulating Turing Machines.
  Initialized by a Turing Machine and an initial tape.
  """
  def __init__(self, machine, tape = None, state = 0):
    self.machine = machine
    if not tape:
      tape = Tape()
    self.tape = tape
    self.state = state
    self.symbol = self.tape.cur_symbol
    self.step_num = 0

    self.rule = self.norm = 0

  def run(self, step_cutoff):
    while self.step_num < step_cutoff:
      # If we are in the halt state, return (Success).
      if self.state == -1:
        return True

      # Try inference rules.
      symbol2write, direction, next_state = self.get_current_cell()
      next_symbol = self.tape.dir[direction].top.symbol
      # If the next transition will be the same this one, macro-step.
      if self.state == next_state and self.symbol == next_symbol:
        # Pop the run of symbols that will all be traveled over.
        run = self.tape.dir[direction].pop()
        # Travel over them.
        self.step_num += run.num
        # Write the appropriate symbol.
        run.symbol = symbol2write
        # Push that run of symbols onto the other side.
        if self.tape.dir[not direction].top.symbol == run.symbol:
          if self.tape.dir[not direction].top.num != -1:
            self.tape.dir[not direction].top.num += run.num
        else:
          self.tape.dir[not direction].push(run)
        # Note that we applied a rule.
        self.rule += 1
        # And move on.
        continue

      # If inference rules failed, do single step.
      self.step()
      self.norm += 1

    # TM has not halted.
    return False

  def step(self):
    """Applies a single step in running the TM."""
    if self.state == -1:
      raise ValueError
    symbol, direction, state = self.get_current_cell()
    # Write symbol and change position.
    if self.tape.dir[not direction].top.symbol == symbol:
      if self.tape.dir[not direction].top.num != -1:
        self.tape.dir[not direction].top.num += 1
    else:
      self.tape.dir[not direction].push(Tape_Node(symbol, 1))
    if self.tape.dir[direction].top.num != -1:
      self.tape.dir[direction].top.num -= 1
    self.tape.cur_symbol = self.tape.dir[direction].top.symbol
    if self.tape.dir[direction].top.num == 0:
      self.tape.dir[direction].pop()
  
    # Update symbol
    self.symbol = self.tape.cur_symbol
    # Change state.
    self.state = state
    # Increment number of steps taken
    self.step_num += 1

  def get_current_cell(self):
    """Gets the current cell from TM."""
    return self.machine.get_cell(self.state, self.symbol)

class Tape:
  """Class for a turing machine's tape."""
  def __init__(self):
    self.cur_symbol = 0
    self.right = Stack()
    self.left = Stack()
    self.dir = [self.left, self.right]

    self.right.push(Tape_Node(0, -1))
    self.left.push(Tape_Node(0, -1))

class Tape_Node:
  def __init__(self, symbol, num):
    self.symbol = symbol
    self.num = num
  def __repr__(self):
    return `self.symbol`+"^"+`self.num`

class Stack:
  def __init__(self):
    self.contents = []
  def push(self, item):
    self.contents.append(item)
    self.top = self.contents[-1]
  def pop(self):
    item = self.contents.pop(-1)
    try:
      self.top = self.contents[-1]
    except IndexError:
      self.top = None
    return item

if __name__ == "__main__":
  import time
  ttable = [[ [1, 1, 1], [2, 0, 0], [1, 1, 0], [1, 1, 0] ], [ [1, 0, 1], [1, 0, 0], [3, 1, 1], [1, 1, -1] ]]

  TM = Turing_Machine(ttable)
  sim = Turing_Machine_Sim(TM)
  success = False
  extent = 1
  while not success:
    success = sim.run(extent)
    print sim.step_num, sim.rule, sim.norm, time.clock()
    print sim.tape.left.contents, sim.state, sim.symbol, sim.tape.right.contents
    print
    #extent += 1
    extent *= 10
