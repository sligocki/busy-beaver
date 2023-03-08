"""
Class for managing direct simulations (non-chain tape).
"""

import argparse
import collections
import time

import Common
import IO
from Macro import Turing_Machine


class DirectTape:
  def __init__(self, init_symbol):
    self.init_symbol = init_symbol

    # Internal storage
    self.tape = collections.deque([self.init_symbol])
    self.index = 0

    # Exposed position relative to start position.
    # - is Left, + is Right.
    self.position = 0

  def pos2index(self, pos):
    return pos - self.position + self.index

  def read(self, pos=None):
    if pos == None:
      index = self.index
    else:
      index = self.pos2index(pos)
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
        self.tape.append(self.init_symbol)
    else:  # Left
      self.position -= 1
      self.index -= 1
      # Expand tape if necessary
      if self.index < 0:
        self.tape.appendleft(self.init_symbol)
        self.index += 1

  def copy(self):
    new_tape = DirectTape(self.init_symbol)
    new_tape.tape = self.tape.copy()
    new_tape.index = self.index
    new_tape.position = self.position
    return new_tape

  def in_range(self, pos):
    return (0 <= self.pos2index(pos) < len(self.tape))

  def count_nonzero(self):
    return sum(1 for symb in self.tape if symb != self.init_symbol)


class DirectSimulator:
  def __init__(self, tm : Turing_Machine.Simple_Machine, *,
               initialize : bool = True, blank_init_symbol : bool = False):
    self.tm = tm

    if initialize:
      self.halted = False
      self.state = tm.init_state

      init_symbol = tm.init_symbol if not blank_init_symbol else None
      self.tape = DirectTape(init_symbol = init_symbol)

      self.step_num = 0

  def copy(self):
    new_sim = DirectSimulator(self.tm, initialize=False)
    new_sim.state = self.state
    new_sim.halted = self.halted
    new_sim.tape = self.tape.copy()
    new_sim.step_num = self.step_num
    return new_sim

  def step(self):
    if not self.halted:
      state_in = self.state
      symbol_in = self.tape.read()
      trans = self.tm.trans_table[state_in][symbol_in]

      self.tape.write(trans.symbol_out)
      self.tape.move(trans.dir_out)
      self.state = trans.state_out
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


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm_file")
  parser.add_argument("record_num", type=int, nargs="?", default=0)
  parser.add_argument("num_steps", type=int)
  args = parser.parse_args()

  tm = IO.load_tm(args.tm_file, args.record_num)
  print(tm.ttable_str())
  sim = DirectSimulator(tm)

  start_time = time.time()
  sim.seek(args.num_steps)
  print(f"Simulated {sim.step_num:_} steps in {time.time() - start_time:_.1f}s")

if __name__ == "__main__":
  main()
