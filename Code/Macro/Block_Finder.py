#
# Block_Finder.py
#
"""
Search for a good block size for the TM simulator.
"""
from __future__ import division

import copy
import optparse
from optparse import OptionParser, OptionGroup
import sys
import time

from Simulator import Simulator
import Turing_Machine

def add_option_group(parser):
  """Add Block_Finder options group to an OptParser parser object."""
  assert isinstance(parser, OptionParser)

  group = OptionGroup(parser, "Block Finder options")

  group.add_option("--verbose-block-finder", action="store_true")

  group.add_option("--bf-limit1", type=int, default=200, metavar="LIMIT",
                   help="Number of steps to run the first half of the "
                   "block finder (0 to not run at all) [Default: %default].")

  group.add_option("--bf-limit2", type=int, default=200, metavar="LIMIT",
                   help="Number of steps to run the second half of the "
                   "block finder (0 to not run at all) [Default: %default].")

  group.add_option("--bf-extra-mult", type=int, default=2, metavar="N",
                   help="How far ahead to search in second half of the "
                   " block finder.")

  parser.add_option_group(group)


def block_finder(machine, options):
  """Tries to find the optimal block-size for macro machines"""
  assert isinstance(options, optparse.Values)

  ## First find the minimum efficient tape compression size.
  new_options = copy.copy(options)
  new_options.prover = False  # Disable proof system for block finding.
  new_options.compute_steps = True  # Even if --no-steps, we need steps here.
  new_options.verbose_simulator = options.verbose_block_finder
  sim = Simulator(machine, new_options)

  if options.verbose_block_finder:
    print
    print "Block finder start time:", time.clock()
  ## Find the least compressed time in before limit
  if options.bf_limit1 > 0:
    # Run sim to find when the tape is least compressed with macro size 1
    max_length = len(sim.tape.tape[0]) + len(sim.tape.tape[1])
    worst_loop = 0
    for i in range(options.bf_limit1):
      sim.step()
      tape_length = len(sim.tape.tape[0]) + len(sim.tape.tape[1])
      if tape_length > max_length:
        max_length = tape_length
        worst_loop = sim.num_loops
      # If it has stopped running then this is a good block size!
      if sim.op_state != Turing_Machine.RUNNING:
        if options.verbose_block_finder:
          print "Halted, returning base block size: 1"
          print ""
        return 1

    if options.verbose_block_finder:
      print "Found least compression time:", time.clock()
      print "Least compression at step:", worst_loop
      print ""

    # TODO: Instead of re-seeking, keep going till next bigger tape?
    sim = Simulator(machine, new_options)
    sim.loop_seek(worst_loop)

  ## Or just find the best compression at time limit
  else:
    sim.run(options.bf_limit1)

  if options.verbose_block_finder:
    print "Reset sim time:", time.clock()
    print ""

  # Analyze this time to see which block size provides greatest compression
  tape = uncompress_tape(sim.tape.tape)

  if options.verbose_block_finder:
    print "Uncompressed tape time:", time.clock()
    print ""
    print tape
    print ""

  min_compr = len(tape) + 1 # Worse than no compression
  opt_size = 1
  for block_size in range(1, len(tape)//2):
    compr_size = compression_efficiency(tape, block_size)
    if compr_size < min_compr:
      min_compr = compr_size
      opt_size = block_size

  if options.verbose_block_finder:
    print "Run1 end time:", time.clock()
    print "Optimal base block size:", opt_size
    print ""
    print tape
    print ""

  if options.bf_limit2 <= 0:
    return opt_size

  ## Then try a couple different multiples of this base size to find best speed
  max_chain_factor = 0
  opt_mult = 1
  mult = 1
  while mult <= opt_mult + options.bf_extra_mult:
    block_machine = Turing_Machine.Block_Macro_Machine(machine, mult*opt_size)
    back_machine = Turing_Machine.Backsymbol_Macro_Machine(block_machine)
    sim = Simulator(back_machine, new_options)
    sim.loop_seek(options.bf_limit2)
    if sim.op_state != Turing_Machine.RUNNING:
      return mult*opt_size
    chain_factor = sim.steps_from_chain / sim.steps_from_macro

    if options.verbose_block_finder:
      print mult, chain_factor

    # Note that we prefer smaller multiples
    # We only choose larger multiples if they perform much better
    if chain_factor > 2*max_chain_factor:
      max_chain_factor = chain_factor
      opt_mult = mult
    mult += 1

  if options.verbose_block_finder:
    print ""
    print "Run2 end time:", time.clock()
    print "Optimal block mult:", opt_mult
    print ""
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

