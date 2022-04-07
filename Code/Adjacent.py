#! /usr/bin/env python3
"""
Enumerate all adjacent machines to an input one.
"""

import copy
import sys

import IO
from Macro import Turing_Machine


def adjacent(ttable):
  num_states = len(ttable)
  num_symbols = len(ttable[0])
  machines = []
  for state_in in range(num_states):
    for symbol_in in range(num_symbols):
      new_ttable = copy.deepcopy(ttable)
      for state_out in range(num_states):
        for symbol_out in range(num_symbols):
          for dir_out in range(2):
            if ttable[state_in][symbol_in] != (symbol_out, dir_out, state_out):
              new_ttable[state_in][symbol_in] = (symbol_out, dir_out, state_out)
              yield new_ttable

if __name__ == "__main__":
  if len(sys.argv) >= 3:
    line = int(sys.argv[2])
  else:
    line = 1

  ttable = IO.load_TTable_filename(sys.argv[1], line)

  for out_ttable in adjacent(ttable):
    tm = Turing_Machine.Simple_Machine(out_ttable)
    print(tm.ttable_str())
