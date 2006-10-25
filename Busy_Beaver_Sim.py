#! /usr/bin/env python
#
# Busy_Beaver_Sim.py
#
# This module contains the Busy_Beaver class, which runs a Turing machine
# simulator (either in C or Python) with an initially blank tape.
#

import sys
import time

from Turing_Machine import Turing_Machine

def load(infile, num = 1, log_number = None):
  """
  Load the contents of the Turing machine from a file.
  """
  import string

  if log_number == None:
    while num > 1:
      infile.readline()
      num -= 1

    line = infile.readline()
    parts = line.split()
  else:
    line = infile.readline()
    parts = line.split()

    while line != "" and int(parts[0]) != log_number:
      line = infile.readline()
      parts = line.split()

  start_index = 0
  start_found = False
  for item in parts:
    if len(item) >= 2:
      if item[:2] == "[[":
        start_found = True
        break
    start_index += 1

  end_index = start_index+1
  end_found = False
  for item in parts[start_index+1:]:
    if len(item) >= 2:
      if item[-2:] == "]]":
        end_found = True
        end_index += 1
        break
    end_index += 1

  if start_found and end_found:
    TTable = eval(string.join(parts[start_index:end_index]))
  else:
    sys.stderr.write("Turing machine not found in input file\n")
    sys.exit(1)
  return Turing_Machine(TTable)


def load_old(file):
  """
  Load the contents of the Turing machine from a file using the old format.
  """

  machine = Turing_Machine(1,1)

  data = file.read()
  data = data.splitlines()

  nstates = len(data)
  nsymbols = 0

  for state in data:
    state = state.split()

    if nsymbols == 0:
      nsymbols = int(len(state)) / 3
      TTable = []

    for j in xrange(nsymbols):
      if state[3*j + 1] == "R":
        state[3*j + 1] = 1
      elif state[3*j + 1] == "L":
        state[3*j + 1] = 0
      else:
        sys.stderr.write("Direction not 'L' or 'R'\n")
        sys.exit(1)

    state = map(int, state)

    state_list = [None] * nsymbols
    for j in xrange(nsymbols):
      state_list[j] = tuple(state[3*j:3*j + 3])

    TTable.append(state_list)

  machine.set_TTable(TTable)

  return machine


def print_machine(machine):
  """
  Pretty-print the contents of the Turing machine.
  This method prints the state transition information
  (number to print, direction to move, next state) for each state
  but not the contents of the tape.
  """

  sys.stdout.write("Transition table:\n")

  TTable = machine.get_TTable()

  for i in xrange(len(TTable)):
    sys.stdout.write("  State %d:\n" % i)
    for j in xrange(len(TTable[i])):
      sys.stdout.write("    %d: (" % j)
      for k in TTable[i][j]:
        sys.stdout.write(" %2d" % k)
      sys.stdout.write(" )\n")
    sys.stdout.write("\n")
        
  sys.stdout.flush()


def run(machine, tape_length, num_steps, silent=False):
  """
  Start the tape and run it until it halts.
  If 'silent' is 1, don't print out anything during the run.
  """
  from Turing_Machine_Sim import Turing_Machine_Sim

  start_time = time.time()
  result = Turing_Machine_Sim(machine.get_TTable(),
                              machine.num_states,machine.num_symbols,
                              tape_length,num_steps)
  end_time = time.time()

  exit_cond = int(result[0])

  if exit_cond < 0:
    print "Error: %s" % result[2]
  elif exit_cond <= 2:
    num_syms  = int(result[1])
    num_steps = int(result[2])

    if not silent:
      if exit_cond == 0:
        print "Halted"
      else:
        print "Did not halt"
      print
      if (start_time == end_time):
        print "Steps/second: infinite, ;-)"
      else:
        print "Steps/second: ",num_steps / (end_time - start_time)
  elif exit_cond == 3:
    print "Invalid state found"
  elif exit_cond == 4:
    print "Infinite result: %s" % result[2]
  else:
    print "Unknown exit code: %d" % exit_cond

  sys.stdout.flush()

  return (num_syms, num_steps)


