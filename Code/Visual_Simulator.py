#! /usr/bin/env python3
# Visual simulation of a Turing Machine in terminal.

import argparse
import fcntl
import re
import string
import struct
import sys
import termios

from Direct_Simulator import DirectSimulator
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


def should_print(sim : DirectSimulator, print_ops : str) -> bool:
  if "a" in print_ops:
    return True
  if "l" in print_ops and sim.tape.pos_leftmost() == sim.tape.position:
    return True
  if "r" in print_ops and sim.tape.pos_rightmost() == sim.tape.position:
    return True
  return False

def print_tape(sim : DirectSimulator, args) -> None:
  if should_print(sim, args.print):
    half_width = args.print_width // 2 - 10
    if args.relative:
      print_range = range(sim.tape.position - half_width, sim.tape.position + half_width + 1)
    else:
      print_range = range(-half_width, half_width+1)

    sys.stdout.write("\033[0m%10d: " % sim.step_num)

    for pos in print_range:
      value = sim.tape.read_pos(pos)
      if sim.tape.position == pos:
        # If this is the current possition ...
        sys.stdout.write("\033[1;%dm%c" % (COLOR[value], STATES[sim.state]))
      else:
        sys.stdout.write("\033[%dm " % COLOR[value])

    state_str = sim.tm.states[sim.state] if not sim.halted else "HALT"
    sys.stdout.write(f"\033[0m{state_str:4}")
    sys.stdout.write(" \033[%dm%2d\033[0m\n" % (
      COLOR[sim.tape.read()], sim.tape.read()))

    sys.stdout.flush()


def run_visual(sim : DirectSimulator, args):
  print_tape(sim, args)

  while not sim.halted:
    sim.step()
    print_tape(sim, args)

  print("TM Halted on step", sim.step_num)


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
    term_height, term_width = struct.unpack("hh", fcntl.ioctl(fd, termios.TIOCGWINSZ, "1234"))
  except:
    term_width = 80

  parser = argparse.ArgumentParser()
  parser.add_argument("tm", help="Turing Machine or file or file:record_num (0-indexed).")

  parser.add_argument("start_config", nargs="?",
                      help="Start at non-blank tape configuration. "
                      "Ex: 1 23^8 21 <B 0^6 12^7 1")

  parser.add_argument("--print-width", "-w", type=int, default=term_width,
                      help="Width to print to terminal.")
  parser.add_argument("--no-ttable", action="store_true",
                      help="Don't print transition table.")

  # Print options
  parser.add_argument("--relative", "-r", action="store_true",
                      help="Print so that TM head always at the same column.")
  parser.add_argument("--print", "-p", default="a",
                      help="When to print tape: a: always, l: leftmost, r: rightmost. "
                      "May be combined, ex: lr")

  args = parser.parse_args()

  tm = IO.get_tm(args.tm)
  sim = DirectSimulator(tm)

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

  sim.state = state
  for i, symb in enumerate(left):
    # Write left half of tape so that the rightmost symbol is at location -1.
    sim.tape.write_pos(symb, i-len(left))
  for i, symb in enumerate(right):
    # Write right half of tape so that the leftmost symbol is at location 0.
    sim.tape.write_pos(symb, i)

  run_visual(sim, args=args)
  sys.stdout.flush()

if __name__ == "__main__":
  main()
