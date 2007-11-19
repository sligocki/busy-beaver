#! /usr/bin/env python

import sys
from Macro import Turing_Machine, Chain_Simulator, Block_Finder
import IO

def run(TTable, block_size=None, back=True, prover=True, rec=False, verbose=True):
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
  extent = 1
  #raw_input("Ready?")
  try:
    while sim.op_state == Turing_Machine.RUNNING:
      if verbose: sim.print_self()
      sim.seek(extent)
      extent *= 10
  finally:
    sim.print_self()

  if sim.op_state == Turing_Machine.HALT:
    print
    print "Turing Machine Halted!"
    print "Steps:   ", sim.step_num
    print "Nonzeros:", sim.get_nonzeros()
  elif sim.op_state == Turing_Machine.INF_REPEAT:
    print
    print "Turing Machine proven Infinite!"
    print "Reason:", sim.inf_reason
  elif sim.op_state == Turing_Machine.UNDEFINED:
    print
    print "Turing Machine reached Undefined transition!"
    print "State: ", sim.op_details[0][1]
    print "Symbol:", sim.op_details[0][0]
    print "Steps:   ", sim.step_num
    print "Nonzeros:", sim.get_nonzeros()

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

# Verbose Prover (default off)
if "-vp" in sys.argv:
  sys.argv.remove("-vp")
  Chain_Simulator.Chain_Proof_System.DEBUG = True
else:
  Chain_Simulator.Chain_Proof_System.DEBUG = False

# Verbose Simulator (default off)
if "-vs" in sys.argv:
  sys.argv.remove("-vs")
  Chain_Simulator.DEBUG = True
  verbose = False
else:
  Chain_Simulator.DEBUG = False
  verbose = True

# Brief Simulator output (default off)
if "-br" in sys.argv:
  sys.argv.remove("-br")
  Chain_Simulator.DEBUG = False
  verbose = False

if len(sys.argv) >= 3:
  line = int(sys.argv[2])
else:
  line = 1

ttable = IO.load_TTable_filename(sys.argv[1], line)

if len(sys.argv) >= 4:
  block_size = int(sys.argv[3])
else:
  block_size = None

run(ttable, block_size, back, prover, recursive, verbose)

