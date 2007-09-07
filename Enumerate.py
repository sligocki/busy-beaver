#! /usr/bin/env python
#
# Enumerate.py
#
# This is a Busy Beaver Turing machine enumerator.  It enumerates a 
# representative set of all Busy Beavers for given # of states and symbols,
# runs the accelerated simulator, gathers statistics, and outputs the machines
# that take the longest to halt.
#

import copy
import cPickle as pickle

from Turing_Machine import Turing_Machine, Turing_Machine_Runtime_Error
from IO import IO
import Macro_Simulator

class Stack(list):
  def push(self, item):
    return self.append(item)

class Enumerator(object):
  """Holds enumeration state information for checkpointing."""
  def __init__(self, num_states, num_symbols, max_steps, max_time, io, 
                     save_freq=100000, checkpoint_filename="checkpoint"):
    self.num_states = num_states
    self.num_symbols = num_symbols
    self.max_steps = max_steps
    self.max_time = max_time
    self.io = io
    self.save_freq = save_freq
    self.checkpoint_filename = checkpoint_filename
    
    self.stack = Stack()
    self.tm_num = 0
    
    self.num_halt = self.num_infinite = self.num_unresolved = 0
    self.best_steps = self.best_score = 0
  
  def enum(self):
    """Enumerate all num_states*num_symbols TMs in Tree-Normal Form"""
    blank_tm = Turing_Machine(self.num_states, self.num_symbols)
    self.stack.push(blank_tm)
    self.continue_enum()

  def continue_enum(self):
    i = 0
    while len(self.stack) > 0:
      if (i % self.save_freq) == 0:
        self.save()
      # While we have machines to run, pop one off the stack ...
      cur_tm = self.stack.pop()
      # ... and run it
      cond, info = self.run(cur_tm)
      
      # If it hits an undefined transition ...
      if cond == Macro_Simulator.UNDEFINED:
        on_state, on_symbol, steps, score = info
        # ... push all the possible non-halting transitions onto the stack ...
        self.add_transitions(cur_tm, on_state, on_symbol)
        # ... and make this tm the halting one (mutates cur_tm)
        self.add_halt_trans(cur_tm, on_state, on_symbol, steps, score)
      # Otherwise record defined result
      elif cond == Macro_Simulator.HALT:
        steps, score = info
        self.add_halt(cur_tm, steps, score)
      elif cond == Macro_Simulator.INFINITE:
        reason, = info
        self.add_infinite(cur_tm, reason)
      elif cond == Macro_Simulator.OVERSTEPS:
        steps, = info
        self.add_unresolved(Macro_Simulator.OVERSTEPS, steps)
      elif cond == Macro_Simulator.TIMEOUT:
        time, steps = info
        self.add_unresolved(Macro_Simulator.TIMEOUT, steps, time)
      else:
        raise Exception, "Enumerator.enum() - unexpected condition (%r)" % cond
  
  def save(self):
    print self.num_halt, self.num_infinite, self.num_unresolved
    print self.best_steps, self.best_score
    #f = file(self.checkpoint_filename, "wb")
    #pickle.dump(self, f)
  
  def run(self, tm):
    return Macro_Simulator.run(tm.get_TTable(), self.max_steps, self.max_time)
  
  def add_transitions(self, old_tm, state_in, symbol_in):
    """Push Turing Machines with each possible transition at this state and symbol"""
    # 'max_state' and 'max_symbol' are the state and symbol numbers for the
    # smallest state/symbol not yet written (i.e. available to add to TTable).
    max_state  = old_tm.get_num_states_available()
    max_symbol = old_tm.get_num_symbols_available()
    # If this is the last undefined cell, then it must be a halt, so only try
    # other values for cell if this is not the last undefined cell.
    if old_tm.num_empty_cells > 1:
      # 'state_out' in [0, 1, ... max_state] == range(max_state + 1)
      for state_out in range(max_state + 1):
        for symbol_out in range(max_symbol + 1):
          for direction_out in range(2):
            new_tm = copy.deepcopy(old_tm)
            new_tm.add_cell(state_in , symbol_in ,
                            state_out, symbol_out, direction_out)
            self.stack.push(new_tm)
  def add_halt_trans(self, tm, on_state, on_symbol, steps, score):
    #   1) Add the halt state
    tm.add_cell(on_state, on_symbol, -1, 1, 1)
    #   2) This machine  *may* write one more symbol
    if on_symbol == 0:
      score += 1
    #   3) Save this machine
    self.add_halt(tm, steps, score)
  
  def add_halt(self, tm, steps, score):
    self.num_halt += 1
    if steps > self.best_steps or score > self.best_score:
      ## Magic nums: the '-1' is for tape size (not used) .. the '0' is for halting.
      self.io.write_result(self.tm_num, -1, -1, (0, score, steps), tm)
      self.best_steps = max(self.best_steps, steps)
      self.best_score = max(self.best_score, score)
    self.tm_num += 1
  def add_infinite(self, tm, reason):
    self.num_infinite += 1
    self.tm_num += 1
  def add_unresolved(self, tm, steps, time=None):
    self.num_unresolved += 1
    self.tm_num += 1


# Command line interpretter code
if __name__ == "__main__":
  import sys
  from Option_Parser import Generator_Option_Parser
  
  # Get command line options.
  # Enumerate.py may be sent an infile param but it should be ignored
  opts, args = Generator_Option_Parser(sys.argv, 
          [("time",      int,     15, False, True), 
           ("save_freq", int, 100000, False, True)], ignore_infile=True)
  steps = (opts["steps"] if opts["steps"] > 0 else Macro_Simulator.INF)
  io = IO(None, opts["outfile"], opts["log_number"])
  
  enumerator = Enumerator(opts["states"], opts["symbols"], steps, 
                          opts["time"], io, opts["save_freq"])
  enumerator.enum()

