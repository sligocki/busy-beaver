#! /usr/bin/env python
#
# Tree_Filter.py
#
# This runs Turing machines that did not halt and tries to detect "tree"
# behavior.
#

from Turing_Machine import Turing_Machine, Turing_Machine_Runtime_Error, \
                           Filter_Unexpected_Return
from IO import IO

def Tree_Filter(num_states, num_symbols, tape_lenth, max_steps, next, io):
  """Iterate through all machines in input and attempt to classify as trees."""
  while next:
    machine_num = next[0]

    num_states  = next[1]
    num_symbols = next[2]

    results = next[5]

    machine = Turing_Machine(num_states, num_symbols)
    machine.set_TTable(next[6])

    # If this machine has not been shown to halt or proven infinite.
    if (results[0] != 0 and results[0] != 4):
      Examine_Machine(machine_num, machine, num_states, num_symbols,
                      tape_lenth, max_steps, results, io)

    next = io.read_result()

def Examine_Machine(machine_num, machine, num_states, num_symbols,
                    tape_length, max_steps, old_results, io):
  """Examine specific tree and attempt to classify as tree."""
  results = run(machine, num_states, num_symbols,
                tape_length, max_steps, machine_num)

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

def run(machine, num_states, num_symbols, tape_length, max_steps, machine_num):
  """Wrapper for three step tree checking code."""
  from Tree_Identify import Tree_Identify
  from Tree_Classify import Tree_Classify
  from Tree_Prove import Tree_Prove

  print "run", machine_num
  identify = Tree_Identify(machine.get_TTable(), num_states, num_symbols, tape_length, max_steps)
  print "identify", identify
  if identify and identify[0] != -1:
    classify = Tree_Classify(machine, identify)
    print "classify", classify
    if classify:
      prove = Tree_Prove(machine, classify)
      print "prove", prove
      if prove:
        return prove
      else:
        # Tree_Prove rejected machine.
        # This means that the description passed by Tree_Classify did not work
        # for a general number of middle pieces.  If Tree_Classify is running
        # correctly this means that the machine performed like a tree for one
        # repetition, but not for all repititions, so it may halt.
        raise ValueError, "Tree_Classify returned an incorrect classification.\n%s" % repr(classify)
    else:
      # Tree_Classify rejected machine.
      # This means that the last 2 step_numbers passed by Tree_Identify were
      # not consecutive "repeats" of a tree repetition.  If Tree_Identify is
      # running correctly that means that it detected some similar patern.
      # Prob want to call Tree_Identify again to find new repeating pattern?
  elif not identify:
    # Tree_Identify rejected machine.
    # This means no tree-type patterns were discovered (but some might exist?)
    return (1,)
  else: # if identify[0] == -1:
    # Return Error.
    return identify

def save_machine(machine_num, machine, results, tape_length, max_steps,
                 io, old_results = []):
  """Saves a busy beaver machine with the provided data information."""
  io.write_result(machine_num, tape_length, max_steps, results, machine,
                  old_results = old_results);

# Default test code
if __name__ == "__main__":
  import sys
  from Option_Parser import Filter_Option_Parser

  # Get command line options.
  opts, args = Filter_Option_Parser(sys.argv, [])

  io = IO(opts["infile"], opts["outfile"], opts["log_number"])
  next = io.read_result()

  Tree_Filter(opts["states"], opts["symbols"], opts["tape"],
              opts["steps"], next, io)
