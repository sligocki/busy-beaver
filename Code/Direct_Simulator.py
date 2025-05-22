"""
Class for managing direct simulations (non-chain tape).
"""

from __future__ import annotations

import argparse
import collections
from dataclasses import dataclass
import time

import Common
import IO
from Macro.Turing_Machine import Simple_Machine as TM
from Macro.Turing_Machine import Simple_Machine_State as State
from Macro.Turing_Machine import Symbol


@dataclass(frozen=True)
class SymbolOrBlank:
  value : Symbol
  is_initial : bool

  def __str__(self) -> str:
    if self.is_initial:
      return "_"
    else:
      return str(self.value)

class DirectTape:
  def __init__(self, init_symbol : Symbol):
    self.init_symbol = SymbolOrBlank(init_symbol, True)

    # Internal storage
    self.tape = collections.deque([self.init_symbol])
    self.index = 0

    # We do not expose index (which is an implementation detail).
    # Instead we expose position which is relative to the start position.
    # - is Left, + is Right.
    self.position = 0

  # Tape is grown lazily, so the leftmost/rightmost positions are at the
  # extreme ends of the deque.
  def pos_leftmost(self) -> int:
    """Furthest left position visited on the tape."""
    return self._index2pos(0)
  def pos_rightmost(self) -> int:
    """Furthest right position visited on the tape."""
    return self._index2pos(len(self.tape) - 1)

  def read_or_blank(self, pos : int | None = None) -> SymbolOrBlank:
    if pos is None:
      pos = self.position
    index = self._pos2index(pos)
    if 0 <= index < len(self.tape):
      return self.tape[index]
    else:
      return self.init_symbol

  def read(self, pos : int | None = None) -> Symbol:
    return self.read_or_blank(pos).value

  def write(self, symbol : Symbol, pos : int | None = None) -> None:
    if pos is None:
      pos = self.position
    self._expand_tape(pos)
    self.tape[self._pos2index(pos)] = SymbolOrBlank(symbol, False)

  def move(self, dir) -> None:
    if dir:  # Right
      self.position += 1
      self.index += 1
    else:  # Left
      self.position -= 1
      self.index -= 1
    self._expand_tape()

  def copy(self):
    new_tape = DirectTape(self.init_symbol)
    new_tape.tape = self.tape.copy()
    new_tape.index = self.index
    new_tape.position = self.position
    return new_tape

  def _pos2index(self, pos : int) -> int:
    return pos - self.position + self.index
  def _index2pos(self, index : int) -> int:
    return index - self.index + self.position
  def _index_default(self, pos : int | None = None) -> int:
    if pos == None:
      return self.index
    else:
      return self._pos2index(pos)

  def _expand_tape(self, new_pos : int | None = None) -> None:
    """Expand the deque to include the given position (defaults to current pos)."""
    new_index = self._index_default(new_pos)
    if new_index < 0:
      self.tape.extendleft([self.init_symbol] * -new_index)
      # Position does not change, but we must update index since extendleft changes the indexing.
      self.index += -new_index
    elif new_index >= len(self.tape):
      self.tape.extend([self.init_symbol] * (new_index - len(self.tape) + 1))
    # Note: We must recompute index since the deque may have been extended to the left.
    assert 0 <= self._index_default(new_pos) < len(self.tape)

  def count_nonzero(self) -> int:
    return sum(1 for symb in self.tape if symb.value != self.init_symbol.value)


class DirectSimulator:
  def __init__(self, tm : TM, *, initialize : bool = True):
    self.tm = tm

    if initialize:
      self.halted = False
      self.state : State = tm.init_state

      init_symbol = tm.init_symbol
      self.tape = DirectTape(init_symbol = init_symbol)

      self.step_num = 0

  def cur_symbol(self) -> Symbol:
    return self.tape.read()

  def copy(self) -> DirectSimulator:
    new_sim = DirectSimulator(self.tm, initialize=False)
    new_sim.state = self.state
    new_sim.halted = self.halted
    new_sim.tape = self.tape.copy()
    new_sim.step_num = self.step_num
    return new_sim

  def step(self) -> None:
    if not self.halted:
      state_in = self.state
      symbol_in = self.tape.read()
      trans = self.tm.get_trans_object(symbol_in, state_in)

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

  def seek(self, target_step_num : int) -> None:
    while not self.halted and self.step_num < target_step_num:
      self.step()


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm", help="Turing Machine or file or file:record_num (0-indexed).")
  parser.add_argument("num_steps", type=int)
  args = parser.parse_args()

  tm = IO.get_tm(args.tm)
  print(tm.ttable_str())
  sim = DirectSimulator(tm)

  start_time = time.time()
  sim.seek(args.num_steps)
  print(f"Simulated {sim.step_num:_} steps in {time.time() - start_time:_.1f}s")
  if sim.halted:
    print(f"Halted with score {sim.halt_score:_} at step {sim.step_num:_}")

if __name__ == "__main__":
  main()
