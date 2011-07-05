#! /usr/bin/env python
#
# Growth_Fit.py
#
"""
Collects data on tape used vs. steps taken and fits curves to the data.
"""

import sys
import time

from Turing_Machine import Turing_Machine

def count(infile, num = 1):
  """
  Load the contents of the Turing machine from a file.
  """
  import string

  line = infile.readline()
  linenum = 1

  while line:
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
      sys.stdout.write("%-12d     " % linenum)
      TTable = eval(string.join(parts[start_index:end_index]))
    else:
      sys.stderr.write("Turing machine not found in input file\n")
      sys.exit(1)

    machine = Turing_Machine(TTable)

    result = run(machine,tape,steps,brief)

    x = numpy.array(result[0])
    y = numpy.array(result[1])
    l = numpy.array(result[2])
    r = numpy.array(result[3])

    # print
    # print x
    # print y

    loglin = numpy.polyfit(numpy.log(x),y,1)

    a = 1.0/loglin[0]
    if a > 500:
      a = math.exp(500)
    else:
      a = math.exp(a)

    b = -loglin[1]/loglin[0]
    if b > 500:
      b = math.exp(500)
    else:
      b = math.exp(b)

    sys.stdout.write("Log: %13.6e %13.6e   " % (a,b))

    loglog = numpy.polyfit(numpy.log(x),numpy.log(y),1)

    a = 1.0/loglog[0]

    b = -loglog[1]/loglog[0]
    if b > 500:
      b = math.exp(500)
    else:
      b = math.exp(b)

    sys.stdout.write("Poly: %13.6e %13.6e   " % (a,b))

    sys.stdout.write(" - width\n")

    loglin = numpy.polyfit(numpy.log(x),l,1)

    a = 1.0/loglin[0]
    if a > 500:
      a = math.exp(500)
    else:
      a = math.exp(a)

    b = -loglin[1]/loglin[0]
    if b > 500:
      b = math.exp(500)
    else:
      b = math.exp(b)

    sys.stdout.write("                 ")
    sys.stdout.write("Log: %13.6e %13.6e   " % (a,b))

    loglog = numpy.polyfit(numpy.log(x),numpy.log(l),1)

    a = 1.0/loglog[0]

    b = -loglog[1]/loglog[0]
    if b > 500:
      b = math.exp(500)
    else:
      b = math.exp(b)

    sys.stdout.write("Poly: %13.6e %13.6e   " % (a,b))

    sys.stdout.write(" - left\n")

    loglin = numpy.polyfit(numpy.log(x),r,1)

    a = 1.0/loglin[0]
    if a > 500:
      a = math.exp(500)
    else:
      a = math.exp(a)

    b = -loglin[1]/loglin[0]
    if b > 500:
      b = math.exp(500)
    else:
      b = math.exp(b)

    sys.stdout.write("                 ")
    sys.stdout.write("Log: %13.6e %13.6e   " % (a,b))

    loglog = numpy.polyfit(numpy.log(x),numpy.log(r),1)

    a = 1.0/loglog[0]

    b = -loglog[1]/loglog[0]
    if b > 500:
      b = math.exp(500)
    else:
      b = math.exp(b)

    sys.stdout.write("Poly: %13.6e %13.6e   " % (a,b))

    sys.stdout.write(" - right\n")

    sys.stdout.write("\n")

    line = infile.readline()
    linenum += 1

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


def run(machine, tape_length, num_steps, silent=False):
  """
  Start the tape and run it until it halts.
  If 'silent' is 1, don't print out anything during the run.
  """
  from Turing_Machine_Count import Turing_Machine_Count

  start_time = time.time()
  result = Turing_Machine_Count(machine.get_TTable(),
                                machine.num_states,machine.num_symbols,
                                tape_length,num_steps)
  end_time = time.time()

  sys.stdout.flush()

  return result


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
        num_syms -= 1

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
  import numpy
  import math

  opts, args = Filter_Option_Parser(sys.argv,
                                    [("brief" , None, None, False, False),
                                     ("visual", None, None, False, False),
                                     ("width" , int , 79  , False, True ),
                                     ("num"   , int , 1   , False, True )],
                                    True)

  infile = opts["infile"]

  brief  = opts["brief"]
  visual = opts["visual"]
  width  = opts["width"]
  num    = opts["num"]

  if opts["tape"] == None:
    tape = 10000000
  else:
    tape = opts["tape"]

  if opts["steps"] == None:
    steps = 10000000
  else:
    steps = opts["steps"]

  count(infile, num)

  sys.stdout.flush()
  sys.exit(0)
