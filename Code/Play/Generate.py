#! /usr/bin/env python
#
# Generate.py
#
"""
This is a Busy Beaver Turing machine generator.  It enumerates a 
representative set of all Busy Beavers for given # of states and symbols.
"""

import copy

from Turing_Machine import Turing_Machine, Turing_Machine_Runtime_Error
from IO import IO

# global machine number
g_machine_num = 0

def Generate(num_states, num_symbols, tape_length, max_steps, io):
  """
  Stats all distinct BB machines with num_states and num_symbols.

  Runs through all distinct busy beaver machines with num_states and
  num_symbols until they:
   -1) Generate an internal error
    0) Halt
    1) Exceed tape_length
    2) Exceed max_steps

  It then categorizes all distict machines as one of these above 3 along with
  important information such as:
    0) Number of non-zero symbols written
    1) Number of steps run for
  """
  machine = Turing_Machine(num_states, num_symbols)
  Generate_Recursive(machine, num_states, num_symbols,
                     tape_length, max_steps, io)

def Generate_Recursive(machine, num_states, num_symbols,
                       tape_length, max_steps, io):
  """
  Stats this BB machine.

  Runs this machine until it:
   -1) Generates an internal error
    0) Halts
    1) Exceeds tape_length
    2) Exceeds max_steps
    3) Reaches an undefined cell of the transition table

  If it reaches an undefined cell it recursively calls this function with
  each of the possible entrees to that cell so that it can find every distinct
  machine which comes from the input machine
  """

  # results = (exit_condition, )
  #  error) (-1, error#, error_string)
  #  halt)  (0, #sym, #steps)
  #  tape)  (1, #sym, #steps)
  #  steps) (2, #sym, #steps)
  #  undef) (3, cur_state, cur_sym, #sym, #stpes)
  #  inf)   (4, inf#, ..., inf_message)
  results = run(machine.get_TTable(), num_states, num_symbols,
                tape_length, max_steps)

  exit_condition = results[0]

  # 3) Reached Undefined Cell
  if exit_condition == 3:
    # Position of undefined cell in transition table
    state_in  = results[1]
    symbol_in = results[2]
    num_symb_written = results[3]
    num_steps_taken = results[4]

    # If undefined cell is Halt.
    #   1) Add the halt state
    machine_new = copy.deepcopy(machine)
    machine_new.add_cell(state_in , symbol_in ,
                        -1, 1, 1)

    #   2) This machine will write one more non-zero symbol if current symbol
    # is not non-zero (I.e. is zero)
    if symbol_in == 0:
      num_symb_written += 1

    #   3) This machine will take one more step to halt state
    num_steps_taken += 1

    new_results = (0, num_symb_written, num_steps_taken)

    #   4) Save this machine
    save_machine(machine_new, new_results, tape_length, max_steps, io)

    # 'max_state' and 'max_symbol' are the state and symbol numbers for the
    # smallest state/symbol not yet written (i.e. available to add to TTable).
    max_state = machine.get_num_states_available()
    max_symbol = machine.get_num_symbols_available()

    # If undefined cell is not Halt
    # If this is the last undefined cell, then it must be a halt, so only try
    # other values for cell if this is not the last undefined cell.
    if machine.num_empty_cells > 1:
      # 'state_out' in [0, 1, ... max_state] == range(max_state + 1)
      for state_out in range(max_state + 1):
        for symbol_out in range(max_symbol + 1):
          for direction_out in range(4):
            machine_new = copy.deepcopy(machine)
            # 'state_in' and 'symbol_in' specify cell in transition table.
            # 'state_out', 'symbol_out', and 'direction_out' specify value to
            # put in that cell.
            machine_new.add_cell(state_in , symbol_in ,
                                 state_out, symbol_out, direction_out)
            Generate_Recursive(machine_new, num_states, num_symbols,
                               tape_length, max_steps, io)
  # -1) Error
  elif exit_condition == -1:
    error_number = results[1]
    message = results[2]
    sys.stderr.write("Error %d: %s\n" % (error_number, message))
    save_machine(machine, results, tape_length, max_steps, io)
    raise Turing_Machine_Runtime_Error, "Error encountered while running a turing machine"
  # All other returns
  else:
    save_machine(machine, results, tape_length, max_steps, io)

  return

def run(TTable, num_states, num_symbols, tape_length, max_steps):
  """
  Wrapper for C machine running code.
  """
  from Turing_Machine_Sim import Turing_Machine_Sim
  return Turing_Machine_Sim(TTable, num_states, num_symbols,
                            tape_length, max_steps)


def save_machine(machine, results, tape_length, max_steps, io):
  """
  Saves a busy beaver machine with the provided information.
  """
  global g_machine_num
  io.write_result(g_machine_num, tape_length, max_steps, results, machine)
  g_machine_num += 1

# Command line interpretter code
if __name__ == "__main__":
  import sys
  from Option_Parser import Generator_Option_Parser

  # Get command line options.
  # Generate.py may be sent an infile param but it should be ignored
  opts, args = Generator_Option_Parser(sys.argv, [], ignore_infile = True)

  io = IO(None, opts["outfile"], opts["log_number"])

  Generate(opts["states"], opts["symbols"], opts["tape"], opts["steps"], io)
