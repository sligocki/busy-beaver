#! /usr/bin/env python
#
# This is a Busy Beaver machine generator
#

from BB_Machine import BB_Machine
import copy
import cPickle as pickle

# global machine number
gMachine_num = 0
# Global variables for text and data output.
gTextFile = None
gTextFilename = None
gDataFile = None
gDataFilename = None

def BB_Prover(num_states, num_symbols, tape_lenth, max_steps):
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
  BB_Prover_Recursive(machine, num_states, num_symbols, tape_lenth, max_steps)

def BB_Prover_Recursive(machine, num_states, num_symbols, tape_length, max_steps):
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
    BB_save_machine(machine_new, newResults, tape_length, max_steps)

    # All other states
    if machine.num_empty_cells > 1:
      for state_out in range(max_state + 1):
        for symbol_out in range(max_symbol + 1):
          for direction_out in range(2):
            machine_new = copy.deepcopy(machine)
            machine_new.AddCell(state_in , symbol_in ,
                                state_out, symbol_out, direction_out)
            BB_Prover_Recursive(machine_new, num_states, num_symbols,
                                tape_length, max_steps)
    return

  # -1) Error
  elif exit_condition == -1:
    error_number = results[1]
    message = results[2]
    sys.stderr.write("Error %d: %s\n" % (error_number,message))

    BB_save_machine(machine, results, tape_length, max_steps)
    return

  # All other returns
  else:
    BB_save_machine(machine, results, tape_length, max_steps)
    return

def BB_run(TTable, num_states, num_symbols, tape_length, max_steps):
  """
  Wrapper for C machine running code.
  """
  import busyBeaverC
  return busyBeaverC.run(TTable, num_states, num_symbols, tape_length, float(max_steps))

def BB_save_machine(machine, results, tape_length, max_steps):
  """
  Saves a busy beaver machine with the provided data information.
  """
  # Original Kludgey output.
  """
  print "Transition Table:"
  for state in machine.getTTable():
    print state
  print "Exited with condition:", exit_condition
  print "Number of steps:", steps_run_for,
  print "Number of non-zero symbols written:", symbols_written
  print
  """

  global gTextFile, gTextFilename, gDataFile, gDataFilename, gMachine_num

  # if first call.
  if not gTextFile:
    if gTextFilename and gTextFilename != "-":
      gTextFile = file(gTextFilename, "w")
    else:
      import sys
      gTextFile = sys.stdout
  if not gDataFile:
    if gDataFilename:
      gDataFile = file(gDataFilename, "wb")

  gTextFile.write("%d " % gMachine_num)
  gTextFile.write("%d " % machine.num_states)
  gTextFile.write("%d " % machine.num_symbols)
  gTextFile.write("%d " % tape_length)
  gTextFile.write("%d " % max_steps)
  for item in results:
    gTextFile.write("%s " % item)
  gTextFile.write("%s " % machine.getTTable())
  gTextFile.write("\n")
  gTextFile.flush()

  if gDataFile:
    pickle.dump((gMachine_num,
                 machine.num_states,
                 machine.num_symbols,
                 tape_length,
                 max_steps,
                 results,
                 machine),
                gDataFile)

  gMachine_num += 1

# Default test code
if __name__ == "__main__":
  import getopt, sys
  usage = "BB_Prover.py [--help] [--states=] [--symbols=] [--tape=] [--steps=] [--textfile=] [--datafile=]"
  try:
    opts, args = getopt.getopt(sys.argv[1:], "",
                               ["help",
                                "states=",
                                "symbols=",
                                "tape=",
                                "steps=",
                                "textfile=",
                                "datafile="])
  except getopt.GetoptError:
    print usage
    sys.exit(1)

  states = 2
  symbols = 2
  tape_length = 20003
  max_steps = 10000
  gTextFilename = None
  isData = None
  gDataFilename = None

  for opt, arg in opts:
    if opt == "--help":
      print usage
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
        gTextFilename = arg
    elif opt == "--datafile":
      isData = not None
      if arg:
        gDataFilename = arg

  # The furthest that the machine can travel in n steps is n away from the
  # origin.  It could travel in eighter direction so the tape need not be longer
  # than 2 * max_steps
  tape_length = min(tape_length, 2 * max_steps + 3)

  if not gTextFilename:
    gTextFilename = "BBP_%d_%d_%d_%d.txt" % \
                    (states, symbols, tape_length, max_steps)

  if isData and not gDataFilename:
    gDataFilename = "BBP_%d_%d_%d_%d.data" % \
                    (states, symbols, tape_length, max_steps)

  BB_Prover(states, symbols, tape_length, max_steps)
