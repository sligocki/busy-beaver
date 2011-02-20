#! /usr/bin/env python
"""Tree Filter which uses the Macro Machine Simulator."""

from Common import Exit_Condition
import IO
from Macro import Simulator, Turing_Machine, Block_Finder
from Alarm import ALARM, AlarmException

# TODO(shawn): Get rid of bad global vars :/
max_step2inf = 0
max_loop2inf = 0

def run(TTable, block_size, steps, runtime, recursive, progress):
  # Get and initialize a new simulator object.
  m1 = Turing_Machine.Simple_Machine(TTable)
  if not block_size:
    # Find optimal macro block size automatically.
    block_size = Block_Finder.block_finder(m1, steps // 10)
  m2 = Turing_Machine.Block_Macro_Machine(m1, block_size)
  m3 = Turing_Machine.Backsymbol_Macro_Machine(m2)

  sim = Simulator.Simulator(m3, recursive)

  # Run with an optional timer.
  try:
    if runtime:
      ALARM.set_alarm(runtime)
      
    sim.loop_run(steps)

    ALARM.cancel_alarm()

  except AlarmException:
    ALARM.cancel_alarm()
    sim.op_state = Turing_Machine.TIME_OUT

  if sim.op_state == Turing_Machine.RUNNING:
    if progress:
      pass #print "\tUnknown", block_size, sim.step_num, sim.num_loops
    # TODO(shawn): Return time taken.
    return Exit_Condition.UNKNOWN, "Max_Steps", sim.get_nonzeros(), sim.step_num

  elif sim.op_state == Turing_Machine.TIME_OUT:
    if progress:
      print "\tTimeout", block_size, sim.step_num, sim.num_loops
    return Exit_Condition.UNKNOWN, "Timeout", sim.get_nonzeros(), sim.step_num

  elif sim.op_state == Turing_Machine.INF_REPEAT:
    if progress:
      global max_step2inf, max_loop2inf
      max_step2inf = max(max_step2inf, sim.step_num)
      max_loop2inf = max(max_loop2inf, sim.num_loops)
      print "\tInfinite", block_size, (sim.step_num, max_step2inf),
      print (sim.num_loops, max_loop2inf)
    return (Exit_Condition.INFINITE, "Macro_Simulator",
            block_size, len(sim.prover.rules), sim.prover.num_recursive_rules,
            sim.step_num, sim.num_loops)

  elif sim.op_state == Turing_Machine.HALT:
    if progress:
      print "\tHalted", sim.get_nonzeros(), sim.step_num
    return (Exit_Condition.HALT, sim.get_nonzeros(), sim.step_num,
            "Macro_Simulator", block_size, len(sim.prover.rules),
            sim.prover.num_recursive_rules, sim.num_loops)

  elif sim.op_state == Turing_Machine.UNDEFINED:
    if progress:
      print "\tUndefined", sim.get_nonzeros(), sim.step_num
    # sim.op_details[0][0 & 1] stores the symbol and state that we halted on.
    return (Exit_Condition.UNDEF_CELL, sim.op_details[0][1], sim.op_details[0][0],
            sim.get_nonzeros(), sim.step_num, "Macro_Simulator", block_size,
            len(sim.prover.rules), sim.prover.num_recursive_rules, sim.num_loops)

  else:
    raise Exception, "unexpected op_state"

if __name__ == "__main__":
  from optparse import OptionParser
  import sys

  from Option_Parser import open_infile, open_outfile

  # Parse command line options
  usage = "usage: %prog --infile= --outfile= [options]"
  parser = OptionParser(usage=usage)
  # General options:
  parser.add_option("--infile", help="Input file name.")
  parser.add_option("--outfile", help="Output file name.")
  parser.add_option("--log_number", type=int, metavar="NUM",
                    help="Log number to use in output file.")
  # Macro_Simulator specific:
  parser.add_option("-n", "--block-size", type=int,
                    help="Block size to use in macro machine simulator "
                    "(default is to guess with the block_finder algorithm).")
  parser.add_option("--steps", type=int, default=10000,
                    help="Max simulation loops to run each machine for "
                    "(0 for infinite) [Default: %default].")
  parser.add_option("--time", type=float,
                    help="Max (real) time (in seconds) to run each simulation "
                    "for (default is no time limit).")
  parser.add_option("-r", "--recursive", action="store_true", default=False,
                    help="Turn on recursive proof system.")
  parser.add_option("--progress", action="store_true", default=False,
                    help="Print progress to stdout.")

  (options, args) = parser.parse_args()

  if not options.infile:
    parser.error("--infile is a required parameter.")
  if not options.outfile:
    parser.error("--outfile is a required parameter.")

  infile = open_infile(options.infile)
  outfile = open_outfile(options.outfile)
  io = IO.IO(infile, outfile, options.log_number)

  num_halt = 0
  num_undefined = 0

  for io_record in io:
    # Run the simulator/filter on this machine.
    sim_results = run(io_record.ttable, options.block_size, options.steps, 
                      options.time, options.recursive, options.progress)

    # If we could not decide anything, leave the old io_record alone.
    if sim_results[0] in Exit_Condition.UNKNOWN_SET:
      io.write_record(io_record)
    # Otherwise classify it as beeing decided in some way.
    else:
      # We do not expect to find halting machines with this filter.
      # However, finding them is not a problem, but user should know.
      if sim_results[0] == Exit_Condition.HALT:
        num_halt += 1
      if sim_results[0] == Exit_Condition.UNDEF_CELL:
        num_undefined += 1
      io_record.extended_results = ([Exit_Condition.name(io_record.category)] +
                                 io_record.category_reason)
      io_record.category = sim_results[0]
      io_record.category_reason = sim_results[1:]
      io_record.log_number = options.log_number
      io.write_record(io_record)

  # Print number of TMs that halted.
  if num_halt > 0:
    print >>sys.stderr, num_halt, "in file:", options.infile, "- halted!"

  # Print number of TMs that reached an undefined transition.
  if num_undefined > 0:
    print >>sys.stderr, num_undefined, "in file:", options.infile,
    print >>sys.stderr, "- undefined transitions reached!"
