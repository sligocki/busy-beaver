#! /usr/bin/env python
#
# Input_Machines_From_Tuples.py
#
"""
Input machine from a set of tuples, see: http://morethanazillion.blogspot.com/
"""

import sys

undefined_transition = (-1, 0, -1)

if __name__ == "__main__":
  tuples = eval(sys.stdin.read())
  
  num_states = max(state_num for state_num, symb_num, x, y, z in tuples) + 1
  num_symbols = max(symb_num for state_num, symb_num, x, y, z in tuples) + 1
  
  TTable = [None] * num_states
  for state in range(num_states):
    TTable[state] = [undefined_transition] * num_symbols
  
  for state_in, symbol_in, symbol_out, dir_out, state_out in tuples:
    state_in -= 1
    state_out -= 1
    TTable[state_in][symbol_in] = (symbol_out, dir_out, state_out)
  
  print TTable
