#! /usr/bin/env python
#
# Busy_Beaver_Sim.py
#
# This module contains the Busy_Beaver class, which runs a Turing machine
# simulator (either in C or Python) with an initially blank tape.
#

import sys
import time
from types import *
import string
from random import randint
import getopt

import pdb

import Turing_Machine_Sim

class Invalid_Turing_Machine_State:
  """
  This exception class is raised if a Turing Machine state
  is improperly initialized.
  """

  def __init__(self, value=None):
    self.value = value

  def __repr__(self):
    return `self.value`


class Invalid_Turing_Machine:
  """
  This exception class is raised if a Turing Machine
  is improperly initialized.
  """

  def __init__(self, value=None):
    self.value = value

  def __repr__(self):
    return `self.value`


class Turing_Machine_Runtime_Error:
  """
  This exception class is raised if an error occurs while
  simulating a Turing Machine.
  """

  def __init__(self, value=None):
    self.value = value

  def __repr__(self):
    return `self.value`


class Turing_Machine_IO_Error:
  """
  This exception class is raised if an error occurs while
  loading the representation of a Turing Machine from a file
  or while saving the representation of a Turing Machine to a file.
  """

  def __init__(self, value=None):
    self.value = value

  def __repr__(self):
    return `self.value`


class Busy_Beaver:
  """
  This class simulates Turing machines and is used to search for
  Busy Beaver Turing machines, which print a maximal number of 1's
  before stopping.

  The tape on this Turing machine consists only of zeros and ones
  (all zeros to start with) and is finite in length.

  """

  def __init__(self, nstates=5, nsymbols=2, tape_length=10000, contents=None):
    """
    Create the Turing machine.  Initialize all the states
    and create the tape.  

    Arguments:
    -- nstates: number of states of the Turing machine.
    -- nsymbols: number of symbols used by the Turing machine.
    -- tape_length: the length of the tape.
    -- contents: a list of tuples representing the data
           associated with a single state of the Turing
           machine.  Each tuple is of the form:
               ((p, dir, next), ... , (p, dir, next))
           where:
           -- p: the number to print on the tape (0 or 1)
           -- dir: the direction to move (0 = left, 1 = right)
           -- next: the next state (-1 = halt)
       If contents == None then generate random contents
       with the same structure.
    """

    self.nstates = nstates
    self.nsymbols = nsymbols
    self.contents = contents
    self.tape_length = tape_length

    if self.contents == None:
      self.generate_random_contents()
    else:
      self.verify_contents


  def verify_state_info(self, state_info):
    """
    Verify the information about a particular Turing Machine
    state, and raise an exception if the state information
    is invalid.
    """

    pass


  def verify_contents(self):
    """
    Verify the information about the contents and raise an
    exception if the state information is invalid.
    """

    found_halt = False

    # Must be nstates states in contents
    if len(self.contents) != self.nstates:
      raise Invalid_Turing_Machine_State

    for state in self.contents:
      # Must be 'nsymbols' indexes available for each state
      if len(state) != self.nsymbols:
        raise Invalid_Turing_Machine_State
      for index_state in state:
        # Must be 3 arguments to be followed in each index_state
        if len(index_state) != 3:
          raise Invalid_Turing_Machine_State
        # Must write a valid charactor (value) (i.e. 0 or 1)
        if (index_state[0] < 0 or index_state[0] >= self.nsymbols):
          raise Invalid_Turing_Machine_State
        # Must go in a valid direction (0 = L, 1 = R)
        if not (index_state[1] == 0 or index_state[1] == 1):
          raise Invalid_Turing_Machine_State
        # Must go to a valid state (i.e. between -1 and nstates - 1)
        if index_state[2] < -1 or index_state[2] > self.nstates - 1:
          raise Invalid_Turing_Machine_State
        # Test for a halt (-1)
        if index_state[2] == -1:
          found_halt = True

    # There must be a halt (-1)
    if found_halt == False:
      raise Invalid_Turing_Machine_State
              

  def generate_random_contents(self):
    """
    This function generates random valid values for the
    contents of the Turing machine.  It is guaranteed to
    have a single halt state which is reached from only
    one path.
    """

    self.contents = [ [0] * self.nsymbols ] * self.nstates

    for i in xrange(self.nstates):
      for j in xrange(self.nsymbols):
        self.contents[i][j] = [randint(0, self.nsymbols - 1),
                               randint(0, 1),
                               randint(0, self.nstates - 1)]

    self.contents[randint(0, self.nstates - 1)][randint(0, self.nsymbols-1)][2] = -1

    for i in xrange(self.nstates):
      for j in xrange(self.nsymbols):
        self.contents[i][j] = tuple(self.contents[i][j])


  def save_detail(self, filename):
    """
    Save the contents of the Turing machine to a file.
    """

    file = open(filename, "w")
    file.write("Conditions:\n")
    file.write("Number of States = %d\n" % self.nstates)
    file.write("Number of Symbols = %d\n" % self.nsymbols)
    file.write("Tape length = %d\n" % self.tape_length)
    file.write("Transition table:\n")
    for i in xrange(len(self.contents)):
      file.write("State %d: " % i)
      for j in xrange(len(self.contents[i])):
        file.write("%d:%d,%d,%d; " % j,self.contents[i][j])
      file.write("\n")
    file.write("\n")
    file.write("Time Run = %d\n" % self.time_run)

    file.close()


  def save(self, filename):
    """
    Save the contents of the Turing machine to a file.
    """

    file = open(filename, "wb")

    for state in self.contents:
      for symbol in state:
        file.write(`symbol[0]` + " ")
        if symbol[1] == 1:
          file.write("R ")
        else:
          file.write("L ")
        file.write(`symbol[2]` + " ")
      file.write("\n")


  def load(self, filename):
    """
    Load the contents of the Turing machine from a file.
    """

    # contents is stored as a list of lists of lists
    # e.g. contents = [ [ (1, 0,  1), (1, 1,  1) ],
    #                   [ (1, 1,  0), (1, 0, -1) ]  ]
    # contents[n][v] = (char_write, direction_move, state_become)
    #       for state n and current char v (value at current position)

    file = open(filename, "rb")

    data = file.read()
    data = data.splitlines()

    self.nstates = len(data)
    self.nsymbols = 0

    for state in data:
      state = state.split()

      if self.nsymbols == 0:
        self.nsymbols = int(len(state)) / 3
        self.contents = []

      for j in xrange(self.nsymbols):
        if state[3*j + 1] == "R":
          state[3*j + 1] = 1
        elif state[3*j + 1] == "L":
          state[3*j + 1] = 0
        else:
          raise Invalid_Turing_Machine_State

      state = map(int, state)

      state_list = [None] * self.nsymbols
      for j in xrange(self.nsymbols):
        state_list[j] = tuple(state[3*j:3*j + 3])

      self.contents.append(state_list)

    self.verify_contents()


  def print_contents(self):
    """
    Pretty-print the contents of the Turing machine.
    This method prints the state transition information
    (number to print, direction to move, next state) for each state
    but not the contents of the tape.
    """

    print "Transition table:"

    for i in xrange(len(self.contents)):
      print "  State %d: " % i
      for j in xrange(len(self.contents[i])):
        print "    ",j,": ", self.contents[i][j]
        
    sys.stdout.flush()


  def run(self, check=10000, silent=False):
    """
    Start the tape and run it until it halts.
    If 'silent' is 1, don't print out anything during the run.
    """

    start_time = time.time()
    result = Turing_Machine_Sim.run(self.contents,self.nstates,self.nsymbols,
                                    self.tape_length,check)
    end_time = time.time()

    exit_cond = int(result[0])

    if exit_cond < 0:
      print "Error: %s" % result[2]
    elif exit_cond <= 2:
      self.num_syms  = int(result[1])
      self.num_steps = int(result[2])

      if not silent:
        print

        if (start_time == end_time):
          print "Steps/second: infinite, ;-)"
        else:
          print "Steps/second: ",self.num_steps / (end_time - start_time)
    elif exit_cond == 3:
      print "Invalid state found"
    elif exit_cond == 4:
      print "Infinite result: %s" % result[2]
    else:
      print "Unknown exit code: %d" % exit_cond

    sys.stdout.flush()


  def run_visual(self, check=10000, print_width=35, silent=False):
    """
    Start the tape and run it until it halts with visual output.
    """

    start_time = time.time()

    num_syms = 0

    tape = [0] * self.tape_length
    middle = self.tape_length / 2

    position = middle

    position_start = position
    position_end   = position

    state = 0

    max_syms = 0
    total_steps = 0

    num_steps = check

    print

    t = 0
    nt = 1
    while t < nt:
      for i in xrange(num_steps):
        if position < 1 or position >= self.tape_length-1:
          print "Oops..."
          sys.stdout.flush()
          self.num_syms  = -1
          self.num_steps = -1
          return

        value = tape[position]

        new_value = self.contents[state][value][0]
        new_move  = self.contents[state][value][1]
        new_state = self.contents[state][value][2]

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

        if position > middle - print_width - 2 and position < middle + print_width +1:
          just_on = True

          cur_step = total_steps + i

          sys.stdout.write("%10d: " % int(cur_step+1))

          for j in xrange(2*print_width):
            value = tape[middle+(j-print_width)]
            if value != 0:
              if position == middle+(j-print_width):
                sys.stdout.write("%1c" % int(value+64))
              else:
                sys.stdout.write("%1c" % int(value+96))
            else:
              if position == middle+(j-print_width):
                sys.stdout.write(":")
              else:
                sys.stdout.write(".")

          sys.stdout.write(" %1d\n" % new_state)

          sys.stdout.flush()
        else:
          if just_on:
            sys.stdout.write("       ...\n")
            sys.stdout.flush()

            just_on = False

        if position < 1 or position >= self.tape_length-1:
          break

        state = new_state

        if state == -1:
          break

      total_steps += i

      if position < 1 or position >= self.tape_length-1:
        break

      if state == -1:
        break

      if num_syms > max_syms:
        nt += num_syms - max_syms
        max_syms = num_syms

    if state != -1:
      self.num_syms  = 0
      self.num_steps = 0
    else:
      self.num_syms  = num_syms
      self.num_steps = total_steps + 1

    end_time = time.time()

    if not silent:
      print
      print
      print "Steps/second: ",self.num_steps / (end_time - start_time)
      print
      print "Range on tape: ",position_start - middle, \
                         "to",position_end   - middle
      sys.stdout.flush()


