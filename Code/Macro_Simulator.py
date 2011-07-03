#! /usr/bin/env python
#
# Macro_Simulator.py
#
"""
"""

import copy
from optparse import OptionParser, OptionGroup
import sys

from Alarm import ALARM, AlarmException
from Common import Exit_Condition
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

  parser.add_option_group(group)

  Simulator.add_option_group(parser)
  Block_Finder.add_option_group(parser)

def create_default_options():
  """Returns a set of default options."""
  parser = OptionParser()
  add_option_group(parser)
  options, args = parser.parse_args([])
  return options

class GenContainer(object):
  """Generic Container class"""
  def __init__(self, **args):
    for atr in args:
      self.__dict__[atr] = args[atr]

def setup_CTL(m, cutoff):
  options = create_default_options()
  options.prover = False
  sim = Simulator.Simulator(m, options)
  sim.seek(cutoff)

  if sim.op_state != Turing_Machine.RUNNING:
    return False

  tape = [None, None]

  for d in range(2):
    tape[d] = [block.symbol for block in reversed(sim.tape.tape[d]) if block.num != "Inf"]

  config = GenContainer(state=sim.state, dir=sim.dir, tape=tape)
  return config

def run_options(ttable, options):
  """Run the Accelerated Turing Machine Simulator, running a few simple filters
  first and using intelligent blockfinding."""
  return run(ttable, options, options.steps, options.time, options.block_size,
             options.backsymbol, options.prover, options.recursive)

def run(TTable, options, steps=INF, runtime=None, block_size=None, 
                back=True, prover=True, rec=False):
  """Legacy interface, use run_options."""
  for do_over in xrange(0,4):
    try:
      ## Test for quickly for infinite machine
      if Reverse_Engineer_Filter.test(TTable):
        return Exit_Condition.INFINITE, ("Reverse_Engineer",)

      ## Construct the Macro Turing Machine (Backsymbol-k-Block-Macro-Machine)
      m = Turing_Machine.make_machine(TTable)

      if not block_size:
        try:
          ## Set the timer (if non-zero runtime)
          if runtime:
            ALARM.set_alarm(runtime/10.0)  # Set timer

          # If no explicit block-size given, use inteligent software to find one
          block_size = Block_Finder.block_finder(m, options)

          ALARM.cancel_alarm()

        except AlarmException: # Catch Timer
          ALARM.cancel_alarm()

          block_size = 1

      # Do not create a 1-Block Macro-Machine (just use base machine)
      if block_size != 1:
        m = Turing_Machine.Block_Macro_Machine(m, block_size)

      if back:
        m = Turing_Machine.Backsymbol_Macro_Machine(m)

      CTL_config = setup_CTL(m, options.bf_limit1)

      # Run CTL filters unless machine halted
      if CTL_config:
        try:
          if runtime:
            ALARM.set_alarm(runtime/10.0)

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

      ## Set up the simulator
      #global sim # Useful for Debugging
      sim = Simulator.Simulator(m, options)

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

    except AlarmException: # Catch Timer (unexpected!)
      ALARM.cancel_alarm()  # Turn off timer and try again

    sys.stderr.write("Weird1 (%d): %s\n" % (do_over,TTable))

  return Exit_Condition.TIME_OUT, (runtime, -1)

# Main script
if __name__ == "__main__":
  # Parse command line options.
  usage = "usage: %prog [options] machine_file [line_number]"
  parser = OptionParser(usage=usage)
  add_option_group(parser)
  (options, args) = parser.parse_args()
  
  
  if options.steps == 0:
    options.steps = INF

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
  
  print run(ttable, options, options.steps, options.time, options.block_size, 
                    options.backsymbol, options.prover, options.recursive)
