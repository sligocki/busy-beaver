#! /usr/bin/env python
#
# Dual_Machine_Filter.py
#
# This runs Turing machines that did not halt at two different speeds and
# detects whether they match exactly (i.e. detects repeating).
#

from Turing_Machine import Turing_Machine, Turing_Machine_Runtime_Error, \
                           Filter_Unexpected_Return
from IO import IO

def Dual_Machine_Run(num_states, num_symbols, tape_lenth, max_steps, next, io):
  """
  Stats all distinct BB machines with num_states and num_symbols.

  Runs through all distinct busy beaver machines with num_states and
  num_symbols until they:
   -1) Generate an internal error
    0) Halt
    1) Exceed tape_length
    2) Exceed max_steps
    4) Are in a detected infinite loop

  It then categorizes all distict machines as one of these above 3 along with
  important information such as:
    0) Number of non-zero symbols written
    1) Number of steps run for
  """
  while next:
    machine_num = next[0]

    num_states  = next[1]
    num_symbols = next[2]

    results = next[5]

    machine = Turing_Machine(num_states, num_symbols)
    machine.set_TTable(next[6])

    # If this machine has not been shown to halt or proven infinite.
    if (results[0] != 0 and results[0] != 4):
      Dual_Machine_Recursive(machine_num, machine, num_states, num_symbols,
                             tape_lenth, max_steps, results, io)

    next = io.read_result()

def Dual_Machine_Recursive(machine_num, machine, num_states, num_symbols,
                           tape_length, max_steps, old_results, io):
  """
  Stats this BB machine.

  Runs this machine until it:
   -1) Generates an internal error
    0) Halts
    1) Exceeds tape_length
    2) Exceeds max_steps
    3) Reaches an undefined cell of the transition table
    4) Is in a detected infinite loop

  If it reaches an undefined cell it recursively calls this function with
  each of the possible entrees to that cell so that it can find ever distinct
  machine which comes from the input machine

  Otherwise it saves the input machine with the reason that it ended and
  important information such as:
    0) Number of non-zero symbols written
    1) Number of steps run for
  """
  results = run(machine.get_TTable(), num_states, num_symbols,
                tape_length, max_steps)

  exit_condition = results[0]

  #   -1) Error
  if exit_condition == -1:
    error_number = results[1]
    message      = results[2]
    sys.stderr.write("Error %d: %s\n" % (error_number, message))
    save_machine(machine_num, machine, results, tape_length, max_steps, io,
                 old_results)
    raise Turing_Machine_Runtime_Error, "Error encountered while running a turing machine"

  #    3) Reached Undefined Cell
  # Should not occur because Filters should only be run on Generate.py results.
  elif exit_condition == 3:
    sys.stderr.write("Machine (%d) reached undefined cell: %s" %
                     (machine_num, result))
    save_machine(machine_num, machine, results, tape_length, max_steps, io,
                 old_results)
    raise Filter_Unexpected_Return, "Machine reached undefined cell in filter."

  # All other returns:
  #    0) Halt
  #    1) Exceed tape_length
  #    2) Exceed max_steps
  #    4) Are in a detected infinite loop
  else:
    # If classified (Halt or Infinite)
    if (results[0] == 0 or results[0] == 4):
      save_machine(machine_num, machine, results, tape_length, max_steps, io,
                   old_results)
    # If still unclassified
    else:
      save_machine(machine_num, machine, old_results, tape_length, max_steps,
                   io)

  return

def run(TTable, num_states, num_symbols, tape_length, max_steps):
  """
  Wrapper for C machine running code.
  """
  import Dual_Machine
  return Dual_Machine.run(TTable, num_states, num_symbols,
                          tape_length, max_steps)

def save_machine(machine_num, machine, results, tape_length, max_steps,
                 io, old_results = []):
  """
  Saves a busy beaver machine with the provided data information.
  """
  io.write_result(machine_num, tape_length, max_steps, results, machine,
                  old_results);

# Default test code
if __name__ == "__main__":
  import sys
  from Option_Parser import Filter_Option_Parser

  # Get command line options.
  opts, args = Filter_Option_Parser(sys.argv, [])

  io = IO(opts["infile"], opts["outfile"], opts["log_number"])
  next = io.read_result()

  Dual_Machine_Run(opts["states"], opts["symbols"], opts["tape"],
                   opts["steps"], next, io)
