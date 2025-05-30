#! /usr/bin/env python3

import argparse
from dataclasses import dataclass

from Direct_Simulator import DirectSimulator, TM, State, SymbolOrBlank
import IO


@dataclass
class Trans:
  """Single TM transition index (state and symbol read)."""
  state : State
  symbol : SymbolOrBlank

  def __str__(self) -> str:
    return f"{self.state}{self.symbol}"

class Transcript:
  """Transcript or transition history of all transitions TM used when started on a blank tape."""
  def __init__(self, tm : TM) -> None:
    self.tm = tm
    self.sim = DirectSimulator(tm)
    self.history : list[Trans] = []

  def __str__(self) -> str:
    s = " ".join(str(t) for t in self.history)
    if not self.sim.halted:
      s += " ..."
    return s
  
  def __len__(self) -> int:
    return len(self.history)
  
  def extend_history(self, size : int) -> None:
    target = self.sim.step_num + size
    while self.sim.step_num < target and not self.sim.halted:
      self.history.append(Trans(self.sim.state, self.sim.tape.read_or_blank()))
      self.sim.step()


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm", help="Turing Machine or file or file:record_num (0-indexed).")
  parser.add_argument("num_steps", type=int, nargs="?", default=20)
  args = parser.parse_args()

  tm = IO.get_tm(args.tm)
  transcript = Transcript(tm)
  transcript.extend_history(args.num_steps)
  print(transcript)

if __name__ == "__main__":
  main()