#! /usr/bin/env python

import sys
from Macro import Turing_Machine, Chain_Simulator, Block_Finder
import IO

def run(TTable, block_size=None, back=True):
  # Construct Machine (Backsymbol-k-Block-Macro-Machine)
  m1 = Turing_Machine.Simple_Machine(TTable)
  # If no explicit block-size given, use inteligent software to find one
  if not block_size:
    Block_Finder.DEBUG = True
    block_size = Block_Finder.block_finder(m1)
  # Do not create a 1-Block Macro-Machine (just use base machine)
  if block_size == 1:
    m2 = m1
  else:
    m2 = Turing_Machine.Block_Macro_Machine(m1, block_size)
  m3 = Turing_Machine.Backsymbol_Macro_Machine(m2)
  #m4 = Turing_Machine.Block_Macro_Machine(m3, block_size)
  #m5 = Turing_Machine.Backsymbol_Macro_Machine(m4)

  global sim
  sim = Chain_Simulator.Simulator()
  if back:
    sim.init(m3)
  else:
    sim.init(m2)
  extent = 1
  try:
    while sim.op_state is Turing_Machine.RUNNING:
      sim.print_self()
      sim.seek(extent)
      extent *= 10
  finally:
    sim.print_self()

  if sim.op_state is Turing_Machine.HALT:
    print
    print "Turing Machine Halted!"
    print "Steps:   ", sim.step_num
    print "Nonzeros:", sim.get_nonzeros()
  elif sim.op_state is Turing_Machine.INF_REPEAT:
    print
    print "Turing Machine proven Infinite!"
    print "Reason:", sim.inf_reason
  elif sim.op_state is Turing_Machine.UNDEFINED:
    print
    print "Turing Machine reached Undefined transition!"
    print "State: ", sim.state
    print "Symbol:", sim.tape.get_top_symbol()
    print "Steps:   ", sim.step_num
    print "Nonzeros:", sim.get_nonzeros()

# Main script
if "-b" in sys.argv:
  sys.argv.remove("-b")
  back = False
else:
  back = True

if len(sys.argv) >= 3:
  line = int(sys.argv[2])
else:
  line = 1

ttable = IO.load_TTable_filename(sys.argv[1], line)

if len(sys.argv) >= 4:
  block_size = int(sys.argv[3])
else:
  block_size = None

run(ttable, block_size, back)
