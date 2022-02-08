#! /usr/bin/env python
"""
Try Reverse_Engineer_Filter, CTL and then simulate TM as a Macro Machine using
the Proof System.
"""

import copy
from optparse import OptionParser, OptionGroup
import sys
import time

import Alarm
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

  group.add_option("--max-loops", type=int, default=INF,
                   help="Max simulator loops to run each simulation (0 for infinite). "
                   "[Default: infinite]")
  group.add_option("--time", type=int, default=15,
                   help="Max seconds to run each simulation. "
                   "[Default: %default]")
  group.add_option("--tape-limit", type=int, default=50,
                   help="Max tape size to allow.")
  group.add_option("--no-reverse-engineer", dest="reverse_engineer",
                   action="store_false", default=True,
                   help="Don't try Reverse_Engineer_Filter.")
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

def run_timer(ttable, options, stats, time_limit_sec):
  try:
    start_time = time.time()
    Alarm.ALARM.set_alarm(time_limit_sec)
    
    return run_options(ttable, options, stats)

    Alarm.ALARM.cancel_alarm()

  except Alarm.AlarmException:
    Alarm.ALARM.cancel_alarm()
    return Exit_Condition.TIME_OUT, (time.time() - start_time,)

def run_options(ttable, options, stats=None):
  """Run the Accelerated Turing Machine Simulator, running a few simple filters
  first and using intelligent blockfinding."""
  if options.max_loops == 0:
    options.max_loops = INF

  ## Test for quickly for infinite machine
  if options.reverse_engineer and Reverse_Engineer_Filter.test(ttable):
    # Note: quasihalting result is not computable when using Reverse_Engineer filter.
    return Exit_Condition.INFINITE, ("Reverse_Engineer", ("N/A", "N/A"))

  ## Construct the Macro Turing Machine (Backsymbol-k-Block-Macro-Machine)
  m = Turing_Machine.make_machine(ttable)

  block_size = options.block_size
  if not block_size:
    # If no explicit block-size given, use inteligent software to find one
    block_size = Block_Finder.block_finder(m, options)

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
        # Note: quasihalting result is not computed when using CTL filters.
        return Exit_Condition.INFINITE, ("CTL_A*", ("N/A", "N/A"))

      CTL_config_copy = copy.deepcopy(CTL_config)
      if CTL2.CTL(m, CTL_config_copy):
        # Note: quasihalting result is not computed when using CTL filters.
        return Exit_Condition.INFINITE, ("CTL_A*_B", ("N/A", "N/A"))

  ## Set up the simulator
  sim = Simulator.Simulator(m, options)

  ## Run the simulator

  while (sim.num_loops < options.max_loops and
         sim.op_state == Turing_Machine.RUNNING and
         sim.tape.compressed_size() <= options.tape_limit):
    sim.step()

  # TODO(shawn): pass the stats object into sim so we don't have to copy.
  if stats:
    stats.num_rules += len(sim.prover.rules)
    stats.num_recursive_rules += sim.prover.num_recursive_rules
    stats.num_collatz_rules += sim.prover.num_collatz_rules
    stats.num_failed_proofs += sim.prover.num_failed_proofs

  ## Resolve end conditions and return relevent info.
  if sim.tape.compressed_size() > options.tape_limit:
    return Exit_Condition.OVER_TAPE, (sim.tape.compressed_size(), sim.step_num)

  elif sim.op_state == Turing_Machine.RUNNING:
    return Exit_Condition.MAX_STEPS, (sim.step_num,)

  elif sim.op_state == Turing_Machine.HALT:
    return Exit_Condition.HALT, (sim.step_num, sim.get_nonzeros())

  elif sim.op_state == Turing_Machine.INF_REPEAT:
    return Exit_Condition.INFINITE, (sim.inf_reason, sim.inf_quasihalt)

  elif sim.op_state == Turing_Machine.UNDEFINED:
    on_symbol, on_state = sim.op_details[0][:2]
    return Exit_Condition.UNDEF_CELL, (on_state, on_symbol,
                                       sim.step_num, sim.get_nonzeros())

  elif sim.op_state == Turing_Machine.GAVE_UP:
    return Exit_Condition.UNKNOWN, (sim.op_state,) + sim.op_details

  raise Exception, (sim.op_state, ttable, sim)

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
  
  if options.time > 0:
    print run_timer(ttable, options, None, options.time)
  else:
    print run_options(ttable, options)
