#! /usr/bin/env python
#
# No_Halt_Filter.py
#
"""
This detects some cases where the current transition table can
never be extended to include a halt.
"""

import sys

from Common import Exit_Condition
from Turing_Machine import Turing_Machine, Turing_Machine_Runtime_Error, \
                           Filter_Unexpected_Return
from IO import IO

def No_Halt_Run(num_states, num_symbols, tape_length, max_steps, next, io):
  while next:
    machine_num = next[0]

    num_states  = next[1]
    num_symbols = next[2]

    old_tape_length = next[3]
    old_max_steps   = next[4]

    results = next[5]

    machine = Turing_Machine(num_states, num_symbols)
    machine.set_TTable(next[6])

    if (results[0] != 0 and results[0] != 4):
      No_Halt_Recursive(machine_num,
                        machine, num_states, num_symbols,
                        tape_length, max_steps, results,
                        old_tape_length, old_max_steps, io)

    next = io.read_result()

def No_Halt_Recursive(machine_num, machine, num_states, num_symbols,
                      tape_length, max_steps, old_results,
                      old_tape_length, old_max_steps, io):
  results = run(machine.get_TTable(), num_states, num_symbols,
                tape_length, max_steps)

  exit_condition = results[0]

  #   -1) Error
  if exit_condition == Exit_Condition.ERROR:
    error_number = results[1]
    message      = results[2]
    sys.stderr.write("Error %d: %s\n" % (error_number, message))
    save_machine(machine_num, machine, results,
                 old_tape_length, old_max_steps, io, old_results)
    raise Turing_Machine_Runtime_Error("Error encountered while running a turing machine")

  #    3) Reached Undefined Cell
  # Should not occur because Filters should only be run on Generate.py results.
  elif exit_condition == Exit_Condition.UNDEF_CELL:
    sys.stderr.write("Machine (%d) reached undefined cell: %s" %
                     (machine_num, result))
    save_machine(machine_num, machine, results,
                 old_tape_length, old_max_steps, io, old_results)
    raise Filter_Unexpected_Return("Machine reached undefined cell in filter.")

  # All other returns:
  #    0) Halt
  #    4) Are in a detected infinite loop
  elif (exit_condition in (Exit_Condition.HALT, Exit_Condition.INFINITE)):
    save_machine(machine_num, machine, results,
                 old_tape_length, old_max_steps, io, old_results)
  # If still unclassified:
  #    1) Exceed tape_length
  #    2) Exceed max_steps
  else:
    save_machine(machine_num, machine, old_results,
                 old_tape_length, old_max_steps, io)

  return

def run(TTable, num_states, num_symbols, tape_length, max_steps):
  """
  Checks No_Halt condition.
  """
  symbol_written = [False] * num_symbols
  undefined_transition = [False] * num_symbols
  # Symbol 0 is there from the start
  symbol_written[0] = True

  for state in range(num_states):
    for symbol in range(num_symbols):
      new_symbol = TTable[state][symbol][0]
      # TODO(shawn): Should this be checking new_state == HALT_STATE (== -1)?
      if (new_symbol == -1):
        undefined_transition[symbol] = True
      else:
        symbol_written[new_symbol] = True

  result = (Exit_Condition.INFINITE, "No_Halt")
  for symbol in range(num_symbols):
    if (symbol_written[symbol] and undefined_transition[symbol]):
      result = (Exit_Condition.UNKNOWN, 0, 0)
      break

  return result

def save_machine(machine_num, machine, results, tape_length, max_steps,
                 io, old_results = []):
  """
  Saves a busy beaver machine with the provided data information.
  """
  io.write_result(machine_num, tape_length, max_steps, results, machine,
                  old_results = old_results)

# Default test code
if __name__ == "__main__":
  from Option_Parser import Filter_Option_Parser

  # Get command line options.
  opts, args = Filter_Option_Parser(sys.argv, [])

  io = IO(opts["infile"], opts["outfile"], opts["log_number"])
  next = io.read_result()

  No_Halt_Run(opts["states"], opts["symbols"], opts["tape"], opts["steps"],
              next, io)
