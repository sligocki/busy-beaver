#! /usr/bin/env python

import os
import math
import sys
import time

import IO

# Abstraction of infinity.
Inf = "Inf"

# Efficiency check parameters.
num_macro = 0
num_steps = 0

# Module specific Error to be raised when something unexpected happens
class Error(Exception): pass
# Exception classes used to signal the halting or detected infinite run of TMs.
class TM_Finish(Exception): pass
class TM_Infinity(TM_Finish): pass
class TM_Halt(TM_Finish): pass

def reverse(in_list):
  reversed_in_list = list(in_list)
  reversed_in_list.reverse()
  return reversed_in_list

class Simulator:
  """The accelerated TM simulator."""
  def __init__(self, TTable):
    self.TTable = TTable
    self.num_states = len(TTable)
    self.num_symbols = len(TTable[0])
    # Initialize blank Simulator.
    self.config = Config()
    self.step_num = 0
    # Setup macro hash.
    self.macro = {}
    for state_in in range(self.num_states):
      for symbol_in in range(self.num_symbols):
        symbol_out, dir_out, state_out = self.TTable[state_in][symbol_in]
        # If it halts move on.
        if state_out == -1:
          continue
        # See if it has a 1 step repeating pattern.
        if state_out == state_in:
          self.macro[(state_in, (symbol_in,), dir_out)] = ([symbol_out], 1, 1)
        # See if it has a 2 step repeating pattern.
        state_in2 = state_out
        for symbol_in2 in range(self.num_symbols):
          symbol_out2, dir_out2, state_out2 = self.TTable[state_in2][symbol_in2]
          if dir_out2 == dir_out and state_out2 == state_in:
            if symbol_in != symbol_in2:
              seq_in = [symbol_in, symbol_in2]; seq_in_reps = 1
            else:
              seq_in = [symbol_in]; seq_in_reps = 2
            if symbol_out != symbol_out2:
              seq_out = [symbol_out, symbol_out2]; seq_out_reps = 1
            else:
              seq_out = [symbol_out]; seq_out_reps = 2
            self.macro[(state_in, tuple(seq_in), dir_out)] = (seq_out, seq_in_reps, seq_out_reps)
  def run(self, step_cutoff):
    """Run simulator until it reaches/surpasses a specific step_num."""
    while self.step_num < step_cutoff:
      item, dir, state = self.config.get_pos()
      seq = item.seq
      if self.macro.has_key((state, tuple(seq), dir)):
        new_seq, reps_per_cycle_old, reps_per_cycle_new = self.macro[(state, tuple(seq), dir)]
        if item.rep == Inf:
          raise TM_Infinity
        cycles2do = item.rep // reps_per_cycle_old
        if cycles2do > 0:
          old_reps2do = reps_per_cycle_old * cycles2do
          new_reps2do = reps_per_cycle_new * cycles2do
          # We reverse the sequense because we are writing it behind ourselves.
          new_seq = reverse(new_seq)
          new_item = Tape_Item(new_seq, new_reps2do)
          item.rep -= old_reps2do
          if item.rep == 0:
            item = None
          self.step_num += len(seq)*old_reps2do
          self.config.macro_step(new_item, item)
          continue
      symbol = seq[0]
      self.step_num += 1
      self.config.step(*self.TTable[state][symbol])
  def macro_setup(self):
    """Sets up entire macro table, complicated so I'm putting it off."""
    def rec_macro(state_in, dir_in, init_state, cuttoff):
      if cuttoff < 0:
        return False
      for symbol_in in range(self.num_symbols):
        symbol_out, dir_out, state_out = self.TTable[state_in][symbol_in]
        if dir_out != dir_in:
          continue
        if state_out == init_state:
          return [symbol_out]
        else:
          seq = rec_macro(state_out, dir_out, init_state, cuttoff - 1)
          if seq:
            return [symbol_in]+seq[0], [symbol_out]+seq[1]
          else:
            return False
    self.macro = {}
    for state_in in range(self.num_states):
      for symbol_in in range(self.num_symbols):
        symbol_out, dir_out, state_out = self.TTable[state_in][symbol_in]
        if state_out == state_in:
          self.macro[(state_in, [symbol_in], dir_out)] = ([symbol_out], 1, 1)
          continue
        seq = rec_macro(state_out, dir_out, state_in, self.num_states)
        if seq:
          seq_in = [symbol_in]+seq[0]
          seq_out = [symbol_out]+seq[1]
          self.macro[(state_in, seq_in, dir_out)] = (seq_out, )

