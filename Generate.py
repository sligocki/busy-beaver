#! /usr/bin/env python
#
# Generate.py
#
# This is a Busy Beaver Turing machine generator.  It enumerates a 
# representative set of all Busy Beavers for given # of states and symbols.
#

import copy

from Turing_Machine import Turing_Machine
from IO import IO

# global machine number
g_machine_num = 0
g_next = None

class Turing_Machine_Runtime_Error:
  """
  This exception class is raised if an error occurs while running/simulating a
  turing machine (currently done in c-code).
  """

  def __init__(self, value=None):
    self.value = value

  def __repr__(self):
    return `self.value`

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
  global g_machine_num, g_next

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
    # Info for interpolating what would happen if undefined state was halt.
    # They are returned as floats, so we convert them to ints.
    num_symb_written = int(round(results[4]))
    num_steps_taken = int(round(results[5]))

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
  # We must convert max_steps to float because it could be larger than a C int
  # max(int) == 2,147,483,647
  import Turing_Machine_Sim
  return Turing_Machine_Sim.run(TTable, num_states, num_symbols,
                                tape_length, float(max_steps))


def save_machine(machine, results, tape_length, max_steps, io, save_it):
  """
  Saves a busy beaver machine with the provided data information.
  """
  global g_machine_num

  if save_it:
    io.write_result(g_machine_num, tape_length, max_steps, results, machine);

  g_machine_num += 1

# Command line interpretter code
if __name__ == "__main__":
  import os, sys, getopt

  usage = "Generate.py --states= --symbols= [--help] [--tape=] [--steps=] [--outfile=] [--restart=]"
  try:
    opts, args = getopt.getopt(sys.argv[1:], "", [
                                                  "help",
                                                  "states=",
                                                  "symbols=",
                                                  "tape=",
                                                  "steps=",
                                                  "outfile=",
                                                  "restart=",
                                                  "infile="   # infile is never used but is automatically passed by Tools/update script so it must be accepted.
                                                 ])
  except getopt.GetoptError:
    sys.stderr.write("%s\n" % usage)
    sys.exit(1)

  out_filename = None
  out_file = None

  is_restart = None
  restart_filename = None
  restart_file = None

  # 'states' and 'symbols' are required variables so they have no default.
  states = None
  symbols = None
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
      max_steps = int(arg)
    elif opt == "--outfile":
      if arg:
        out_filename = arg
    elif opt == "--restart":
      is_restart = True
      if arg:
        restart_filename = arg

  if is_restart:
    # If restart input not from stdin.
    if restart_filename and restart_filename != "-":
      restart_file = file(restart_filename, "r")
    else:
      restart_file = sys.stdin

    temp_input = IO(restart_file, None)
    g_next = temp_input.read_result()
    del temp_input

    states  = g_next[1]
    symbols = g_next[2]

    tape_length = g_next[3]
    max_steps   = g_next[4]

  # The furthest that the machine can travel in n steps is n+1 away from the
  # origin.  It could travel in either direction so the tape need not be longer
  # than 2 * max_steps + 3
  tape_length = int(min(tape_length, 2 * max_steps + 3))

  if not states or not symbols:
    sys.stderr.write(usage)
    sys.exit(1)

  # Default output filename.  (E.g. 2.2.20003.10000.out)
  if not out_filename:
    out_filename = "%d.%d.%d.%d.out" % \
                    (states, symbols, tape_length, max_steps)

  # If not outputing to stdout.
  if out_filename != "-":
    if os.path.exists(out_filename):
      sys.stderr.write("Output text file, '%s', exists\n" % (out_filename,));
      sys.exit(1)
    else:
      out_file = file(out_filename, "w")
  else:
    out_file = sys.stdout

  # If not restarting 'restart_file' == None, so no input will be created
  io = IO(restart_file, out_file)

  Generate(states, symbols, tape_length, max_steps, io)
