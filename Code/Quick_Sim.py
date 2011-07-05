#! /usr/bin/env python
#
# Quick_Sim.py
#
"""
A TM simulator with a variety of advanced features, options, and output
formats.
"""

import sys, string

from Macro import Turing_Machine, Simulator, Block_Finder
import IO

def run(TTable, block_size, back, prover, recursive, options):
  # Construct Machine (Backsymbol-k-Block-Macro-Machine)
  m = Turing_Machine.make_machine(TTable)

  # If no explicit block-size given, use inteligent software to find one
  if not block_size:
    block_size = Block_Finder.block_finder(m, options)

  if not options.quiet:
    Turing_Machine.print_machine(m)

  # Do not create a 1-Block Macro-Machine (just use base machine)
  if block_size != 1:
    m = Turing_Machine.Block_Macro_Machine(m, block_size)
  if back:
    m = Turing_Machine.Backsymbol_Macro_Machine(m)

  global sim  # For debugging, especially with --manual
  sim = Simulator.Simulator(m, options)

  if options.manual:
    return  # Let's us run the machine manually. Must be run as python -i Quick_Sim.py
  try:
    if options.quiet or options.verbose:  # Note verbose prints inside sim.step()
      if options.verbose:
        sim.verbose_print()

      total_loops = 0;

      while (sim.op_state == Turing_Machine.RUNNING and
             (options.loops == 0 or total_loops < options.loops)):
        sim.step()
        total_loops += 1;
    else:
      # TODO: maybe print based on time
      total_loops = 0;

      while (sim.op_state == Turing_Machine.RUNNING and
             (options.loops == 0 or total_loops < options.loops)):
        sim.print_self()
        sim.loop_run(options.print_loops)
        total_loops += options.print_loops;
  finally:
    sim.print_self()

  if sim.op_state == Turing_Machine.HALT:
    print
    print "Turing Machine Halted!"
    print
    if options.compute_steps:
      print "Steps:   ", sim.step_num
    print "Nonzeros:", sim.get_nonzeros()
    print
  elif sim.op_state == Turing_Machine.INF_REPEAT:
    print
    print "Turing Machine proven Infinite!"
    print "Reason:", sim.inf_reason
  elif sim.op_state == Turing_Machine.UNDEFINED:
    print
    print "Turing Machine reached Undefined transition!"
    print "State: ", sim.op_details[0][1]
    print "Symbol:", sim.op_details[0][0]
    print
    if options.compute_steps:
      print "Steps:   ", sim.step_num
    print "Nonzeros:", sim.get_nonzeros()
    print


if __name__ == "__main__":
  from optparse import OptionParser, OptionGroup
  # Parse command line options.
  usage = "usage: %prog [options] machine_file [line_number]"
  parser = OptionParser(usage=usage)
  # TODO: One variable for different levels of verbosity.
  # TODO: Combine optparsers from MacroMachine, Enumerate and here.
  parser.add_option("-q", "--quiet", action="store_true", help="Brief output")
  parser.add_option("-v", "--verbose", action="store_true",
                    help="Print step-by-step informaion from simulator "
                    "and prover (Overrides other --verbose-* flags).")
  parser.add_option("-l", "--loops", type=int, default=0,
                    help="Specify a maximum number of loops.")
  parser.add_option("--print-loops", type=int, default=10000, metavar="LOOPS",
                    help="Print every LOOPS loops [Default %default].")
  
  parser.add_option("--manual", action="store_true",
                    help="Don't run any simulation, just set up simulator "
                    "and quit. (Run as python -i Quick_Sim.py to interactively "
                    "run simulation.)")

  Simulator.add_option_group(parser)
  Block_Finder.add_option_group(parser)
  
  (options, args) = parser.parse_args()

  if options.quiet:
    options.verbose_simulator = False
    options.verbose_prover = False
    options.verbose_block_finder = False
  elif options.verbose:
    options.verbose_simulator = True
    options.verbose_prover = True
    options.verbose_block_finder = True
  
  if len(args) < 1:
    parser.error("Must have at least one argument, machine_file")
  filename = args[0]
  
  if len(args) >= 2:
    try:
      line = int(args[1])
    except ValueError:
      parser.error("line_number must be an integer.")
    if line < 1:
      parser.error("line_number must be >= 1")
  else:
    line = 1
  
  ttable = IO.load_TTable_filename(filename, line)
  
  run(ttable, options.block_size, options.backsymbol, options.prover, 
              options.recursive, options)

