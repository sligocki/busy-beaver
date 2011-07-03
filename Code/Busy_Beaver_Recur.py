#! /usr/bin/env python
#
# Busy_Beaver_Recur.py
#
"""
This module contains the Busy_Beaver class, which runs a Turing machine
simulator in C which outputs the TM tape when the head is at one extreme
of the tape or the other.  This is then used to try to find a repeating
pattern and a recurrence relation for the number of steps in that pattern.
"""

import string
import sys
import time

from IO import IO
from Turing_Machine import Turing_Machine

# White, Red, Blue, Green, Magenta, Cyan, Brown/Yellow
color = [49, 41, 44, 42, 45, 46, 43]
# Characters to use for states (end in "Z" so that halt is Z)
states = string.ascii_uppercase + string.ascii_lowercase + string.digits + "!@#$%^&*" + "Z"
symbols = string.digits + "-"
dirs = "LRS-"

def load(infile, line_num = 1):
  """
  Load the contents of the Turing machine from a file.
  """

  io = IO(infile, None)

  for i, result in enumerate(io):
    # Note: we start counting lines at 1, but enumerate starts at 0.
    if i + 1 == line_num:
      return Turing_Machine(result.ttable)


def print_machine(machine):
  """
  Pretty-print the contents of the Turing machine.
  This method prints the state transition information
  (number to print, direction to move, next state) for each state
  but not the contents of the tape.
  """

  sys.stdout.write("\n")
  sys.stdout.write("Transition table:\n")
  sys.stdout.write("\n")

  TTable = machine.get_TTable()

  sys.stdout.write("       ")
  for j in xrange(len(TTable[0])):
    sys.stdout.write("+-----")
  sys.stdout.write("+\n")

  sys.stdout.write("       ")
  for j in xrange(len(TTable[0])):
    sys.stdout.write("|  %d  " % j)
  sys.stdout.write("|\n")

  sys.stdout.write("   +---")
  for j in xrange(len(TTable[0])):
    sys.stdout.write("+-----")
  sys.stdout.write("+\n")

  for i in xrange(len(TTable)):
    sys.stdout.write("   | %c " % states[i])
    for j in xrange(len(TTable[i])):
      sys.stdout.write("| ")
      if TTable[i][j][0] == -1 and \
         TTable[i][j][1] == -1 and \
         TTable[i][j][2] == -1:
        sys.stdout.write("--- ")
      else:
        sys.stdout.write("%c"   % symbols[TTable[i][j][0]])
        sys.stdout.write("%c"   % dirs   [TTable[i][j][1]])
        sys.stdout.write("%c "  % states [TTable[i][j][2]])
    sys.stdout.write("|\n")

    sys.stdout.write("   +---")
    for j in xrange(len(TTable[0])):
      sys.stdout.write("+-----")
    sys.stdout.write("+\n")

  sys.stdout.write("\n")

  sys.stdout.flush()


def run(machine, tape_length, num_steps, silent=False):
  """
  Start the tape and run it until it halts.
  If 'silent' is True, don't print out anything during the run.
  """
  from Turing_Machine_Recur import Turing_Machine_Recur

  start_time = time.time()
  result = Turing_Machine_Recur(machine.get_TTable(),
                                machine.num_states,machine.num_symbols,
                                tape_length,num_steps)
  end_time = time.time()

  exit_cond = int(result[0])

  num_syms  = 0
  num_steps = 0

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
    bad_state  = int(result[1])
    bad_symbol = int(result[2])

    num_syms  = int(result[3])
    num_steps = int(result[4])

    print "Invalid TM table entry reached - state: %d, symbol: %d" % (bad_state,bad_symbol)
  elif exit_cond == 4:
    print "Infinite result: %s" % result[2]
  else:
    print "Unknown exit code: %d" % exit_cond

  sys.stdout.flush()

  return (num_syms, num_steps)


if __name__ == "__main__":
  from Option_Parser import Filter_Option_Parser
  import fcntl, termios, struct

  # Get terminal width, this is surprisingly hard to do :(
  # See: http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
  try:
    # This will be fooled if you pipe in stdin from somewhere else, but I don't
    # know why you would do that since this program doesn't read stdin.
    fd = 0
    term_height, term_width = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
  except:
    term_width = 80

  opts, args = Filter_Option_Parser(sys.argv,
                                    [("brief"      , None, None, False, False),
                                     ("width", int, term_width , False, True ),
                                     ("line_num"   , int , 1   , False, True )],
                                    True)

  infile      = opts["infile"]

  brief       = opts["brief"]
  width       = opts["width"]
  line_num    = opts["line_num"]

  if opts["tape"] == None:
    tape = 10000000
  else:
    tape = opts["tape"]

  if opts["steps"] == None:
    steps = 1000000000
  else:
    steps = opts["steps"]

  machine = load(infile, line_num)
  infile.close()

  if not brief:
    print_machine(machine)

  num_syms, num_steps = run(machine,tape,steps,brief)
  if brief:
    print machine.num_states, machine.num_symbols, num_syms,num_steps
  else:
    print
    print "Number of 'not 0's printed: %u, steps: %u" % (num_syms, num_steps)

  sys.stdout.flush()