class Config:
  """Specific representation for a Turing Machine's Tape."""
  def __init__(self):
    self.tape = [Stack(), Stack()] # Represents the actual tape as 2 stacks, one on each side of the head.
    # Initialize tape and other configuration information.
    self.tape[0].push(Tape_Item([0], Inf))
    self.tape[1].push(Tape_Item([0], Inf))
    self.dir = 1   # Direction the head is moving (0 = Left, 1 = Right)
    self.state = 0 # Start is state 0.
  def __repr__(self):
    if self.dir:  dir = "->"
    else:         dir = "<-"
    return "%s %d %s %s" % (self.tape[0].repr(0), self.state, dir, self.tape[1].repr(1))
  def get_pos(self):
    """Returns information needed to perform next move/macro-move."""
    item = self.tape[self.dir][0] # The top Tape_Item/sequence approaching.
    return item, self.dir, self.state
  def macro_step(self, seq_write, seq_leave = None):
    """Make a macro-step over a whole sequence of symbols."""
    global num_macro; num_macro += 1
    self.tape[self.dir].pop()
    if seq_leave:
      self.tape[self.dir].push(seq_leave)
    # Now write the seq_write sequences behind you.
    stack = self.tape[not self.dir]
    if seq_write.seq == stack[0].seq:
      if stack[0].rep != Inf:
        stack[0].rep += seq_write.rep
    else:
      if len(stack) >= len(seq_write.seq) == 2 and \
         stack[0].seq == seq_write.seq[0:1] and stack[0].rep == 1 and \
         stack[1].seq == seq_write.seq[1:2] and stack[1].rep == 1:
        stack.pop(); stack.pop()
        seq_write.rep += 1
      if seq_write.rep == 1:
        reverse_seq_write = reverse(seq_write.seq)
        for symbol in reverse_seq_write:
          self._push(not self.dir, symbol)
      else:
        stack.push(seq_write)
        
  def step(self, symbol_out, dir_out, state_out):
    """Make a single TM transition.
    Write symbol, move in dir, change to state."""
    global num_steps; num_steps += 1
    # Pop old symbol off of appropriate stack (self.dir == dir_in).
    self._pop(self.dir)
    # Push new symbol onto appropriate stack (not dir_out).
    self._push(not dir_out, symbol_out)
    # Move in direction.
    self.dir = dir_out
    # Change state.
    self.state = state_out
    if self.state == -1:
      raise TM_Halt
  def _pop(self, dir):
    stack = self.tape[dir]
    item = stack[0]
    if len(item.seq) == 1:
      # [a^1, ...] -> a + [...]
      if item.rep == 1:
        stack.pop()
      # [a^n, ...] -> a + [a^(n-1), ...]
      else:
        # Note: [a^Inf] -> a + [a^Inf]
        if item.rep != Inf:
          item.rep -= 1
    else:
      # [(abc...)^1, ...] -> a + [(bc...)^1, ...]
      if item.rep == 1:
        # This situation should not exist in current implimentation (27 June 2006).
        raise Error, "Config._pop: Should not have (abc...)^1"
        item.seq.pop(0)
      # [(abc...)^n, ...] -> a + (b + c + ... + [(abc...)^(n-1), ...])
      else:
        if item.rep != Inf:
          item.rep -= 1
        # [(abc...)^1, ...] should be (a + b + c + ... + [...])
        if item.rep == 1:
          stack.pop()
          seq = reverse(item.seq)
          for symbol in seq:
            self._push(dir, symbol)
        new_seq = reverse(item.seq)
        new_seq.pop(-1)
        for symbol in new_seq:
          self._push(dir, symbol)
  def _push(self, dir, symbol):
    stack = self.tape[dir]
    item = stack[0]
    # a + [a^n, ...] -> [a^(n+1), ...]
    if item.seq == [symbol]:
      # Note: a + [a^Inf] -> [a^Inf]
      if item.rep != Inf:
        item.rep += 1
    # a + [b^1, a^1, b^1, ...] -> [(ab)^2, ...]
    elif len(stack) >= 3 and \
         stack[1].seq == [symbol] and stack[1].rep == 1 and \
         stack[2].seq == stack[0].seq and stack[2].rep == stack[0].rep == 1:
      new_item = Tape_Item([symbol]+stack[0].seq, 2)
      stack.pop(); stack.pop(); stack.pop()
      stack.push(new_item)
    # a + [b^1, (ab)^n, ...] -> [(ab)^(n+1), ...]
    elif len(stack) >= 2 and \
         [symbol]+stack[0].seq == stack[1].seq and stack[0].rep == 1:
      if item.rep != Inf:
        stack[1].rep += 1
      stack.pop()
    # a + [...] -> [a^1, ...]
    else:
      new_item = Tape_Item([symbol], 1)
      stack.push(new_item)
  def get_nonzeros(self):
    n = 0 # Number of non-zeros
    for i in range(2):
      for item in self.tape[i]:
        if item.rep != Inf:
          n += (len(item.seq) - item.seq.count(0)) * item.rep
    return n

