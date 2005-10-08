#! /usr/bin/env python
#
# This is continues past runs of Busy Beaver machines
#

import copy

from BB_Machine import BB_Machine
from BB_IO import BB_IO

# global machine number
gMachine_num = 0

def BB_Continue(num_states, num_symbols, tape_lenth, max_steps, io):
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
  nextLine = io.readResult()

  while nextLine:
    num_states  = int(nextLine[1])
    num_symbols = int(nextLine[2])

    results = nextLine[5]

    machine = BB_Machine(num_states, num_symbols)
    machine.setTTable(nextLine[6])

    if (results[0] == 0):
      save_it = not None
      BB_save_machine(machine, results, tape_length, max_steps, io, save_it)
    else:
      BB_Continue_Recursive(machine, num_states, num_symbols,
                            tape_lenth, max_steps, io)

    nextLine = io.readResult()

def BB_Continue_Recursive(machine, num_states, num_symbols,
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
  results = BB_run(machine.getTTable(),
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
    max_state = machine.getNumStatesAvailable()
    max_symbol = machine.getNumSymbolsAvailable()

    # Halt state
    #   1) Add the halt state
    #   3) This machine will write one more non-zero symbol
    #   2) This machine will take one more step and halt
    #   4) Save this machine
    machine_new = copy.deepcopy(machine)
    machine_new.AddCell(state_in , symbol_in ,
                        -1, 1, 1)

    if results[3] == 0:
      newNumSyms  = results[4] + 1
    else:
      newNumSyms  = results[4]

    newNumSteps = results[5] + 1

    newResults = (0,newNumSyms,newNumSteps)
    save_it = not None

    BB_save_machine(machine_new, newResults, tape_length, max_steps, io,
                    save_it)

    # All other states
    if machine.num_empty_cells > 1:
      for state_out in range(max_state + 1):
        for symbol_out in range(max_symbol + 1):
          for direction_out in range(2):
            machine_new = copy.deepcopy(machine)
            machine_new.AddCell(state_in , symbol_in ,
                                state_out, symbol_out, direction_out)
            BB_Continue_Recursive(machine_new, num_states, num_symbols,
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
  import busyBeaverC
  return busyBeaverC.run(TTable, num_states, num_symbols, tape_length, float(max_steps))

def BB_save_machine(machine, results, tape_length, max_steps, io, save_it):
  """
  Saves a busy beaver machine with the provided data information.
  """
  global gMachine_num

  if save_it:
    io.writeResult(gMachine_num, tape_length, max_steps, results, machine);

  gMachine_num += 1

# Default test code
if __name__ == "__main__":
  import getopt, sys

  usage = "BB_Continue.py [--help] [--states=] [--symbols=] [--tape=] [--steps=] [--textfile=] [--datafile=] [--infile=]"
  try:
    opts, args = getopt.getopt(sys.argv[1:], "", [
                                                  "help",
                                                  "states=",
                                                  "symbols=",
                                                  "tape=",
                                                  "steps=",
                                                  "textfile=",
                                                  "datafile=",
                                                  "infile="
                                                 ])
  except getopt.GetoptError:
    sys.stderr.write("%s\n" % usage)
    sys.exit(1)

  # variables for text and data output.
  textFilename = None
  textFile = None

  isData = None
  dataFilename = None
  dataFile = None

  inFilename = None
  inFile = None

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
        textFilename = arg
    elif opt == "--datafile":
      isData = not None
      if arg:
        dataFilename = arg
    elif opt == "--infile":
      if arg:
        inFilename = arg

  # The furthest that the machine can travel in n steps is n away from the
  # origin.  It could travel in either direction so the tape need not be longer
  # than 2 * max_steps + 3
  tape_length = int(min(tape_length, 2 * max_steps + 3))

  if inFilename and inFilename != "-":
    inFile = file(inFilename, "r")
  else:
    inFile = sys.stdin

  if not textFilename:
    textFilename = "BBP_%d_%d_%d_%.0f.txt" % \
                    (states, symbols, tape_length, max_steps)

  if textFilename and textFilename != "-":
    textFile = file(textFilename, "w")
  else:
    textFile = sys.stdout

  if isData and not dataFilename:
    dataFilename = "BBP_%d_%d_%d_%.0f.data" % \
                    (states, symbols, tape_length, max_steps)

  if dataFilename:
    dataFile = file(dataFilename, "wb")

  io = BB_IO(inFile, textFile, dataFile)

  BB_Continue(states, symbols, tape_length, max_steps, io)
