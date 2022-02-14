#!/usr/bin/env python

import time

import IO
from Macro import Turing_Machine


# Simple repeating machine.
ttable = IO.parse_ttable("0RA 1LA")
tm = Turing_Machine.make_machine(ttable)
for block_size in range(2, 21):
  macro_machine = Turing_Machine.Block_Macro_Machine(tm, block_size)
  macro_symbol = Turing_Machine.Block_Symbol((0, 1) + (0,) * (block_size - 2))

  print("Starting", block_size)
  start_time = time.time()
  trans = macro_machine.get_trans_object(macro_symbol,
                                         macro_machine.init_state,
                                         Turing_Machine.RIGHT)
  end_time = time.time()
  print("Finished", block_size, end_time - start_time)

  assert trans.condition in (Turing_Machine.INF_REPEAT,), trans.__dict__

print("Success")
