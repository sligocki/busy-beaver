#! /usr/bin/env python

import sys, math, copy

import signal, signalPlus

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
  pass

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
    tape[d] = [block.symbol for block in sim.tape.tape[d] if block.num != "Inf"]
  config = GenContainer(state=sim.state, dir=sim.dir, tape=tape)
  return config

def run(TTable, steps=INF, runtime=None, block_size=None, back=True, prover=True, rec=False, cutoff=200):
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
          block_size = Block_Finder.block_finder(m)

        signalPlus.alarm(0)  # Turn off timer

      except AlarmException: # Catch Timer (unexcepted)
        signalPlus.alarm(0)  # Turn off timer
        block_size = 1
        
      signalPlus.alarm(0)  # Turn off timer

      # Do not create a 1-Block Macro-Machine (just use base machine)
      if block_size != 1:
        m = Turing_Machine.Block_Macro_Machine(m, block_size)
      if back:
        m = Turing_Machine.Backsymbol_Macro_Machine(m)

      CTL_config = setup_CTL(m, cutoff)

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

      signalPlus.alarm(0)  # Turn off timer

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

  signalPlus.alarm(0)  # Turn off timer
  return TIMEOUT, (runtime, -1)

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
    runtime = int(sys.argv[5])
  else:
    runtime = 15

  print run(ttable, steps, runtime, block_size, back, prover, recursive)
