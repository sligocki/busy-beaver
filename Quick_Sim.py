#! /usr/bin/env python

import sys
from Macro import Turing_Machine, Chain_Simulator
import IO

def run(TTable, block_size):
  global sim
  # Construct Machine (Backsymbol-k-Block-Macro-Machine)
  m1 = Turing_Machine.Simple_Machine(TTable)
  m2 = Turing_Machine.Block_Macro_Machine(m1, block_size)
  m3 = Turing_Machine.Backsymbol_Macro_Machine(m2)
  #m4 = Turing_Machine.Block_Macro_Machine(m3, block_size)
  #m5 = Turing_Machine.Backsymbol_Macro_Machine(m4)

  sim = Chain_Simulator.Simulator()
  sim.init(m3)
  extent = 1
  try:
    while sim.op_state is Turing_Machine.RUNNING:
      sim.print_self()
      sim.seek(extent)
      extent *= 10
  finally:
    sim.print_self()

k = int(sys.argv[1])
t = IO.load_TTable_filename(sys.argv[2])
run(t, k)