def run_visual(machine, tape_length, num_steps, print_width=79, silent=False):
  """
  Start the tape and run it until it halts with visual output.
  """

  start_time = time.time()

  num_syms = 0

  tape = [0] * tape_length
  middle = tape_length / 2

  position = middle

  position_start = position
  position_end   = position

  state = 0

  max_syms = 0
  total_steps = 0

  print

  TTable = machine.get_TTable()

  half_width = (print_width - 18) / 2
  if half_width < 1:
    half_width = 1

  t = 0
  nt = 1
  while t < nt:
    for i in xrange(num_steps):
      if position < 1 or position >= tape_length-1:
        print "Oops..."
        sys.stdout.flush()
        num_syms  = -1
        num_steps = -1
        return (num_syms, num_steps)

      value = tape[position]

      new_value = TTable[state][value][0]
      new_move  = TTable[state][value][1]
      new_state = TTable[state][value][2]

      if (value == 0 and new_value != 0):
        num_syms += 1

      if (value != 0 and new_value == 0):
        num_syms -= 1;

      tape[position] = new_value

      if new_move == 0:
        position -= 1
        if position < position_start:
          position_start = position
      else:
        position += 1
        if position > position_end:
          position_end = position

      if not silent:
        if position > middle - half_width - 2 and position < middle + half_width +1:
          just_on = True

          cur_step = total_steps + i

          sys.stdout.write("%10d: " % int(cur_step+1))

          for j in xrange(2*half_width):
            value = tape[middle+(j-half_width)]
            if value != 0:
              if position == middle+(j-half_width):
                sys.stdout.write("%1c" % int(value+64))
              else:
                sys.stdout.write("%1c" % int(value+96))
            else:
              if position == middle+(j-half_width):
                sys.stdout.write(":")
              else:
                sys.stdout.write(".")

          sys.stdout.write(" %2d"   % new_state)
          sys.stdout.write(" %2d\n" % tape[position])

          sys.stdout.flush()
        else:
          if just_on:
            sys.stdout.write("       ...\n")
            sys.stdout.flush()

            just_on = False

      if position < 1 or position >= tape_length-1:
        break

      state = new_state

      if state == -1:
        break

    total_steps += i

    if position < 1 or position >= tape_length-1:
      break

    if state == -1:
      break

    if num_syms > max_syms:
#      nt += num_syms - max_syms
      max_syms = num_syms

    t += 1

  if state != -1:
    num_syms  = 0
    num_steps = 0
  else:
    num_syms  = num_syms
    num_steps = total_steps + 1

  end_time = time.time()

  print
  print
  print "Steps/second: ", num_steps / (end_time - start_time)
  print
  print "Range on tape: ", position_start - middle, \
                     "to", position_end   - middle

  sys.stdout.flush()

  return (num_syms, num_steps)


if __name__ == "__main__":
  from Option_Parser import Filter_Option_Parser

  opts, args = Filter_Option_Parser(sys.argv,
                                    [("brief" , None, None, False, False),
                                     ("visual", None, None, False, False),
                                     ("width" , int , 79  , False, True ),
                                     ("old"   , None, None, False, False),
                                     ("num"   , int , 1   , False, True )],
                                    True)

  infile     = opts["infile"]
  log_number = opts["log_number"]

  brief      = opts["brief"]
  visual     = opts["visual"]
  width      = opts["width"]
  old        = opts["old"]
  num        = opts["num"]

  if opts["tape"] == None:
    tape = 10000000
  else:
    tape = opts["tape"]

  if opts["steps"] == None:
    steps = 1000000000
  else:
    steps = opts["steps"]

  if old:
    machine = load_old(infile)
  else:
    machine = load(infile,num,log_number)
  infile.close()

  if not brief:
    print_machine(machine)

  if visual:
    num_syms, num_steps = run_visual(machine,tape,steps,width,brief)
    print
    print "Number of 'not 0's printed: %u, steps: %u" % (num_syms,num_steps)
  else:
    num_syms, num_steps = run(machine,tape,steps,brief)
    if brief:
      print machine.num_states,machine.num_symbols,num_syms,num_steps
    else:
      print
      print "Number of 'not 0's printed: %u, steps: %u" % (num_syms,num_steps)

  sys.stdout.flush()
  sys.exit(0)
