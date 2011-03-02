#! /usr/bin/env python
"""
Filters out machines whose halt states obviously cannot be reached based
on a simple end case fact:
  If machine:
    * only halts on symbol 2 and in state B,
    * only writes 2s when moving Left (thus all 2s are on it's Right) and
    * only transitions to state B when moving Left
  then it cannot ever halt.
"""

from __future__ import division

from Common import Exit_Condition, HALT_STATE
import IO

def get_stats(TTable):
  """Finds all halt transitions and other statistical info"""
  num_states = len(TTable)
  num_symbols = len(TTable[0])
  halts = []
  # List of transitions to this state.
  to_state =  [ [] for i in range(num_states) ]
  # List of transitions which write this symbol.
  to_symbol = [ [] for i in range(num_symbols) ]
  for state in range(num_states):
    for symbol in range(num_symbols):
      cell = TTable[state][symbol]
      if cell[2] == HALT_STATE:
        halts.append((state, symbol))
      else:
        to_state[cell[2]].append(((state, symbol), cell))
        to_symbol[cell[0]].append(((state, symbol), cell))
  return halts, to_state, to_symbol

def cannot_reach_halt((halt_state, halt_symbol), to_state, to_symbol):
  """True means it is imposible to reach the halt state.
     False is inconclusive."""
  # Internal function has access to arguments of this function.
  def same_direction():
    """Test whether all transitions to halt_state are in the same direction as
       all the transitions writing halt_symbol."""
    addr, cell = to_state[halt_state][0]
    prehalt_dir = cell[1]
    for addr, cell in to_state[halt_state]:
      if cell[1] != prehalt_dir:
        return False
    for addr, cell in to_symbol[halt_symbol]:
      if cell[1] != prehalt_dir:
        return False
    # If all trans in the same direction, then we cannot reach this halt.
    return True

  # If no transitions go to halt_state -> never halt (Unless A0 -> Halt)
  if len(to_state[halt_state]) == 0 and (halt_state, halt_symbol) != (0, 0):
    return True
  # Method 1 requires that we write the symbol that we halt on.
  if halt_symbol != 0:
    # If no transitions write the halt_symbol -> never halt (Assumes symbol != 0)
    if len(to_symbol[halt_symbol]) == 0:
      return True
    # If all transitions to halt_state and from halt_symbol are the same
    #   direction and we must write the symbol we halt on we cannot halt.
    if same_direction():
      return True
  # If none of the methods work, we cannot prove it will not halt.
  return False

def test(TTable):
  # Get initial stat info
  halts, to_state, to_symbol = get_stats(TTable)
  # See if all halts cannot be reached
  for halt in halts:
    if not cannot_reach_halt(halt, to_state, to_symbol):
      return False
  # If all halt states cannot be reached:
  return Exit_Condition.INFINITE, "Reverse_Engineer"


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
