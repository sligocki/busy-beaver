#! /usr/bin/env python
#
# This is a Busy Beaver machine generator
#

import copy

from BB_Machine import BB_Machine
from BB_IO import BB_IO

# global machine number
g_machine_num = 0
g_next = None

def BB_Prover(num_states, num_symbols, tape_length, max_steps, io):
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
  machine = BB_Machine(num_states, num_symbols)
  BB_Prover_Recursive(machine, num_states, num_symbols,
                      tape_length, max_steps, io)

def BB_Prover_Recursive(machine, num_states, num_symbols,
                        tape_length, max_steps, io):
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
  global g_machine_num, g_next

  if g_next and machine.get_TTable() == g_next[6]:
    results = g_next[5]
    save_it = None

    g_next = io.read_result()
  else:
    results = BB_run(machine.get_TTable(),
                     num_states,
                     num_symbols,
                     tape_length,
                     max_steps)
    save_it = not None

  exit_condition = results[0]

  # 3) Reached Undefined Cell
  if exit_condition == 3:
    state_in  = results[1]  # Position of undefined cell
    symbol_in = results[2]
    # max_state and max_symbol different from num_states and num_symbols.
    # they are restricted to only one greater than the current largest state or
    # symbol.
    max_state = machine.get_num_states_available()
    max_symbol = machine.get_num_symbols_available()

    # Halt state
    #   1) Add the halt state
    #   3) This machine will write one more non-zero symbol
    #   2) This machine will take one more step and halt
    #   4) Save this machine
    machine_new = copy.deepcopy(machine)
    machine_new.add_cell(state_in , symbol_in ,
                        -1, 1, 1)

    if g_next and machine_new.get_TTable() == g_next[6]:
      new_results = g_next[5]
      save_it = None

      g_next = io.read_result()
    else:
      if results[3] == 0:
        new_num_syms  = results[4] + 1
      else:
        new_num_syms  = results[4]

      new_sum_steps = results[5] + 1

      new_results = (0,new_num_syms,new_num_steps)
      save_it = not None

    BB_save_machine(machine_new, new_results, tape_length, max_steps, io,
                    save_it)

    # All other states
    if machine.num_empty_cells > 1:
      for state_out in range(max_state + 1):
        for symbol_out in range(max_symbol + 1):
          for direction_out in range(2):
            machine_new = copy.deepcopy(machine)
            machine_new.add_cell(state_in , symbol_in ,
                                 state_out, symbol_out, direction_out)
            BB_Prover_Recursive(machine_new, num_states, num_symbols,
                                tape_length, max_steps, io)
  # -1) Error
  elif exit_condition == -1:
    error_number = results[1]
    message = results[2]
    sys.stderr.write("Error %d: %s\n" % (error_number,message))

    BB_save_machine(machine, results, tape_length, max_steps, io, save_it)
  # All other returns
  else:
    BB_save_machine(machine, results, tape_length, max_steps, io, save_it)

  return

def BB_run(TTable, num_states, num_symbols, tape_length, max_steps):
  """
  Wrapper for C machine running code.
  """
  import busy_beaver_C
  return busy_beaver_C.run(TTable, num_states, num_symbols,
                           tape_length, float(max_steps))

def BB_save_machine(machine, results, tape_length, max_steps, io, save_it):
  """
  Saves a busy beaver machine with the provided data information.
  """
  global g_machine_num

  if save_it:
    io.write_result(g_machine_num, tape_length, max_steps, results, machine);

  g_machine_num += 1

# Default test code
if __name__ == "__main__":
  import getopt, sys

  usage = "BB_Prover.py [--help] [--states=] [--symbols=] [--tape=] [--steps=] [--textfile=] [--datafile=] [--restart=]"
  try:
    opts, args = getopt.getopt(sys.argv[1:], "", [
                                                  "help",
                                                  "states=",
                                                  "symbols=",
                                                  "tape=",
                                                  "steps=",
                                                  "textfile=",
                                                  "datafile=",
                                                  "restart="
                                                 ])
  except getopt.GetoptError:
    sys.stderr.write("%s\n" % usage)
    sys.exit(1)

  # variables for text and data output.
  text_filename = None
  text_file = None

  is_data = None
  data_filename = None
  data_file = None

  is_restart = None
  restart_filename = None
  restart_file = None

  states = 2
  symbols = 2
  tape_length = 20003
  max_steps = 10000

  for opt, arg in opts:
    if opt == "--help":
      sys.stdout.write("%s\n" % usage)
      sys.exit(0)
    elif opt == "--states":
      states = int(arg)
    elif opt == "--symbols":
      symbols = int(arg)
    elif opt == "--tape":
      tape_length = int(arg)
    elif opt == "--steps":
      max_steps = float(arg)
    elif opt == "--textfile":
      if arg:
        text_filename = arg
    elif opt == "--datafile":
      is_data = not None
      if arg:
        data_filename = arg
    elif opt == "--restart":
      is_restart = not None
      if arg:
        restart_filename = arg

  g_next = None

  if is_restart:
    if restart_filename and restart_filename != "-":
      restart_file = file(restart_filename, "r")
    else:
      restart_file = sys.stdin

    input = BB_IO(restart_file, None, None)

    g_next = input.read_result()

    states  = g_next[1]
    symbols = g_next[2]

    tape_length = g_next[3]
    max_steps   = g_next[4]

  # The furthest that the machine can travel in n steps is n away from the
  # origin.  It could travel in either direction so the tape need not be longer
  # than 2 * max_steps + 3
  tape_length = int(min(tape_length, 2 * max_steps + 3))

  if not text_filename:
    text_filename = "BBP_%d_%d_%d_%.0f.txt" % \
                    (states, symbols, tape_length, max_steps)

  if text_filename and text_filename != "-":
    text_file = file(text_filename, "w")
  else:
    text_file = sys.stdout

  if is_data and not data_filename:
    data_filename = "BBP_%d_%d_%d_%.0f.data" % \
                    (states, symbols, tape_length, max_steps)

  if data_filename:
    data_file = file(data_filename, "wb")

  io = BB_IO(restart_file, text_file, data_file)

  BB_Prover(states, symbols, tape_length, max_steps, io)