#
# Test the class.
#

if __name__ == "__main__":
  def usage():
    print "Usage  Busy_Beaver_Sim.py [-b] [-h] [-v] [-w width] [--brief] [--help] [--visual] [--width=width] [filename]"
    sys.stdout.flush()

  bb = Busy_Beaver(5, 2, 10000000)
  print_width = 30

  try:
    opts, args = getopt.getopt(sys.argv[1:],"bhvw:",["brief","help","visual","width"])
  except getopt.GetoptError:
    usage()
    sys.exit(1)

  brief  = False
  visual = False

  for opt, arg in opts:
    if opt in ("-b","--brief"):
      brief = True
    if opt in ("-v","--visual"):
      brief  = False
      visual = True
    if opt in ("-w","--width"):
      print_width = int(arg)
    if opt in ("-h","--help"):
      usage()
      sys.exit()

  if len(args) == 0:
    bb.load("bb.in")
  elif len(args) == 1:
    bb.load(args[0])
  else:
    usage()
    sys.exit(1)

  if not brief:
    bb.print_contents()

  if visual:
    bb.run_visual(10000000.0,print_width,brief)
  else:
    bb.run(10000000.0,brief)

  if brief:
    print bb.nstates,bb.nsymbols,bb.num_syms,bb.num_steps
  else:
    print
    print "Number of 'not O's printed: %u, steps: %u" % (bb.num_syms,bb.num_steps)

  sys.stdout.flush()

  bb.save("bb.out")

