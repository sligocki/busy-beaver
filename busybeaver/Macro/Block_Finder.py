from __future__ import division

import copy
import sys
import time

import Chain_Simulator
import Turing_Machine

DEBUG = False

def block_finder(machine, limit1=200, limit2=200, run1=True, run2=True, extra_mult=2):
  """Tries to find the optimal block-size for macromachines"""
  ## First find the minimum efficient tape compression size
  sim = Chain_Simulator.Simulator()
  sim.init(machine)
  sim.proof = None # Don't allow proof steps. We just want to find the best block size.
  
  if DEBUG:
    print "Block finder start time:", time.clock()
  ## Find the least compressed time in before limit
  if run1:
    # Run sim to find when the tape is least compressed with macro size 1
    max_length = len(sim.tape.tape[0]) + len(sim.tape.tape[1])
    worst_time = 0
    for i in range(limit1):
      sim.step()
      tape_length = len(sim.tape.tape[0]) + len(sim.tape.tape[1])
      if tape_length > max_length:
        max_length = tape_length
        worst_time = sim.step_num
      # If it has stopped running then this is a good block size!
      if sim.op_state != Turing_Machine.RUNNING:
        if DEBUG:
          print "Halted, returning base block size: 1"
        return 1
    
    if DEBUG:
      print "Found least compression time:", time.clock()
      print "Least compression at step:", worst_time
    
    sim.init(machine)
    sim.proof = None
    sim.seek(worst_time)
      
  ## Or just find the best compression at time limit
  else:
    sim.run(limit1)
  
  if DEBUG:
    print "Reset sim time:", time.clock()
  
  # Analyze this time to see which block size provides greatest compression
  tape = uncompress_tape(sim.tape.tape)
  
  if DEBUG:
    print "Uncompressed tape time:", time.clock()
    print tape
  
  min_compr = len(tape) + 1 # Worse than no compression
  opt_size = 1
  for block_size in range(1, len(tape)//2):
    compr_size = compression_efficiency(tape, block_size)
    if compr_size < min_compr:
      min_compr = compr_size
      opt_size = block_size
  
  if DEBUG:
    print "Run1 end time:", time.clock()
    print "Optimal base block size:", opt_size
    print tape
  
  if not run2:
    return opt_size
  
  ## Then try a couple different multiples of this base size to find best speed
  max_chain_factor = 0
  opt_mult = 1
  mult = 1
  while mult <= opt_mult + extra_mult:
    block_machine = Turing_Machine.Block_Macro_Machine(machine, mult*opt_size)
    back_machine = Turing_Machine.Backsymbol_Macro_Machine(block_machine)
    sim.init(back_machine)
    sim.proof = None # No proof system
    sim.loop_seek(limit2)
    if sim.op_state != Turing_Machine.RUNNING:
      return mult*opt_size
    chain_factor = sim.steps_from_chain / sim.steps_from_macro
    
    if DEBUG:
      print mult, chain_factor
    
    # Note that we prefer smaller multiples
    # We only choose larger multiples if they perform much better
    if chain_factor > 2*max_chain_factor:
      max_chain_factor = chain_factor
      opt_mult = mult
    mult += 1
  
  if DEBUG:
    print "Run2 end time:", time.clock()
    print "Optimal block mult:", opt_mult
    sys.stdout.flush()
  
  return opt_mult*opt_size

def uncompress_tape(compr_tape):
  """Expand out repatition counts in tape."""
  tape_out = []
  left_tape = compr_tape[0][1:]
  right_tape = compr_tape[1][1:]
  right_tape.reverse()
  for seq in left_tape + right_tape:
    tape_out += [seq.symbol]*seq.num
  return tape_out

def compression_efficiency(tape, k):
  """Find size of tape when compressed with blocks of size k."""
  compr_size = len(tape)
  for i in range(0, len(tape) - 2*k, k):
    if tape[i:i + k] == tape[i + k:i + 2*k]:
      compr_size -= k
  return compr_size

