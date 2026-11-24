#! /usr/bin/env python3
# Visual simulation of a Turing Machine in terminal.

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass

import IO
from Direct_Simulator import DirectSimulator, State
from Macro import Turing_Machine
from Parse_Config import STATES, expand_config, parse_tape_config

# Note: Halt will be "!" (already defined in Parse_Config.STATES)
# White, Red, Green, Blue, Cyan, Brown/Yellow, Magenta
COLOR = [49, 41, 42, 44, 46, 43, 45]


@dataclass(frozen=True)
class PrintFilter:
  # Which states should we print for
  states: list[State]
  # Which locations should we print for
  extreme: str

  @staticmethod
  def parse(filter_str: str) -> PrintFilter:
    states = []
    extreme = ""
    for x in filter_str:
      if x in "lr":
        extreme += x
      else:
        states.append(STATES.index(x))
    return PrintFilter(states, extreme)

  def should_print(self, sim: DirectSimulator) -> bool:
    return self.should_print_state(sim) and self.should_print_loc(sim)

  def should_print_state(self, sim: DirectSimulator) -> bool:
    if not self.states:
      return True
    else:
      return sim.state in self.states

  def should_print_loc(self, sim: DirectSimulator) -> bool:
    if not self.extreme:
      return True
    if "l" in self.extreme and sim.tape.pos_leftmost() == sim.tape.position:
      return True
    if "r" in self.extreme and sim.tape.pos_rightmost() == sim.tape.position:
      return True
    return False


def print_tape(sim: DirectSimulator, args) -> None:
  half_width = args.print_width // 2 - 10
  if args.relative:
    print_range = range(sim.tape.position - half_width, sim.tape.position + half_width + 1)
  else:
    print_range = range(-half_width, half_width + 1)

  sys.stdout.write("\033[0m%10d: " % sim.step_num)

  for pos in print_range:
    value = sim.tape.read(pos)
    if sim.tape.position == pos:
      # If this is the current position ...
      sys.stdout.write("\033[1;%dm%c" % (COLOR[value], STATES[sim.state]))
    else:
      sys.stdout.write("\033[%dm " % COLOR[value])

  state_str = sim.tm.states[sim.state] if not sim.halted else "HALT"
  sys.stdout.write(f"\033[0m{state_str:4}")
  sys.stdout.write(" \033[%dm%2d\033[0m\n" % (COLOR[sim.tape.read()], sim.tape.read()))

  sys.stdout.flush()


def run_visual(sim: DirectSimulator, filter: PrintFilter, args):
  print_tape(sim, args)

  while not sim.halted:
    sim.step()
    if filter.should_print(sim):
      print_tape(sim, args)

  print("TM Halted on step", sim.step_num)


def ttable_with_colors(tm):
  s = Turing_Machine.machine_ttable_to_str(tm)
  for symb, col in zip(Turing_Machine.SYMBOLS, COLOR):
    s = s.replace(" " + symb, " \033[%dm%s\033[0m" % (col, symb))
  return s


def get_terminal_width(default: int = 80) -> int:
  try:
    cols = int(os.environ.get("COLUMNS", ""))
    if cols > 0:
      return cols
  except ValueError:
    pass
  for stream in (sys.stdout, sys.stderr, sys.stdin):
    try:
      cols = os.get_terminal_size(stream.fileno()).columns
      if cols > 0:
        return cols
    except (AttributeError, OSError, ValueError):
      continue
  return default


def main():
  term_width = get_terminal_width()

  parser = argparse.ArgumentParser()
  parser.add_argument("tm", help="Turing Machine or file or file:record_num (0-indexed).")

  parser.add_argument(
    "start_config",
    nargs="?",
    help="Start at non-blank tape configuration. Ex: 1 23^8 21 <B 0^6 12^7 1",
  )

  parser.add_argument(
    "--print-width",
    "-w",
    type=int,
    default=term_width,
    help="Width to print to terminal.",
  )
  parser.add_argument("--no-ttable", action="store_true", help="Don't print transition table.")

  # Print options
  parser.add_argument(
    "--relative",
    "-r",
    action="store_true",
    help="Print so that TM head always at the same column.",
  )
  parser.add_argument(
    "--print-filter",
    "-p",
    default="",
    help="When to print tape: l: leftmost, r: rightmost. "
    "Uppercase letters may be used for states as well. "
    "May be combined, ex: lrBC",
  )

  args = parser.parse_args()

  tm = IO.get_tm(args.tm)
  sim = DirectSimulator(tm)

  if not args.no_ttable:
    print(ttable_with_colors(tm))
    print(tm.ttable_str())
    print()

  state = 0
  left = []
  right = []
  if args.start_config:
    parsed = parse_tape_config(args.start_config)
    state, left, right = expand_config(parsed)

  sim.state = Turing_Machine.Simple_Machine_State(state)
  for i, symb in enumerate(left):
    # Write left half of tape so that the rightmost symbol is at location -1.
    sim.tape.write(symb, i - len(left))
  for i, symb in enumerate(right):
    # Write right half of tape so that the leftmost symbol is at location 0.
    sim.tape.write(symb, i)

  filter = PrintFilter.parse(args.print_filter)

  run_visual(sim, filter, args=args)
  sys.stdout.flush()


if __name__ == "__main__":
  main()
