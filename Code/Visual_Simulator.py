#! /usr/bin/env python3
# Visual simulation of a Turing Machine in terminal.

import argparse
import fcntl
import itertools
import math
import re
import string
import struct
import sys
import termios

import IO
from Macro import Turing_Machine


# Note: Halt will be "!"
STATES = string.ascii_uppercase + string.ascii_lowercase + "!"
# White, Red, Green, Blue, Cyan, Brown/Yellow, Magenta
COLOR = [49, 41, 42, 44, 46, 43, 45]


def parse_config(config_str):
  left = []
  right = []
  in_left = True
  dir_left = None
  state = None
  for block in config_str.split():
    if (m := re.fullmatch(r"<([A-Za-z])", block)):
      dir_left = True
      state = STATES.index(m.group(1))
      in_left = False

    elif (m := re.fullmatch(r"([A-Za-z])>", block)):
      dir_left = False
      state = STATES.index(m.group(1))
      in_left = False

    else:
      assert (m := re.fullmatch(r"(\d+)(\^(\d+))?", block)), block
      base = [int(x) for x in m.group(1)]
      if m.group(3):
        exp = int(m.group(3))
      else:
        exp = 1
      if in_left:
        left += base * exp
      else:
        right += base * exp

  if dir_left:
    # Normalize so that current (top) symbol is always on right.
    top = left.pop() if left else 0
    right.insert(0, top)

  return (state, left, right)


def print_tape(tape : list[int], position : int, start_pos : int, half_width : int,
               tm : Turing_Machine.Simple_Machine, state, step_num : int):
  sys.stdout.write("\033[0m%10d: " % step_num)

  for j in range(2*half_width):
    value = tape[start_pos+(j-half_width)]
    if position == start_pos+(j-half_width):
      # If this is the current possition ...
      sys.stdout.write("\033[1;%dm%c" % (COLOR[value], STATES[state]))
    else:
      sys.stdout.write("\033[%dm " % COLOR[value])

  state_str = tm.states[state] if state >= 0 else "HALT"
  sys.stdout.write(f"\033[0m{state_str:4}")
  sys.stdout.write(" \033[%dm%2d\033[0m\n" % (
    COLOR[tape[position]], tape[position]))

  sys.stdout.flush()


def run_visual(tm : Turing_Machine.Simple_Machine,
               print_width : int,
               start_state, start_left_tape, start_right_tape,
               *, tape_length : int = 100_000, max_steps : int = math.inf,
               args):
  """
  Start the tape and run it until it halts with visual output.
  """
  tape = [0] * tape_length
  start_pos = tape_length // 2  # Default to middle

  position = start_pos

  position_left  = position
  position_right = position

  state = start_state
  tape[position - len(start_left_tape):position + len(start_right_tape)] = \
    start_left_tape + start_right_tape

  half_width = (print_width - 19) // 2
  if half_width < 1:
    half_width = 1

  print_tape(tape, position, start_pos, half_width, tm, state, 0)

  for step_num in itertools.count(1):
    value = tape[position]
    trans = tm.get_trans_object(value, state)

    tape[position] = trans.symbol_out

    if trans.dir_out == Turing_Machine.LEFT:
      position -= 1
      if position < position_left:
        position_left = position
    else:
      position += 1
      if position > position_right:
        position_right = position

    state = trans.state_out

    # Print configuration
    if position > start_pos - half_width - 2 and position < start_pos + half_width +1:
      just_on = True
      if args.only_leftmost:
        if position == position_left:
          print_tape(tape, position, start_pos, half_width, tm, state, step_num)
      elif args.only_rightmost:
        if position == position_right:
          print_tape(tape, position, start_pos, half_width, tm, state, step_num)
      else:
        print_tape(tape, position, start_pos, half_width, tm, state, step_num)
    elif just_on:
      sys.stdout.write("       ...\n")
      sys.stdout.flush()
      just_on = False

    if position < 1 or position >= tape_length-1:
      break

    if step_num >= max_steps:
      break

    if state == -1:
      print("TM Halted on step", step_num)
      break


def ttable_with_colors(tm):
  s = Turing_Machine.machine_ttable_to_str(tm)
  for symb, col in zip(Turing_Machine.SYMBOLS, COLOR):
    s = s.replace(" " + symb, " \033[%dm%s\033[0m" % (col, symb))
  return s


def main():
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
  parser.add_argument("record_num", type=int, nargs="?", default=0)
  parser.add_argument("--width", type=int, default=term_width,
                      help="width to print to terminal.")
  parser.add_argument("--start-config",
                      help="Start at non-blank tape configuration. "
                      "Ex: 1 23^8 21 <B 0^6 12^7 1")
  parser.add_argument("--only-leftmost", "-l", action="store_true",
                      help="Only print tape when TM reaches the leftmost position")
  parser.add_argument("--only-rightmost", "-r", action="store_true",
                      help="Only print tape when TM reaches the rightmost position")

  parser.add_argument("--max-steps", type=int, default=math.inf,
                      help="Limit number of steps run")
  parser.add_argument("--no-ttable", action="store_true")
  args = parser.parse_args()

  tm = IO.load_tm(args.tm_file, args.record_num)

  if not args.no_ttable:
    print(ttable_with_colors(tm))
    print(tm.ttable_str())
    print()

  if args.start_config:
    state, left, right = parse_config(args.start_config)
  else:
    state = 0
    left = []
    right = []

  run_visual(tm, args.width, state, left, right,
             max_steps=args.max_steps, args=args)
  sys.stdout.flush()

if __name__ == "__main__":
  main()
