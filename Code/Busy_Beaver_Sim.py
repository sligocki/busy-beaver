#! /usr/bin/env python
#
# Busy_Beaver_Sim.py
#
# This module contains the Busy_Beaver class, which runs a Turing machine
# simulator (either in C or Python) with an initially blank tape.

import sys, time, string

from Turing_Machine import Turing_Machine

def load(infile, line_num = 1, machine_num = None):
  """
  Load the contents of the Turing machine from a file.
  """

  if machine_num == None:
    while line_num > 1:
      infile.readline()
      line_num -= 1

    line = infile.readline()
    parts = line.split()
  else:
    line = infile.readline()
    parts = line.split()

    while line != "" and int(parts[0]) != machine_num:
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
  sys.stdout.write("\n")

  TTable = machine.get_TTable()

  sys.stdout.write("   ")
  for j in xrange(len(TTable[0])):
    sys.stdout.write("  %d " % j)
  sys.stdout.write("\n")

  for i in xrange(len(TTable)):
    sys.stdout.write(" %c " % chr(ord('A') + i))
    for j in xrange(len(TTable[i])):
      sys.stdout.write(" ")
      if TTable[i][j][2] == -1:
        sys.stdout.write("%c" % 'Z')
      else:
        sys.stdout.write("%c" % chr(ord('A') + TTable[i][j][2]))
      sys.stdout.write("%d" % TTable[i][j][0])
      sys.stdout.write("%c" % ('L','R')[TTable[i][j][1]])
    sys.stdout.write("\n")
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


# White, Red, Blue, Green, Magenta, Cyan, Brown/Yellow
color = [49, 41, 44, 42, 45, 46, 43]
states = string.ascii_uppercase + string.ascii_lowercase + string.digits + "!@#$%^&*"
def run_visual(machine, tape_length, num_steps, print_width=79, silent=False, start_tape=None):
  """
  Start the tape and run it until it halts with visual output.
  """
  
  start_time = time.time()

  num_syms = 0

  tape = [0] * tape_length
  start_pos = tape_length // 2  # Default to middle
  
  if start_tape:
    n = len(start_tape)
    tape[start_pos : start_pos + n] = start_tape
  
  position = start_pos
  
  position_left  = position
  position_right = position

  state = 0

  max_syms = 0
  total_steps = 0

  TTable = machine.get_TTable()

  half_width = (print_width - 18) // 2
  if half_width < 1:
    half_width = 1

  # Print configuration
  if not silent:
    sys.stdout.write("\033[0m%10d: " % 0)  # Step number

    for j in xrange(2*half_width):
      value = tape[start_pos+(j-half_width)]
      if position == start_pos+(j-half_width):
        # If this is the current possition ...
        sys.stdout.write("\033[1;%dm%c" % (color[value], states[state]))
      else:
        sys.stdout.write("\033[%dm " % (color[value]))

    sys.stdout.write("\033[0m  %c" % chr(ord('A') + state))
    sys.stdout.write(" %2d\n" % tape[position])

    sys.stdout.flush()

  t = 0
  nt = 1
  while t < nt:
    for i in xrange(num_steps):
      if position < 1 or position >= tape_length-1:
        print "Oops ... Didn't start on tape!?"
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
        if position < position_left:
          position_left = position
      else:
        position += 1
        if position > position_right:
          position_right = position
      
      # Print configuration
      if not silent:
        if position > start_pos - half_width - 2 and position < start_pos + half_width +1:
          just_on = True

          cur_step = total_steps + i

          sys.stdout.write("\033[0m%10d: " % int(cur_step+1))  # Step number

          for j in xrange(2*half_width):
            value = tape[start_pos+(j-half_width)]
            if position == start_pos+(j-half_width):
              # If this is the current possition ...
              sys.stdout.write("\033[1;%dm%c" % (color[value], states[new_state]))
            else:
              sys.stdout.write("\033[%dm " % (color[value]))

          sys.stdout.write("\033[0m  %c" % chr(ord('A') + new_state))
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
  print "Range on tape: ", position_left  - start_pos, \
                     "to", position_right - start_pos

  sys.stdout.flush()

  return (num_syms, num_steps)


if __name__ == "__main__":
  from Option_Parser import Filter_Option_Parser
  import fcntl, termios, struct

  # Get terminal width to use as the default width. This is surprisingly hard to do :(
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
                                     ("visual"     , None, None, False, False),
                                     ("width", int, term_width , False, True ),
                                     ("old"        , None, None, False, False),
                                     ("line_num"   , int , 1   , False, True ),
                                     ("machine_num", int , None, False, True )],
                                    True)

  infile      = opts["infile"]

  brief       = opts["brief"]
  visual      = opts["visual"]
  width       = opts["width"]
  old         = opts["old"]
  line_num    = opts["line_num"]
  machine_num = opts["machine_num"]

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
    machine = load(infile,line_num,machine_num)
  infile.close()

  #if not brief:
  #  print_machine(machine)

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
