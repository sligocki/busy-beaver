#
# Block_Finder.py
#
"""
Search for a good block size for the TM simulator.
"""


import copy
import math
import optparse
from optparse import OptionParser, OptionGroup
import sys
import time

import IO
from Macro.Simulator import Simulator
from Macro import Turing_Machine

import io_pb2

def add_option_group(parser : OptionParser):
  """Add Block_Finder options group to an OptParser parser object."""
  assert isinstance(parser, OptionParser)

  group = OptionGroup(parser, "Block Finder options")

  group.add_option("--verbose-block-finder", action="store_true")

  group.add_option("--max-block-size", type=int, default=0,
                   help="Maximum block size to try when using Block Finder. "
                   "Note: This is ignored if --block-size is set explicitly. "
                   "[Default: %default]")

  group.add_option("--block-mult", type=int, default=0,
                   help="Set fixed multiple of the block sized decided by block"
                   "finder (often better than setting --block-size directly in"
                   "order to avoid sizes that completely fail to compress the"
                   "tape). "
                   "[Default: %default]")

  group.add_option("--max-block-mult", type=int, default=2, metavar="N",
                   help="How far ahead to search in second half of the "
                   "block finder. "
                   "[Default: %default]")

  parser.add_option_group(group)


def block_finder(machine : Turing_Machine.Turing_Machine,
                 options : optparse.Values,
                 params : io_pb2.BlockFinderParams,
                 result : io_pb2.BlockFinderResult) -> None:
  """Tries to find the optimal block-size for macro machines using heuristics."""
  if params.max_block_size:
    max_block_size = params.max_block_size
  else:
    max_block_size = math.inf
  with IO.Timer(result):
    ## First find the minimum efficient tape compression size.
    new_options = copy.copy(options)
    new_options.compute_steps = True  # Even if --no-steps, we need steps here.
    new_options.prover = False
    new_options.verbose_simulator = False

    if options.verbose_block_finder:
      print("BF: Searching for optimal block size")

    if params.compression_search_loops:
      sim = Simulator(machine, new_options)

      ## Find the least compressed time in before limit
      # Run sim to find when the tape is least compressed with macro size 1
      max_length = len(sim.tape.tape[0]) + len(sim.tape.tape[1])
      worst_loop = 0
      for i in range(params.compression_search_loops):
        sim.step()
        tape_length = len(sim.tape.tape[0]) + len(sim.tape.tape[1])
        if tape_length > max_length:
          max_length = tape_length
          worst_loop = sim.num_loops
        # If it has stopped running then this is a good block size!
        if sim.op_state != Turing_Machine.RUNNING:
          result.best_block_size = 1
          return

      result.least_compressed_loop = worst_loop
      result.least_compressed_tape_size_chain = max_length

      # TODO: Instead of re-seeking, keep going till next bigger tape?
      sim = Simulator(machine, new_options)
      sim.loop_seek(worst_loop)
      assert len(sim.tape.tape[0]) + len(sim.tape.tape[1]) == max_length

      # Analyze this time to see which block size provides greatest compression
      tape = uncompress_tape(sim.tape.tape)
      result.least_compressed_tape_size_raw = len(tape)

      if options.verbose_block_finder:
        tape_str = "".join(str(symb) for symb in tape)
        print("BF: Least compressed tape at step", sim.step_num, ":", tape_str)

      min_compr = len(tape) + 1 # Worse than no compression
      opt_size = 1
      for block_size in range(1, len(tape)//2):
        compr_size = compression_efficiency(tape, block_size)
        if compr_size < min_compr:
          if block_size <= max_block_size:
            min_compr = compr_size
            opt_size = block_size
          else:
            break

      result.best_compression_block_size = opt_size
      result.best_compression_tape_size = min_compr

      if options.verbose_block_finder:
        print("BF: Optimal tape compression block size", opt_size,
              "tape size", min_compr)

    else:  # if not params.compression_search_loops
      opt_size = 1

    if params.block_mult:
      result.best_block_size = params.block_mult * opt_size
      if options.verbose_block_finder:
        print("BF: Block Finder finished")
        print()
        print(result)
        sys.stdout.flush()
      return

    if params.mult_sim_loops <= 0:
      result.best_block_size = opt_size
      return

    ## Then try a couple different multiples of this base size to find best speed
    if options.verbose_block_finder:
      print("BF: Searching for optimal mult for block size", opt_size)
    max_chain_factor = 0
    opt_mult = 1
    mult = 1
    while (mult <= opt_mult + params.max_block_mult and
           mult * opt_size <= max_block_size):
      block_machine = Turing_Machine.Block_Macro_Machine(machine, mult*opt_size)
      back_machine = Turing_Machine.Backsymbol_Macro_Machine(block_machine)
      sim = Simulator(back_machine, new_options)
      sim.loop_seek(params.mult_sim_loops)
      if sim.op_state != Turing_Machine.RUNNING:
        result.best_block_size = mult * opt_size
        return
      chain_factor = sim.steps_from_chain / sim.steps_from_macro

      if options.verbose_block_finder:
        print("BF: *", mult, chain_factor)

      # Note that we prefer smaller multiples
      # We only choose larger multiples if they perform much better
      if chain_factor > 2 * max_chain_factor:
        max_chain_factor = chain_factor
        opt_mult = mult
      mult += 1

    result.best_mult = opt_mult
    result.best_chain_factor = max_chain_factor
    result.best_block_size = opt_mult * opt_size

  if options.verbose_block_finder:
    print("BF: Block Finder finished")
    print()
    print(result)
    sys.stdout.flush()

def uncompress_tape(compr_tape):
  """Expand out repetition counts in tape."""
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
