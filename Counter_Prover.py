#! /usr/bin/env python

import sys, IO
from Macro import Turing_Machine, Chain_Simulator, Chain_Proof_System, Block_Finder

# Globals
UP = 1
DOWN = 0

DEBUG = True
def debug(s):
  if DEBUG:
    print s

class Proved_Counter(Exception): pass

class CP(Chain_Proof_System.Proof_System):
  def log(self, tape, state, step_num):
    # Looking for ...0Ab^n C> 0...
    if len(tape.tape[UP]) == 1 and tape.dir == UP:
      if DEBUG:
        print state, tape
      return Chain_Proof_System.Proof_System.log(self, tape, state, step_num)
    else:
      return False, None, None
  def compare(self, old_config, new_config):
    # Unpack configurations
    old_state, old_tape, old_step_num = old_config
    new_state, new_tape, new_step_num = new_config
    if DEBUG:
      print "Looks good!"
      print " ", old_state, old_tape
      print " ", new_state, new_tape
    # Looking for ...0Ab^n C> 0... -> ...0Ab^(n+1) C> 0...
    if new_tape.tape[DOWN][0].num != old_tape.tape[DOWN][0].num + 1 or \
       new_tape.tape[DOWN][1:] != old_tape.tape[DOWN][1:]:
      debug("  Failed Rule 0")
      return False

    S = old_state # Set signal
    t = new_tape.tape[DOWN][0].symbol # Temp/carry symbol
    h = new_tape.tape[DOWN][1].symbol # Home symbol (TODO: expand home symbol)
    b = self.machine.init_symbol # Blank symbol

    ## Rule 1) S> b -> <R 1
    cond, trans, num_steps = self.machine.get_transition(b, S, UP)
    symbol_out, state_out, dir_out = trans
    if dir_out != DOWN:
      debug("  Failed Rule 1")
      return False
    R = state_out # Reset signal
    s1 = symbol_out # 1 symbol

    ## Rule 2) t <R -> <R 0
    cond, trans, num_steps = self.machine.get_transition(t, R, DOWN)
    symbol_out, state_out, dir_out = trans
    if dir_out != DOWN or state_out != R:
      debug("  Failed Rule 2")
      return False
    s0 = symbol_out # 0 symbol

    ## Rule 3) h <R -> h S>
    cond, trans, num_steps = self.machine.get_transition(h, R, DOWN)
    symbol_out, state_out, dir_out = trans
    if trans != (h, S, UP):
      debug("  Failed Rule 3")
      return False

    ## Rule 4) S> 0 -> <R 1
    cond, trans, num_steps = self.machine.get_transition(s0, S, UP)
    symbol_out, state_out, dir_out = trans
    if trans != (s1, R, DOWN):
      debug("  Failed Rule 4")
      return False

    ## Rule 5) S> 1 -> t S>
    cond, trans, num_steps = self.machine.get_transition(s1, S, UP)
    symbol_out, state_out, dir_out = trans
    if trans != (t, S, UP):
      debug("  Failed Rule 5")
      return False

    # If all 5 rules are satisfied it will run forever.
    raise Proved_Counter

def counter_prover(machine, steps=100):
  sim = Chain_Simulator.Simulator()
  sim.init(machine)
  sim.proof = CP(machine)
  try:
    sim.loop_run(steps)
  except Proved_Counter:
    return True

# Main script
if len(sys.argv) >= 3:
  line = int(sys.argv[2])
else:
  line = 1

ttable = IO.load_TTable_filename(sys.argv[1], line)

# Setting up params
UP = 0; DOWN = 1
offset = 1

# Construct Machine (Backsymbol-k-Block-Macro-Machine)
m1 = Turing_Machine.Simple_Machine(ttable)
# Use inteligent software to find optimal block size
Block_Finder.DEBUG = DEBUG
block_size = Block_Finder.block_finder(m1, 100)
# Do not create a 1-Block Macro-Machine (just use base machine)
if block_size == 1:
  m2 = m1
else:
  m2 = Turing_Machine.Block_Macro_Machine(m1, block_size, offset)
m3 = Turing_Machine.Backsymbol_Macro_Machine(m2)

if counter_prover(m3):
  print "Proven counter!"
else:
  print "Inconclusive :("
