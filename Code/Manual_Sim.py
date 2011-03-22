#! /usr/bin/env python

import sys, string

from Macro import Turing_Machine, Simulator, Block_Finder
import IO

# White, Red, Blue, Green, Magenta, Cyan, Brown/Yellow
color = [49, 41, 44, 42, 45, 46, 43]
# Characters to use for states (end in "Z" so that halt is Z)
states = string.ascii_uppercase + string.ascii_lowercase + string.digits + "!@#$%^&*" + "Z"
symbols = string.digits + "-"
dirs = "LRS-"

def print_machine(machine):
  """
  Pretty-print the contents of the Turing machine.
  This method prints the state transition information
  (number to print, direction to move, next state) for each state
  but not the contents of the tape.
  """

  sys.stdout.write("\n")
  sys.stdout.write("Transition table:\n")
  sys.stdout.write("\n")

  TTable = machine.trans_table

  sys.stdout.write("       ")
  for j in xrange(len(TTable[0])):
    sys.stdout.write("+-----")
  sys.stdout.write("+\n")

  sys.stdout.write("       ")
  for j in xrange(len(TTable[0])):
    sys.stdout.write("|  %d  " % j)
  sys.stdout.write("|\n")

  sys.stdout.write("   +---")
  for j in xrange(len(TTable[0])):
    sys.stdout.write("+-----")
  sys.stdout.write("+\n")

  for i in xrange(len(TTable)):
    sys.stdout.write("   | %c " % states[i])
    for j in xrange(len(TTable[i])):
      sys.stdout.write("| ")
      if TTable[i][j][0] == -1 and \
         TTable[i][j][1] == -1 and \
         TTable[i][j][2] == -1:
        sys.stdout.write("--- ")
      else:
        sys.stdout.write("%c"   % symbols[TTable[i][j][0]])
        sys.stdout.write("%c"   % dirs   [TTable[i][j][1]])
        sys.stdout.write("%c "  % states [TTable[i][j][2]])
    sys.stdout.write("|\n")

    sys.stdout.write("   +---")
    for j in xrange(len(TTable[0])):
      sys.stdout.write("+-----")
    sys.stdout.write("+\n")

  sys.stdout.write("\n\n")

  sys.stdout.flush()


def run(TTable, block_size, back, prover, recursive, options):
  # Construct Machine (Backsymbol-k-Block-Macro-Machine)
  m = Turing_Machine.make_machine(TTable)

  # If no explicit block-size given, use inteligent software to find one
  if not block_size:
    block_size = 1

  if not options.quiet:
    print_machine(m)

  # Do not create a 1-Block Macro-Machine (just use base machine)
  if block_size != 1:
    m = Turing_Machine.Block_Macro_Machine(m, block_size)
  if back:
    m = Turing_Machine.Backsymbol_Macro_Machine(m)

  global sim
  sim = Simulator.Simulator(m, recursive, enable_prover=prover, init_tape=True,
                            compute_steps=options.compute_steps,
                            verbose_simulator=options.verbose_simulator,
                            verbose_prover=options.verbose_prover,
                            verbose_prefix="")
  if options.manual:
    return  # Let's us run the machine manually. Must be run as python -i Quick_Sim.py
  try:
    if options.quiet or options.verbose:  # Note verbose prints inside sim.step()
      while sim.op_state == Turing_Machine.RUNNING:
        sim.step()
    else:
      # TODO: maybe print based on time
      while sim.op_state == Turing_Machine.RUNNING:
        sim.print_self()
        sim.loop_run(options.print_loops)
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
                    "and prover.")
  parser.add_option("--verbose-prover", action="store_true",
                    help="Provide debugging output from prover.")
  parser.add_option("--verbose-simulator", action="store_true",
                    help="Provide debugging output from simulator.")
  parser.add_option("--verbose-block-finder", action="store_true",
                    help="Provide debugging output from block_finder.")
  parser.add_option("--print-loops", type=int, default=10000, metavar="LOOPS",
                    help="Print every LOOPS loops [Default %default].")
  
  parser.add_option("-b", "--no-backsymbol", dest="backsymbol",
                    action="store_false", default=True,
                    help="Turn off backsymbol macro machine")
  parser.add_option("-p", "--no-prover", dest="prover",
                    action="store_false", default=True,
                    help="Turn off proof system")
  parser.add_option("-r", "--recursive", action="store_true", default=False, 
                    help="Turn on recursive proof system")
  parser.add_option("--no-steps", dest="compute_steps",
                    action="store_false", default=True,
                    help="Don't keep track of base step count (can be expensive"
                    " to calculate especially with recursive proofs).")
  parser.add_option("--manual", action="store_true",
                    help="Don't run any simulation, just set up simulator "
                    "and quit. (Run as python -i Quick_Sim.py to interactively "
                    "run simulation.)")
  
  parser.add_option("-n", "--block-size", type=int,
                    help="Block size to use in macro machine simulator "
                    "(default is to guess with the block_finder algorithm)")
  
  (options, args) = parser.parse_args()
  
  if options.verbose:
    options.verbose_simulator = True
    options.verbose_prover = True
    options.verbose_block_finder = True
  
  # Verbose block finder
  Block_Finder.DEBUG = options.verbose_block_finder
  
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

