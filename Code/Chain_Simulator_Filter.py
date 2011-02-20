#! /usr/bin/env python

import copy
import os
import sys

from Common import Exit_Condition
import Turing_Machine
import IO
import Macro.Block_Finder
import Macro.Turing_Machine
import Macro.Simulator

from Macro.Tape import INF
from Alarm import ALARM, AlarmException

#TIMEOUT = "Time_Out"
#OVERSTEPS = "Over_steps"
#HALT = "Halt"
#INFINITE = "Infinite_repeat"
#UNDEFINED = "Undefined_Transition"

def run(TTable, options, steps=INF, runtime=None, block_size=None, 
                backsymbol=True, prover=True, recursive=False):
  """Run the Accelerated Turing Machine Simulator using intelligent blockfinding if no block_size is given."""
  for do_over in xrange(0,4):
    try:
      ## Construct the Macro Turing Machine (Backsymbol-k-Block-Macro-Machine)
      m = Macro.Turing_Machine.make_machine(TTable)

      if not block_size:
        try:
          ## Set the timer (if non-zero runtime)
          if runtime:
            ALARM.set_alarm(runtime/10.0)  # Set timer

          # If no explicit block-size given, use inteligent software to find one
          block_size = Macro.Block_Finder.block_finder(m, options.bf_limit1, options.bf_limit2, options.bf_run1, options.bf_run2, options.bf_extra_mult)

          ALARM.cancel_alarm()

        except AlarmException: # Catch Timer
          ALARM.cancel_alarm()

          block_size = 1

      # Do not create a 1-Block Macro-Machine (just use base machine)
      if block_size != 1:
        m = Macro.Turing_Machine.Block_Macro_Machine(m, block_size)

      if backsymbol:
        m = Macro.Turing_Machine.Backsymbol_Macro_Machine(m)


      ## Set up the simulator
      #global sim # Useful for Debugging
      sim = Macro.Simulator.Simulator(m, recursive, enable_prover=prover)

      try:
        if runtime:
          ALARM.set_alarm(runtime)  # Set timer

        ## Run the simulator
        sim.loop_seek(steps)

        ALARM.cancel_alarm()

      except AlarmException: # Catch Timer
        ALARM.cancel_alarm()
        return Exit_Condition.TIME_OUT, (runtime, sim.step_num)

      ## Resolve end conditions and return relevent info.
      if sim.op_state == Macro.Turing_Machine.RUNNING:
        return Exit_Condition.MAX_STEPS, (sim.step_num,)
      
      elif sim.op_state == Macro.Turing_Machine.HALT:
        return Exit_Condition.HALT, (sim.step_num, sim.get_nonzeros())
      
      elif sim.op_state == Macro.Turing_Machine.INF_REPEAT:
        return Exit_Condition.INFINITE, (sim.inf_reason,)
      
      elif sim.op_state == Macro.Turing_Machine.UNDEFINED:
        on_symbol, on_state = sim.op_details[0][:2]
        return Exit_Condition.UNDEF_CELL, (on_state, on_symbol, 
                           sim.step_num, sim.get_nonzeros())

    except AlarmException: # Catch Timer (unexpected!)
      ALARM.cancel_alarm()  # Turn off timer and try again

    sys.stderr.write("Weird1 (%d): %s\n" % (do_over,TTable))

  return Exit_Condition.TIME_OUT, (runtime, -1)

# Main script
if __name__ == "__main__":
  from optparse import OptionParser, OptionGroup

  # Parse command line options.
  usage = "usage: %prog --infile= --outfile= --log_number= [options]"
  parser = OptionParser(usage=usage)
  
  parser.add_option("--infile", dest="infilename", metavar="INFILE", help="Input file name (required, no default)")
  parser.add_option("--outfile", dest="outfilename", metavar="OUTFILE", help="Output file name (required, no default)")
  parser.add_option("--log_number", help="Number in the log file of this run (required, no default)")
  parser.add_option("-s", "--steps", type=int, default=0, help="Maximum number of steps to simulate for use 0 for infinite [Default: infinite]")
  parser.add_option("-t", "--time", type=float, default=15.0, help="Maximum number of seconds to simulate for [Default: %default]")
  
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

  if not options.infilename or not options.outfilename or not options.log_number:
    parser.error("--infile=, --outfile=, and --log_number= are required parameters")

  infile  = file(options.infilename,  "r")

  if os.path.exists(options.outfilename):
    sys.stderr.write("Output test file, '%s', exists\n" % options.outfilename)
    sys.exit(1)
  else:
    outfile = file(options.outfilename, "w")
  
  if options.steps == 0:
    options.steps = INF

  log_number = int(options.log_number)

  io = IO.IO(infile, outfile, log_number)

  next = io.read_result()

  while next:
    old_results = next[5]
    ttable      = next[6]

    # Run the simulator/filter on this machine
    cond, info = run(ttable, options, options.steps, options.time,
                     options.block_size, options.backsymbol, options.prover,
                     options.recursive)

    # Output the result
    if cond == Exit_Condition.UNDEF_CELL:
      on_state, on_symbol, steps, score = info
      results = (Exit_Condition.UNDEF_CELL, on_state, on_symbol, score, steps)
    elif cond == Exit_Condition.HALT:
      steps, score = info
      results = (Exit_Condition.HALT, score, steps)
    elif cond == Exit_Condition.INFINITE:
      reason, = info
      results = (Exit_Condition.INFINITE, reason)
    elif cond == Exit_Condition.MAX_STEPS:
      steps, = info
      results = (Exit_Condition.MAX_STEPS, steps)
    elif cond == Exit_Condition.TIME_OUT:
      runtime, steps = info
      results = (Exit_Condition.TIME_OUT, runtime, steps)
    else:
      raise Exception, "Unexpected TM condition (%r)" % cond

    io.write_result_raw(*(next[0:5]+(results, ttable, log_number, old_results)))

    next = io.read_result()
