#! /usr/bin/env python
#
# Assign_Undecideds.py
#
"""
Continues enumeration of machines which reach undefined states after being
enumerated (say during a simulation filter).
"""

import copy
import sys

from Common import Exit_Condition, HALT_TRANS
import IO
from Option_Parser import Filter_Option_Parser

# Get command line options.
opts, args = Filter_Option_Parser(sys.argv,
                  [("next_machine_num", int, None, True, True)])

new_M_num = opts["next_machine_num"]
io = IO.IO(opts["infile"], opts["outfile"])
next = io.read_result()

while next:
  (machine_num, num_states, num_symbols, tape_length, max_steps,
   results, ttable, log_num, old_results) = next

  cond, on_state, on_symbol, score, steps = results[0:5]

  on_state  = int(on_state)
  on_symbol = int(on_symbol);
  score     = int(score);
  steps     = int(steps)

  # Write the halting machine.
  new_results = (Exit_Condition.HALT, score, steps)
  new_ttable = copy.deepcopy(ttable)
  new_ttable[on_state][on_symbol] = HALT_TRANS

  io.write_result_raw(machine_num, num_states, num_symbols,
                      tape_length, max_steps, new_results,
                      new_ttable, log_num, old_results)

  # Get stats.  Number of undefined transitions, whether there is a halt,
  # and the max symbol/states.
  undefs = 0
  max_symbol = max_state = -1
  for row in new_ttable:
    for symbol, dir, state in row:
      if symbol == -1:
        undefs += 1
      else:
        max_symbol = max(max_symbol, symbol)
        max_state = max(max_state, state)

  # If there are other undefined transitions, then define non-halting versions.
  if undefs != 0:
    for symbol in range(min(max_symbol + 2, num_symbols)):
      for dir in range(2):
        for state in range(min(max_state + 2, num_states)):
          new_ttable[on_state][on_symbol] = (symbol, dir, state)
          io.write_result_raw(new_M_num, num_states, num_symbols, tape_length,
                              max_steps, old_results, new_ttable, log_num)
          new_M_num += 1

  # Get next machine.
  next = io.read_result()
