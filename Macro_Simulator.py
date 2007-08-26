#! /usr/bin/env python

import sys, signal
from Macro import Turing_Machine, Chain_Simulator, Block_Finder
import IO

from Macro.Chain_Tape import INF

def signal2exception(exc):
  """Creates a custom signal handler that immediately raises a chosen exception"""
  def catchException(*args):
    raise exc, args
  return catchException
class AlarmException(Exception):
  """An exception to be tied to a timer running out."""
  pass
# Attach the alarm signal to the alarm exception.
signal.signal(signal.SIGALRM, signal2exception(AlarmException)

def run(TTable, steps=INF, time=None, block_size=None, back=True, prover=True, rec=False):
  # Construct Machine (Backsymbol-k-Block-Macro-Machine)
  m = Turing_Machine.Simple_Machine(TTable)
  # If no explicit block-size given, use inteligent software to find one
  if not block_size:
    Block_Finder.DEBUG = True
    block_size = Block_Finder.block_finder(m)
  # Do not create a 1-Block Macro-Machine (just use base machine)
  if block_size != 1:
    m = Turing_Machine.Block_Macro_Machine(m, block_size)
  if back:
    m = Turing_Machine.Backsymbol_Macro_Machine(m)

  global sim
  sim = Chain_Simulator.Simulator()
  sim.init(m, rec)
  if not prover:
    sim.proof = None
  
  if time:
    # Set timer
    signal.alarm(time)
    try:
      sim.seek(steps)
    except AlarmException:
      return TIMEOUT, (time, sim.step_num)
    signal.alarm(0) # Turn off timer
  else:
    sim.seek(steps)

  if sim.op_state == Turing_Machine.RUNNING:
    return OVERSTEPS, (sim.step_num,)
  elif sim.op_state == Turing_Machine.HALT:
    return HALT, (sim.step_num, sim.get_nonzeros())
  elif sim.op_state == Turing_Machine.INF_REPEAT:
    return INFINITE, (sim.inf_reason,)
  elif sim.op_state == Turing_Machine.UNDEFINED:
    return UNDEFINED, (sim.op_details[0][1], sim.op_details[0][0], sim.step_num, sim.get_nonzeros())

# Main script
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

run(ttable, steps, time, block_size, back, prover, recursive)
