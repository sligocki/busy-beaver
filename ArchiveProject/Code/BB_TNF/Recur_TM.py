#! /usr/bin/env python
#
# Recur_Fit.py
#
"""
Attempt to find repeating patterns in the tape and fit a recurrence relation
to the exponents and number of step in the repeating pattern.
"""

import sys, string, copy, numpy

from Macro import Simulator, Block_Finder
import IO
from Recur import recur_TM

if __name__ == "__main__":
  from optparse import OptionParser, OptionGroup

  from Option_Parser import open_infile

  # Parse command line options.
  usage = "usage: %prog [options] machine_file"
  parser = OptionParser(usage=usage)
  # TODO: One variable for different levels of verbosity.
  # TODO: Combine optparsers from MacroMachine, Enumerate and here.
  parser.add_option("-q", "--quiet", action="store_true", help="Brief output")
  parser.add_option("-v", "--verbose", action="store_true",
                    help="Print step-by-step informaion from simulator "
                    "and prover (Overrides other --verbose-* flags).")
  parser.add_option("-l", "--loops", type=int, default=1000,
                    help="Specify a maximum number of loops [Default %default].")
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

  if options.print_loops > options.loops:
    options.print_loops = options.loops

  if len(args) < 1:
    parser.error("Must have one argument, machine_file")
  infilename = args[0]

  infile = open_infile(infilename)

  io = IO.IO(infile, None, None)

  # For each TM, try to find a recurrence relation for the powers in a
  # recurring stripped configuration and the number of steps
  for io_record in io:
    # Get the current TM transition table
    ttable = io_record.ttable

    # Attempt to find the recurrence relations
    recur_TM(ttable, options.block_size, options.backsymbol, options.prover,
                     options.recursive, options)
