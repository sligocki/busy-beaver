#! /usr/bin/env python3
# Visual simulation of a Turing Machine in terminal.

import argparse
import fcntl
import itertools
import string
import struct
import sys
import termios
import time

import IO
from Macro import Turing_Machine


# White, Red, Green, Blue, Magenta, Cyan, Brown/Yellow
color = [49, 41, 42, 44, 45, 46, 43]
# Note: Halt will be "Z"
states = string.ascii_uppercase
def run_visual(TTable, print_width, tape_length=100_000):
  """
  Start the tape and run it until it halts with visual output.
  """

  start_time = time.time()

  num_syms = 0

  tape = [0] * tape_length
  start_pos = tape_length // 2  # Default to middle

  position = start_pos

  position_left  = position
  position_right = position

  state = 0

  half_width = (print_width - 18) // 2
  if half_width < 1:
    half_width = 1

  # Print configuration
  sys.stdout.write("\033[0m%10d: " % 0)  # Step number

  for j in range(2*half_width):
    value = tape[start_pos+(j-half_width)]
    if position == start_pos+(j-half_width):
      # If this is the current position ...
      sys.stdout.write("\033[1;%dm%c" % (color[value], states[state]))
    else:
      sys.stdout.write("\033[%dm " % (color[value]))

  sys.stdout.write("\033[0m  %c" % states[state])
  sys.stdout.write(" %2d\n" % tape[position])

  sys.stdout.flush()

  for step_num in itertools.count(1):
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
    if position > start_pos - half_width - 2 and position < start_pos + half_width +1:
      just_on = True

      sys.stdout.write("\033[0m%10d: " % int(step_num))  # Step number

      for j in range(2*half_width):
        value = tape[start_pos+(j-half_width)]
        if position == start_pos+(j-half_width):
          # If this is the current possition ...
          sys.stdout.write("\033[1;%dm%c" % (color[value], states[new_state]))
        else:
          sys.stdout.write("\033[%dm " % color[value])

      sys.stdout.write("\033[0m  %c" % states[new_state])
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


if __name__ == "__main__":
  # Get terminal width, this is surprisingly hard to do :(
  # See: http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
  try:
    # This will be fooled if you pipe in stdin from somewhere else, but I don't
    # know why you would do that since this program doesn't read stdin.
    fd = 0
    term_height, term_width = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
  except:
    term_width = 80

  parser = argparse.ArgumentParser()
  parser.add_argument("tm_file")
  parser.add_argument("tm_line", type=int, nargs="?", default=1)
  parser.add_argument("--width", type=int, default=term_width,
                      help="width to print to terminal.")
  args = parser.parse_args()

  ttable = IO.Text.load_TTable_filename(args.tm_file, args.tm_line)
  tm = Turing_Machine.Simple_Machine(ttable)

  print(Turing_Machine.machine_ttable_to_str(tm))
  run_visual(ttable, args.width)
  sys.stdout.flush()
