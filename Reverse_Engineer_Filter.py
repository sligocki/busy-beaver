#! /usr/bin/env python
#
# Filters out machines whose halt states obviously cannot be reached based
# on reverse engineering/backtracking.

from __future__ import division
import IO

# Constants
INFINITE = 4
REVERSE_ENG = 3
HALT_STATE = -1

def init_array(val, num):
  temp = [None] * num
  for i in range(num):
    temp[i] = val[:]
  return temp

def get_stats(TTable):
  """Finds all halt transitions and other statistical info"""
  num_states = len(TTable)
  num_symbols = len(TTable[0])
  halts = []
  to_state = init_array([], num_states)
  to_symbol = init_array([], num_symbols)
  for state in range(num_states):
    for symbol in range(num_symbols):
      cell = TTable[state][symbol]
      if cell[2] == HALT_STATE:
        halts.append((state, symbol))
      else:
        to_state[cell[2]].append(cell)
        to_symbol[cell[0]].append(cell)
  return halts, to_state, to_symbol

def cannot_reach_halt((halt_state, halt_symbol), to_state, to_symbol):
  # If no transitions go to halt_state -> never halt (Unless A0 -> Halt)
  if len(to_state[halt_state]) == 0 and halt_state, halt_symbol != 0, 0:
    return True
  # Our method only works when we know that the symbol it will halt from must
  #   be written by the TM (not there initially).
  if halt_symbol == 0:
    return False
  # If no transitions write the halt_symbol -> never halt
  if len(to_symbol[halt_symbol]) == 0:
    return True
  # Test whether all transitions to halt_state are in the same direction as
  #   all the transitions writing halt_symbol.
  prehalt_dir = to_state[halt_state][0][1]
  for cell in to_state[halt_state]:
    if cell[1] != prehalt_dir:
      return False
  for cell in to_symbol[halt_symbol]:
    if cell[1] != prehalt_dir:
      return False
  # If all trans in the same direction, then we cannot reach this halt.
  return True

def test(TTable):
  # Get initial stat info
  halts, to_state, to_symbol = get_stats(TTable)
  # See if all halts cannot be reached
  for halt in halts:
    if not cannot_reach_halt(halt, to_state, to_symbol):
      return False
  # If all halt states cannot be reached:
  return INFINITE, REVERSE_ENG, "Reverse_Engineer"
      
def apply_results(results, old_line, log_number):
  old_results = next[5]
  return next[0:5]+(results, next[6], log_number, old_results)

if __name__ == "__main__":
  import sys
  from Option_Parser import Filter_Option_Parser
  # Get command line options.
  opts, args = Filter_Option_Parser(sys.argv, [])

  log_number = opts["log_number"]
  io = IO.IO(opts["infile"], opts["outfile"], log_number)
  next = io.read_result()
  while next:
    TTable = next[6]
    # Run the simulator/filter on this machine
    results = test(TTable)
    # Deal with result
    if results:
      next = apply_results(results, next, log_number)
    io.write_result_raw(*next)
    next = io.read_result()
