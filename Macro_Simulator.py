#! /usr/bin/env python

import sys, signal
from Macro import Turing_Machine, Chain_Simulator, Block_Finder
import IO, Reverse_Engineer_Filter
import math

from Macro.Chain_Tape import INF

TIMEOUT = "Timeout"
OVERSTEPS = "Over steps"
HALT = "Halt"
INFINITE = "Infinite repeat"
UNDEFINED = "Undefined Transition"


def signal2exception(excep):
  """Creates a custom signal handler that immediately raises a chosen exception"""
  def catchException(*args):
    raise excep, args
  return catchException
class AlarmException(Exception):
  """An exception to be tied to a timer running out."""
  pass
# Attach the alarm signal to the alarm exception.
#   so signal.alarm will cause a catchable exception.
signal.signal(signal.SIGALRM, signal2exception(AlarmException))


def run(TTable, steps=INF, time=None, block_size=None, back=True, prover=True, rec=False):
  """Run the Accelerated Turing Machine Simulator, running a few simple filters first and using intelligent blockfinding."""

  ## Test for quickly for infinite machine
  res = Reverse_Engineer_Filter.test(TTable)
  if res:
    return INFINITE, ("Reverse_Engineered",)
  
  ## Construct the Macro Turing Machine (Backsymbol-k-Block-Macro-Machine)
  m = Turing_Machine.Simple_Machine(TTable)

  try:
    ## Set the timer (if non-zero time)
    if time:
      signal.alarm(int(math.ceil(time/10.0)))  # Set timer

    # If no explicit block-size given, use inteligent software to find one
    if not block_size:
      block_size = Block_Finder.block_finder(m)

    if time:
      signal.alarm(0)  # Turn off timer
  except AlarmException: # Catch Timer (unexcepted)
    block_size = 1
    
  # Do not create a 1-Block Macro-Machine (just use base machine)
  if block_size != 1:
    m = Turing_Machine.Block_Macro_Machine(m, block_size)
  if back:
    m = Turing_Machine.Backsymbol_Macro_Machine(m)

  ## Set up the simulator
  #global sim # Useful for Debugging
  sim = Chain_Simulator.Simulator()
  sim.init(m, rec)
  if not prover:
    sim.proof = None

  try:
    if time:
      signal.alarm(time)  # Set timer

    ## Run the simulator
    sim.seek(steps)

    if time:
      signal.alarm(0)  # Turn off timer
  except AlarmException: # Catch Timer
    return TIMEOUT, (time, sim.step_num)

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

def memoize(func, max_size=10000):
  """Returns the memoized version of a non-recursive function "func".
     Saves up to "max_size" inputs before wiping memory."""
  memory = {}
  def func_memo(*args):
    if args not in memory:
      # If we don't remember it, learn it.
      if len(memory) >= max_size:
        # Dump memory first if it's getting to big.
        memory.clear()
      memory[args] = func(*args)
    return memory[args]
# Memoized version of run ... won't work yet because lists are not hashable.
run_memo = memoize(run)

# Main script
if __name__ == "__main__":
  # Backsymbol (default on)
  if "-b" in sys.argv:
    sys.argv.remove("-b")
    back = False
  else:
    back = True

  # Prover (default on)
  if "-p" in sys.argv:
    sys.argv.remove("-p")
    prover = False
  else:
    prover = True

  # Recursive Prover (default off)
  if "-r" in sys.argv:
    sys.argv.remove("-r")
    recursive = True
  else:
    recursive = False

  if len(sys.argv) >= 3:
    line = int(sys.argv[2])
  else:
    line = 1

  ttable = IO.load_TTable_filename(sys.argv[1], line)

  if len(sys.argv) >= 4:
    block_size = int(sys.argv[3])
  else:
    block_size = None

  if len(sys.argv) >= 5:
    steps = int(sys.argv[4])
    if steps == 0:
      steps = INF
  else:
    steps = INF

  if len(sys.argv) >= 6:
    time = int(sys.argv[5])
  else:
    time = 15

  print run(ttable, steps, time, block_size, back, prover, recursive)
