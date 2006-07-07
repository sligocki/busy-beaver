#! /usr/bin/env python
#
# Turing Machine Simulator based on Heiner Marxen's Macro Machine design.
#

import math, time

HALT_STATE = -1
INF = "Inf"

def reverse(in_list):
  reversed_in_list = list(in_list)
  reversed_in_list.reverse()
  return reversed_in_list

class Macro_TTable:
  """Creates an on-the-fly or lazy-evaluation transition table for a macro machine.
  Can be indexed as if the entire table already existed in memory."""
  def __init__(self, TTable):
    # Normal Machine's transition table
    # TTable: Q x S -> S x D x Q
    # Note: Q = set of states, S = set of symbols, D = set of directions
    self.TTable = TTable
    self.num_states = len(TTable)
    self.num_symbols = len(TTable[0])
    # Macro Machine's transition table (lazy evaluated)
    # macro_TTable: Q x S^m x D -> Q x S^m x D x Z
    # Where m is the size of the macro_symbols and the output Z is the number
    #   of micro steps taken.
    self.macro_TTable = {}
    # Statistical variables
    self.num_misses = 0
  def __getitem__(self, item):
    """Accesses the macro transition table. item = state, symbol, dir."""
    # If we don't already have this input in the table, evaluate it.
    if not self.macro_TTable.has_key(item):
      self.macro_TTable[item] = self._run(*item)
      self.num_misses += 1
    return self.macro_TTable[item]
  def _run(self, macro_state_in, macro_symbol_in, macro_dir_in):
    """Evaluates macro_TTable[state, symbol, dir]"""
    # Set up machine
    num_steps = 0
    state_in = macro_state_in
    tape = list(macro_symbol_in)
    size = len(tape)
    if macro_dir_in:
      pos = 0
    else:
      pos = size - 1
    max_steps = size * self.num_states * self.num_symbols**size
    # Run machine
    while 0 <= pos < size:
      symbol_in = tape[pos]
      symbol_out, dir_out, state_out = self.TTable[state_in][symbol_in]
      state_in = state_out
      tape[pos] = symbol_out
      if dir_out:
        pos += 1
      else:
        pos -= 1
      num_steps += 1
      # If we halt, immediately return.  We use dir_out as position.
      if state_in == HALT_STATE:
        return state_in, tuple(tape), pos, num_steps
      # If we've exceeded the maximum possible number of steps, we'll never halt.
      if num_steps > max_steps:
        return INF, None, None, INF
    # Return critical info about machine if it's still running.
    macro_state_out = state_in
    macro_symbol_out = tuple(tape)
    if pos < 0:
      macro_dir_out = 0
    else:
      macro_dir_out = 1
    return macro_state_out, macro_symbol_out, dir_out, num_steps

class Stack(list):
  """Generic Stack class based on built-in list."""
  def pop(self):
    return list.pop(self, 0)
  def push(self, item):
    self.insert(0, item)

class Tape_Slice:
  """Slice of tape of length macro_step with allowed repatitions."""
  def __init__(self, symbol, number_of_repetitions):
    self.symbol = symbol
    self.num = number_of_repetitions
  def __repr__(self):
    if len(self.symbol) == 1:
      sym = self.symbol[0]
    else:
      sym = self.symbol
    return "%s^%s" % (str(sym), str(self.num))

class Macro_Tape:
  """Stores the turing machine tape in Marxen-style macro-compression."""
  def __init__(self, macro_size):
    self.macro_size = macro_size
    self.dir = 1
    self.tape = [Stack(), Stack()]
    self.tape[0].push(Tape_Slice((0,)*macro_size, INF))
    self.tape[1].push(Tape_Slice((0,)*macro_size, INF))
  def get_top_symbol(self):
    """Simply returns the current symbol and direction."""
    return self.tape[self.dir][0].symbol, self.dir
  def apply_single_move(self, macro_symbol, dir):
    """Apply a single macro step.  del old symbol, push new one."""
    self.del_one()
    self.push_one(macro_symbol, not dir)
    self.dir = dir
  def apply_chain_move(self, macro_symbol):
    """Apply a chain macro step which replaces an entire string of symbols.
    Returns the number of macro symbols replaced."""
    # Pop off old sequence
    num = self.tape[self.dir][0].num
    self.tape[self.dir].pop()
    # Push on new one behind us
    stack = self.tape[not self.dir]
    top = stack[0]
    if top.symbol == macro_symbol:
      if top.num != INF:
        top.num += num
    else:
      stack.push(Tape_Slice(macro_symbol, num))
    return num
  def del_one(self):
    """Delete of the current macro symbol."""
    stack = self.tape[self.dir]
    top = stack[0]
    # Don't decriment infinity
    if top.num != INF:
      top.num -= 1
      # If there are none left, remove from stack.
      if top.num == 0:
        stack.pop()
  def push_one(self, macro_symbol, dir):
    """Push a macro symbol in the direction specified."""
    stack = self.tape[dir]
    top = stack[0]
    # If it is identical to the top symbol, combine them.
    if top.symbol == macro_symbol:
      if top.num != INF:
        top.num += 1
    # Otherwise, just add it seperately.
    else:
      stack.push(Tape_Slice(macro_symbol, 1))

class Macro_Simulator:
  def __init__(self, TTable, macro_size):
    self.tape = Macro_Tape(macro_size)
    self.mtt = Macro_TTable(TTable)
    self.state = 0
    self.cur_step_num = 0
    # Statistical vars
    self.num_single_steps = 0
  def run(self, num_steps):
    self.seek(self.cur_step_num + num_steps)
  def seek(self, step_num):
    while self.cur_step_num < step_num and self.state not in (HALT_STATE, INF):
      self.step()
  def step(self):
    if self.state in (HALT_STATE, INF):
      return
    # Get info from tape
    symbol, dir = self.tape.get_top_symbol()
    # Lookup transition
    new_state, new_symbol, new_dir, this_num_steps \
      = self.mtt[self.state, symbol, dir]
    # Apply transition
    if new_state == HALT_STATE:
      self.state = HALT_STATE
      self.tape.apply_single_move(new_symbol, 1)
      self.cur_step_num += this_num_steps
    elif this_num_steps == INF:
      self.state = INF
      self.cur_step_num = INF
    # If direction and state are unchanged after transition, then the transition
    #   will be repeated across an entire chain of equivolent macro symbols.
    elif new_state == self.state and new_dir == dir:
      num_reps = self.tape.apply_chain_move(new_symbol)
      self.cur_step_num += this_num_steps * num_reps
    # Otherwise, it was a normal transition, just apply it.
    else:
      self.state = new_state
      self.tape.apply_single_move(new_symbol, new_dir)
      self.cur_step_num += this_num_steps
      self.num_single_steps += 1
  def print_self(self):
    print
    print "10^%.1f" % math.log10(self.cur_step_num), self.cur_step_num
    print "10^%.1f" % math.log10(self.num_single_steps), self.num_single_steps
    print self.mtt.num_misses, time.clock()
    print reverse(self.tape.tape[0]), self.state, self.tape.dir, self.tape.tape[1]

def run(macro_size, filename, line_num = 1):
  import IO
  TTable = IO.load_TTable_filename(filename, line_num)
  sim = Macro_Simulator(TTable, macro_size)
  extent = 1
  while sim.state != HALT_STATE and sim.cur_step_num != INF:
    sim.seek(extent)
    sim.print_self()
    extent *= 10

if __name__ == "__main__":
  import sys

  if len(sys.argv) > 3:
    num = int(sys.argv[3])
  else:
    num = 1
  run(int(sys.argv[1]), sys.argv[2], num)
