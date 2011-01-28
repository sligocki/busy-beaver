#! /usr/bin/env python
#
# Filters out machines whose halt states obviously cannot be reached based
# on backtracking.

from __future__ import division
import copy

from Common import Exit_Condition, HALT_STATE
import IO_old as IO

# Constants
BACKTRACK = "Backtrack"

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
        to_state[cell[2]].append(((state, symbol), cell))
        to_symbol[cell[0]].append(((state, symbol), cell))
  return halts, to_state, to_symbol

class Partial_Config:
  def __init__(self, state, symbol):
    self.dir = ([], [])
    self.current = symbol
    self.state = state
  def __repr__(self):
    return "%s %s %s %s" % (`self.dir[0]`, `self.state`, `self.current`, `self.dir[1]`)
  def applies(self, (state_in, symbol_in), (symbol_out, dir_out, state_out)):
    """Tests whether this transition could have been applied to get to this configuration."""
    return len(self.dir[not dir_out]) == 0 or \
           self.dir[not dir_out][0] == symbol_out
  def apply_trans(self, (state_in, symbol_in), (symbol_out, dir_out, state_out)):
    """Return a new configuration with transition applied backwards."""
    new_config = copy.deepcopy(self)
    new_config.dir[dir_out].insert(0, new_config.current)
    if len(new_config.dir[not dir_out]) != 0:
      del new_config.dir[not dir_out][0]
    new_config.current = symbol_in
    new_config.state = state_in
    return new_config

def backtracker((halt_state, halt_symbol), to_state, to_symbol, steps, limit):
  pos_configs = [Partial_Config(halt_state, halt_symbol)]
  for i in range(steps):
    #print " ", len(pos_configs)
    prev_configs = []
    for config in pos_configs:
      for addr, cell in to_state[config.state]:
        if config.applies(addr, cell):
          prev_configs.append(config.apply_trans(addr, cell))
    pos_configs = prev_configs
    if len(pos_configs) == 0:
      #print "End", len(pos_configs)
      return i+1
    elif len(pos_configs) > limit:
      break
  #print "End", len(pos_configs)
  return False

def test(TTable, steps, limit):
  # Get initial stat info
  halts, to_state, to_symbol = get_stats(TTable)
  max_steps = -1
  # See if all halts cannot be reached
  for halt_state, halt_symbol in halts:
    # Initial Criterion: no halt_state transition goes to the halt_state
    # For efficiency esp. in multi-symbol situations
    for cell in TTable[halt_state]:
      if cell[2] == halt_state:
        return False
    this_steps = backtracker((halt_state, halt_symbol), to_state, to_symbol, steps, limit)
    # If any of the backtracks fail, the whole thing fails.
    if not this_steps:
      return False
    max_steps = max(max_steps, this_steps)
  # If all halt states cannot be reached:
  return Exit_Condition.INFINITE, BACKTRACK, max_steps, "Backtrack"
      
def apply_results(results, old_line, log_number):
  old_results = next[5]
  return next[0:5]+(results, next[6], log_number, old_results)

if __name__ == "__main__":
  import sys
  from Option_Parser import Filter_Option_Parser
  # Get command line options.
  opts, args = Filter_Option_Parser(sys.argv, [("backsteps" , int, None, True, True),
                                               ("limit",     int, None, False, True)])

  limit = opts["limit"]
  if limit is None:
    limit = opts["backsteps"]
  log_number = opts["log_number"]
  io = IO.IO(opts["infile"], opts["outfile"], log_number)
  next = io.read_result()
  while next:
    TTable = next[6]
    # Run the simulator/filter on this machine
    results = test(TTable, opts["backsteps"], limit)
    # Deal with result
    if results:
      next = apply_results(results, next, log_number)
    io.write_result_raw(*next)
    next = io.read_result()
