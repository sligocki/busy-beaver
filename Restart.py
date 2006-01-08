#! /usr/bin/env python
#
# Restart.py
#
# Continues earlier incomplete runs of Generate.py.  Takes output from
# Generate.py as input.
#

import copy

from Turing_Machine import Turing_Machine, Turing_Machine_Runtime_Error
from IO import IO

# global machine number
g_machine_num = 0
g_next = None

def Generate(num_states, num_symbols, tape_length, max_steps, io):
  machine = Turing_Machine(num_states, num_symbols)
  Generate_Recursive(machine, num_states, num_symbols,
                     tape_length, max_steps, io)

def Generate_Recursive(machine, num_states, num_symbols,
                       tape_length, max_steps, io):
  global g_machine_num

  if g_next and machine.get_TTable() == g_next[6]:
    results = g_next[5]
    save_it = False

    g_next = io.read_result()
  else:
    # results = (exit_condition, )
    #  error) (-1, error#, error_string)
    #  halt)  (0, #sym, #steps)
    #  tape)  (1, #sym, #steps)
    #  steps) (2, #sym, #steps)
    #  undef) (3, cur_state, cur_sym, #sym, #stpes)
    results = run(machine.get_TTable(), num_states, num_symbols,
                  tape_length, max_steps)
    save_it = True

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

    if g_next and machine_new.get_TTable() == g_next[6]:
      new_results = g_next[5]
      save_it = False

      g_next = io.read_result()
    else:
      # 2) This machine will write one more non-zero symbol if current symbol
      # is not non-zero (I.e. is zero)
      if symbol_in == 0:
        num_symb_written += 1

      # 3) This machine will take one more step to halt state
      num_steps_taken += 1

      new_results = (0, num_symb_written, num_steps_taken)
      save_it = True

    #   4) Save this machine
    save_machine(machine_new, new_results, tape_length, max_steps, io,
                 save_it)

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
          for direction_out in range(2):
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
    save_machine(machine, results, tape_length, max_steps, io, save_it)
    raise Turing_Machine_Runtime_Error, "Error encountered while running a turing machine"
  # All other returns
  else:
    save_machine(machine, results, tape_length, max_steps, io, save_it)

  return

def run(TTable, num_states, num_symbols, tape_length, max_steps):
  """
  Wrapper for C machine running code.
  """
  from Turing_Machine_Sim import Turing_Machine_Sim
  return Turing_Machine_Sim(TTable, num_states, num_symbols,
                            tape_length, max_steps)

def save_machine(machine, results, tape_length, max_steps, io, save_it):
  """
  Saves a busy beaver machine with the provided information.
  """
  global g_machine_num
  if save_it:
    io.write_result(g_machine_num, tape_length, max_steps, results, machine);
  g_machine_num += 1

# Command line interpretter code
if __name__ == "__main__":
  import sys
  from Option_Parser import Filter_Option_Parser

  # Get command line options.
  opts, args = Filter_Option_Parser(sys.argv, [])

  io = IO(opts["infile"], opts["outfile"])
  next = io.read_result()

  Generate(opts["states"], opts["symbols"],
           opts["tape"], opts["steps"], next, io)
