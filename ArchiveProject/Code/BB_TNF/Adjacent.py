#! /usr/bin/env python
#
# Adjacent.py
#
"""
Enumerate all adjacent machines to an input one.
"""

import copy

def adjacent(ttable):
  num_states = len(ttable)
  num_symbols = len(ttable[0])
  machines = []
  for state_in in range(num_states):
    for symbol_in in range(num_symbols):
      for state_out in range(num_states):
        for symbol_out in range(num_symbols):
          for dir_out in range(2):
            if ttable[state_in][symbol_in] != (symbol_out, dir_out, state_out):
              new_ttable = copy.deepcopy(ttable)
              new_ttable[state_in][symbol_in] = (symbol_out, dir_out, state_out)
              machines.append(new_ttable)
  return machines

if __name__ == "__main__":
  import sys, IO

  if len(sys.argv) >= 3:
    line = int(sys.argv[2])
  else:
    line = 1

  ttable = IO.load_TTable_filename(sys.argv[1], line)

  for out_ttable in adjacent(ttable):
    print out_ttable

