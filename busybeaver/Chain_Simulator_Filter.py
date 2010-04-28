#! /usr/bin/env python

import copy
import os,sys

from Macro import Turing_Machine, Chain_Simulator, Block_Finder
import IO, Reverse_Engineer_Filter, CTL1, CTL2

from Macro.Chain_Tape import INF
from Alarm import ALARM, AlarmException

TIMEOUT = "Timeout"
OVERSTEPS = "Over_steps"
HALT = "Halt"
INFINITE = "Infinite_repeat"
UNDEFINED = "Undefined_Transition"

def run(TTable, options, steps=INF, runtime=None, block_size=None, 
                backsymbol=True, prover=True, recursive=False):
  """Run the Accelerated Turing Machine Simulator using intelligent blockfinding if no block_size is given."""
  for do_over in xrange(0,4):
    try:
      ## Construct the Macro Turing Machine (Backsymbol-k-Block-Macro-Machine)
      m = Turing_Machine.make_machine(TTable)

      if not block_size:
        try:
          ## Set the timer (if non-zero runtime)
          if runtime:
            ALARM.set_alarm(runtime/10.0)  # Set timer

          # If no explicit block-size given, use inteligent software to find one
          block_size = Block_Finder.block_finder(m, options.bf_limit1, options.bf_limit2, options.bf_run1, options.bf_run2, options.bf_extra_mult)

          ALARM.cancel_alarm()

        except AlarmException: # Catch Timer
          ALARM.cancel_alarm()

          block_size = 1

      # Do not create a 1-Block Macro-Machine (just use base machine)
      if block_size != 1:
        m = Turing_Machine.Block_Macro_Machine(m, block_size)

      if backsymbol:
        m = Turing_Machine.Backsymbol_Macro_Machine(m)


      ## Set up the simulator
      #global sim # Useful for Debugging
      sim = Chain_Simulator.Simulator()
      sim.init(m, recursive)
      if not prover:
        sim.proof = None

      try:
        if runtime:
          ALARM.set_alarm(runtime)  # Set timer

        ## Run the simulator
        sim.loop_seek(steps)

        ALARM.cancel_alarm()

      except AlarmException: # Catch Timer
        ALARM.cancel_alarm()
        return TIMEOUT, (runtime, sim.step_num)

      ## Resolve end conditions and return relevent info.
      if sim.op_state == Turing_Machine.RUNNING:
        return OVERSTEPS, (sim.step_num,)
      
      elif sim.op_state == Turing_Machine.HALT:
        return HALT, (sim.step_num, sim.get_nonzeros())
      
      elif sim.op_state == Turing_Machine.INF_REPEAT:
        return INFINITE, (sim.inf_reason,)
      
      elif sim.op_state == Turing_Machine.UNDEFINED:
        on_symbol, on_state = sim.op_details[0][:2]
        return UNDEFINED, (on_state, on_symbol, 
                           sim.step_num, sim.get_nonzeros())

    except AlarmException: # Catch Timer (unexpected!)
      ALARM.cancel_alarm()  # Turn off timer and try again

    sys.stderr.write("Weird1 (%d): %s\n" % (do_over,TTable))

  return TIMEOUT, (runtime, -1)

# Main script
if __name__ == "__main__":
  from optparse import OptionParser
  # Parse command line options.
  usage = "usage: %prog --infile= --outfile= [options]"
  parser = OptionParser(usage=usage)
  
  parser.add_option("--infile", dest="infilename", metavar="INFILE", help="Input file name (required, no default)")
  parser.add_option("--outfile", dest="outfilename", metavar="OUTFILE", help="Output file name (required, no default)")
  parser.add_option("--log_number", help="Number in the log file of this run")
  parser.add_option("-s", "--steps", type=int, default=0, help="Maximum number of steps to simulate for use 0 for infinite [Default: infinite]")
  parser.add_option("-t", "--time", type=int, default=15, help="Maximum number of seconds to simulate for [Default: %default]")
  
  parser.add_option("-b", "--no-backsymbol", action="store_false", dest="backsymbol", default=True, 
                    help="Turn off backsymbol macro machine")
  parser.add_option("-p", "--no-prover", action="store_false", dest="prover", default=True, 
                    help="Turn off proof system")
  parser.add_option("-r", "--recursive", action="store_true", default=False, 
                    help="Turn ON recursive proof system [Very Experimental]")
  
  parser.add_option("-n", "--block-size", type=int, help="Block size to use in macro machine simulator (default is to guess with the block_finder algorithm)")
  
  block_options = OptionGroup(parser, "Block Finder options")
  block_options.add_option("--bf-limit1", type=int, default=1000, metavar="LIMIT", help="Number of steps to run the first half of block finder [Default: %default].")
  block_options.add_option("--bf-limit2", type=int, default=1000, metavar="LIMIT", help="Number of stpes to run the second half of block finder [Default: %default].")
  block_options.add_option("--bf-run1", action="store_true", default=True, help="In first half, find worst tape before limit.")
  block_options.add_option("--bf-no-run1", action="store_false", dest="bf_run1", help="In first half, just run to limit.")
  block_options.add_option("--bf-run2", action="store_true", default=True, help="Run second half of block finder.")
  block_options.add_option("--bf-no-run2", action="store_false", dest="bf_run2", help="Don't run second half of block finder.")
  block_options.add_option("--bf-extra-mult", type=int, default=2, metavar="MULT", help="How far ahead to search in second half of block finder.")
  parser.add_option_group(block_options)
  
  (options, args) = parser.parse_args()

  if not options.infilename or not options.outfilename:
    parser.error("--infile= and --outfile= are required parameters")

  infile  = file(options.infilename,  "r")

  if os.path.exists(outfilename):
    sys.stderr.write("Output test file, '%s', exists\n" % outfilename)
    sys.exit(1)
  else:
    outfile = file(options.outfilename, "w")
  
  if options.steps == 0:
    options.steps = INF

  io   = IO.IO(infile, outfile)
  next = io.read_result()

  while next:
    ttable = next[6]

    # Run the simulator/filter on this machine (with an optional timer)
    try:
      if runtime:
        ALARM.set_alarm(runtime)

      success = type_func.test_CTL(ttable, cutoff, block_size, offset)
  print run(ttable, options, options.steps, options.time, options.block_size, 
                    options.backsymbol, options.prover, options.recursive)

      ALARM.cancel_alarm()

    except AlarmException:
      ALARM.cancel_alarm()

      success = False

    # If we could not decide anything, leave the old result alone.
    if not success:
      io.write_result_raw(*next)
    # Otherwise classify it as beeing decided in some way.
    else:
      old_results = next[5]
      io.write_result_raw(*(next[0:5]+(results, ttable, log_number, old_results)))

    next = io.read_result()
