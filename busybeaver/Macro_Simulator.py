#! /usr/bin/env python

import copy
import math
import sys
import signal

import signalPlus

from Macro import Turing_Machine, Chain_Simulator, Block_Finder
import IO, Reverse_Engineer_Filter, CTL1, CTL2

from Macro.Chain_Tape import INF

TIMEOUT = "Timeout"
OVERSTEPS = "Over_steps"
HALT = "Halt"
INFINITE = "Infinite_repeat"
UNDEFINED = "Undefined_Transition"


class AlarmException(Exception):
  """An exception to be tied to a timer running out."""

def AlarmHandler(signum, frame):
  raise AlarmException, "Timeout!"

# Attach the alarm signal to the alarm exception.
#   so signalPlus.alarm will cause a catchable exception.
signal.signal(signal.SIGALRM, AlarmHandler)


class GenContainer:
  """Generic Container class"""
  def __init__(self, **args):
    for atr in args:
      self.__dict__[atr] = args[atr]


def setup_CTL(m, cutoff):
  sim = Chain_Simulator.Simulator()
  sim.init(m)
  sim.proof = None
  sim.seek(cutoff)
  if sim.op_state != Turing_Machine.RUNNING:
    return False
  tape = [None, None]
  for d in range(2):
    tape[d] = [block.symbol for block in reversed(sim.tape.tape[d]) if block.num != "Inf"]
  config = GenContainer(state=sim.state, dir=sim.dir, tape=tape)
  return config

def run(TTable, options, steps=INF, runtime=None, block_size=None, 
                back=True, prover=True, rec=False):
  """Run the Accelerated Turing Machine Simulator, running a few simple filters first and using intelligent blockfinding."""

  for do_over in xrange(0,4):
    try:
      ## Test for quickly for infinite machine
      if Reverse_Engineer_Filter.test(TTable):
        return INFINITE, ("Reverse_Engineered",)
      
      ## Construct the Macro Turing Machine (Backsymbol-k-Block-Macro-Machine)
      m = Turing_Machine.make_machine(TTable)

      try:
        ## Set the timer (if non-zero runtime)
        if runtime:
          signalPlus.alarm(runtime/10.0)  # Set timer

        # If no explicit block-size given, use inteligent software to find one
        if not block_size:
          block_size = Block_Finder.block_finder(m, options.bf_limit1, options.bf_limit2, options.bf_run1, options.bf_run2, options.bf_extra_mult)

        signalPlus.alarm(0)  # Turn off timer

      except AlarmException: # Catch Timer (unexcepted)
        signalPlus.alarm(0)  # Turn off timer
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
            signalPlus.alarm(runtime/10.0)

          CTL_config_copy = copy.deepcopy(CTL_config)
          if CTL1.CTL(m, CTL_config_copy):
            signalPlus.alarm(0)  # Turn off timer
            return INFINITE, ("CTL_A*",)

          CTL_config_copy = copy.deepcopy(CTL_config)
          if CTL2.CTL(m, CTL_config_copy):
            signalPlus.alarm(0)  # Turn off timer
            return INFINITE, ("CTL_A*_B",)

        except AlarmException:
          signalPlus.alarm(0)  # Turn off timer

      ## Set up the simulator
      #global sim # Useful for Debugging
      sim = Chain_Simulator.Simulator()
      sim.init(m, rec)
      if not prover:
        sim.proof = None

      try:
        if runtime:
          signalPlus.alarm(runtime)  # Set timer

        ## Run the simulator
        sim.seek(steps)

        signalPlus.alarm(0)  # Turn off timer

      except AlarmException: # Catch Timer
        signalPlus.alarm(0)  # Turn off timer
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
      signalPlus.alarm(0)  # Turn off timer and try again

    sys.stderr.write("Weird (%d): %s\n" % (do_over,TTable))

  return TIMEOUT, (runtime, -1)

# Main script
if __name__ == "__main__":
  from optparse import OptionParser
  # Parse command line options.
  usage = "usage: %prog [options] machine_file [line_number]"
  parser = OptionParser(usage=usage)
  #parser.set_defaults(verbose=True)
  #parser.add_option("-q", "--quiet", action="store_true", help="Brief output")
  #parser.add_option("--verbose-prover", action="store_true", help="Provide debuggin output from prover")
  #parser.add_option("--verbose-simulator", action="store_true", help="Provide debuggin output from simulator")
  
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