class Tape_Item:
  """Container class which holds tape information.
  Holds a sequence of symbols and a repetition count (e.g. (01)^5 )"""
  def __init__(self, seq, rep):
    self.seq = seq
    self.rep = rep
  def repr(self, dir):
    if len(self.seq) == 1:  seq = self.seq[0]
    elif dir:               seq = self.seq
    else:                   seq = reverse(self.seq)
    return "%s^%s" % (`seq`, str(self.rep))

class Stack:
  """Generic Stack Class."""
  def __init__(self, *args):
    """Uses args as the initial items on stack.  Last arg is on top."""
    self.contents = list(args)
  def push(self, item):
    self.contents.append(item)
  def pop(self):
    return self.contents.pop(-1)
  def __getitem__(self, index):
    return self.contents[-1 - index]
  def __len__(self):
    return len(self.contents)
  def repr(self, dir):
    if dir: l = reverse(self.contents)
    else:   l = self.contents
    return "["+reduce((lambda x, y: x+", "+y.repr(dir)), l[1:], l[0].repr(dir))+"]"

if __name__ == "__main__":
  infile = file(sys.argv[1], "r")
  if len(sys.argv) > 2: line = int(sys.argv[2])
  else:                 line = 1
  TTable = IO.load_TTable(infile, line)
  infile.close()
  sim = Simulator(TTable)
  # Print transition table and list of macro rules.
  for line in TTable:
    print line
  print
  for key in sim.macro.keys():
    print key, ":", sim.macro[key]
  print
  sys.stdout.flush()

  running = True; extent = 1
  try:
    while True:
      sim.run(extent)
      # Print Tape and data.
      print "10^%d" % round(math.log(sim.step_num, 10)),
      print sim.step_num, num_macro, num_steps, time.clock(), os.times()
      print sim.config, sim.config.get_nonzeros()
      print
      sys.stdout.flush()
      #extent += 1
      extent *= 10
  except (TM_Finish, Error, KeyboardInterrupt), e:
    print sys.exc_type, e
    print "10^%d" % round(math.log(sim.step_num, 10)),
    print sim.step_num, num_macro, num_steps, time.clock(), os.times()
    print sim.config, sim.config.get_nonzeros()
    sys.stdout.flush()
