#! /usr/bin/env python
#
# Macro_Simulator.py
#
"""
Run a given TM for a given number of steps and the result.
"""

import copy
from optparse import OptionParser, OptionGroup
import sys

from Alarm import ALARM, AlarmException
from Common import Exit_Condition, GenContainer
import CTL1
import CTL2
import IO
from Macro import Turing_Machine, Simulator, Block_Finder
from Macro.Tape import INF
import Reverse_Engineer_Filter

def add_option_group(parser):
  """Add Macro_Simulator options group to an OptParser parser object."""
  assert isinstance(parser, OptionParser)

  group = OptionGroup(parser, "Macro Simulator options")

  group.add_option("--steps", type=int, default=INF,
                   help="Max steps to run each simulation (0 for infinite). "
                   "[Default: infinite]")
  group.add_option("--time", type=float, default=15.0,
                   help="Max seconds to run each simulation. "
                   "[Default: %default]")
  group.add_option("--tape-limit", type=int, default=50,
                   help="Max tape size to allow.")
  group.add_option("--no-ctl", dest="ctl", action="store_false", default=True,
                   help="Don't try CTL optimization.")

  parser.add_option_group(group)

  Simulator.add_option_group(parser)
  Block_Finder.add_option_group(parser)

def create_default_options():
  """Returns a set of default options."""
  parser = OptionParser()
  add_option_group(parser)
  options, args = parser.parse_args([])
  return options

def setup_CTL(m, cutoff):
  options = create_default_options()
  options.prover = False
  sim = Simulator.Simulator(m, options)
  sim.seek(cutoff)

  if sim.op_state != Turing_Machine.RUNNING:
    return False

  tape = [None, None]

  for d in range(2):
    tape[d] = [block.symbol for block in reversed(sim.tape.tape[d])
               if block.num != "Inf"]

  config = GenContainer(state=sim.state, dir=sim.dir, tape=tape)
  return config

def run_options(ttable, options, stats=None):
  """Run the Accelerated Turing Machine Simulator, running a few simple filters
  first and using intelligent blockfinding."""
  if options.steps == 0:
    options.steps = INF

  for do_over in xrange(0,4):
    try:
      ## Test for quickly for infinite machine
      if Reverse_Engineer_Filter.test(ttable):
        return Exit_Condition.INFINITE, ("Reverse_Engineer",)

      ## Construct the Macro Turing Machine (Backsymbol-k-Block-Macro-Machine)
      m = Turing_Machine.make_machine(ttable)

      try:
        # Set the timer (if non-zero runtime)
        if options.time:
          ALARM.set_alarm(options.time/10.0)  # Set timer

        block_size = options.block_size
        if not block_size:
          # If no explicit block-size given, use inteligent software to find one
          block_size = Block_Finder.block_finder(m, options)

          ALARM.cancel_alarm()

        # Do not create a 1-Block Macro-Machine (just use base machine)
        if block_size != 1:
          m = Turing_Machine.Block_Macro_Machine(m, block_size)

        if options.backsymbol:
          m = Turing_Machine.Backsymbol_Macro_Machine(m)

        if options.ctl:
          CTL_config = setup_CTL(m, options.bf_limit1)

          # Run CTL filters unless machine halted
          if CTL_config:
            CTL_config_copy = copy.deepcopy(CTL_config)
            if CTL1.CTL(m, CTL_config_copy):
              ALARM.cancel_alarm()
              return Exit_Condition.INFINITE, ("CTL_A*",)

            CTL_config_copy = copy.deepcopy(CTL_config)
            if CTL2.CTL(m, CTL_config_copy):
              ALARM.cancel_alarm()
              return Exit_Condition.INFINITE, ("CTL_A*_B",)

        ALARM.cancel_alarm()

      except AlarmException:
        ALARM.cancel_alarm()

      # If alarm kills us before we make a backsymbol machine, do it here.
      if (options.backsymbol and
          not isinstance(m, Turing_Machine.Backsymbol_Macro_Machine)):
        m = Turing_Machine.Backsymbol_Macro_Machine(m)

      ## Set up the simulator
      sim = Simulator.Simulator(m, options)

      try:
        if options.time:
          ALARM.set_alarm(options.time)  # Set timer

        ## Run the simulator
        while (sim.step_num < options.steps and
               sim.op_state == Turing_Machine.RUNNING and
               sim.tape.compressed_size() <= options.tape_limit):
          sim.step()

        ALARM.cancel_alarm()

        # TODO(shawn): pass the stats object into sim so we don't have to copy.
        if stats:
          stats.num_rules += len(sim.prover.rules)
          stats.num_recursive_rules += sim.prover.num_recursive_rules
          stats.num_collatz_rules += sim.prover.num_collatz_rules
          stats.num_failed_proofs += sim.prover.num_failed_proofs

      except AlarmException: # Catch Timer
        ALARM.cancel_alarm()
        return Exit_Condition.TIME_OUT, (options.time, sim.step_num)

      ## Resolve end conditions and return relevent info.
      if sim.tape.compressed_size() > options.tape_limit:
        return Exit_Condition.UNKNOWN, "Over_Tape", sim.tape.compressed_size()
      if sim.op_state == Turing_Machine.RUNNING:
        return Exit_Condition.MAX_STEPS, (sim.step_num,)

      elif sim.op_state == Turing_Machine.HALT:
        return Exit_Condition.HALT, (sim.step_num, sim.get_nonzeros())

      elif sim.op_state == Turing_Machine.INF_REPEAT:
        return Exit_Condition.INFINITE, (sim.inf_reason,)

      elif sim.op_state == Turing_Machine.UNDEFINED:
        on_symbol, on_state = sim.op_details[0][:2]
        return Exit_Condition.UNDEF_CELL, (on_state, on_symbol,
                                           sim.step_num, sim.get_nonzeros())

    except AlarmException:  # Catch Timer (unexpected!)
      ALARM.cancel_alarm()  # Turn off timer and try again

    sys.stderr.write("Weird1 (%d): %s\n" % (do_over, ttable))

  return Exit_Condition.TIME_OUT, (options.time, -1)

# Main script
if __name__ == "__main__":
  # Parse command line options.
  usage = "usage: %prog [options] machine_file [line_number]"
  parser = OptionParser(usage=usage)
  add_option_group(parser)
  (options, args) = parser.parse_args()


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

  print run_options(ttable, options)
