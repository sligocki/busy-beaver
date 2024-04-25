#! /usr/bin/env python3
"""
Enumerate all adjacent machines to an input one.
"""

import argparse
import copy
import sys
from typing import Iterator

import IO
from Macro import Turing_Machine
import Permute


def enum_cell(old_tm : Turing_Machine.Simple_Machine,
              state_in, symbol_in) -> Iterator[Turing_Machine.Simple_Machine]:
  """Enumerate all TTables where cell (state_in, symbol_in) is modified."""
  new_tm = copy.deepcopy(old_tm)
  for state_out in range(old_tm.num_states):
    for symbol_out in range(old_tm.num_symbols):
      for dir_out in range(2):
        new_trans = Turing_Machine.Transition(
          condition = Turing_Machine.RUNNING,
          symbol_out = symbol_out, state_out = state_out, dir_out = dir_out,
          num_base_steps = 1, states_last_seen = {state_in: 0})
        if not old_tm.trans_table[state_in][symbol_in].equals(new_trans):
          new_tm.trans_table[state_in][symbol_in] = new_trans
          yield new_tm

def adjacent(tm : Turing_Machine.Simple_Machine) -> Iterator[Turing_Machine.Simple_Machine]:
  # All TMs which differ in only one cell are adjacent.
  for state_in in range(tm.num_states):
    for symbol_in in range(tm.num_symbols):
      # Don't modify Halt since this will most likely lead to a machine with no halts.
      if tm.trans_table[state_in][symbol_in].condition == Turing_Machine.RUNNING:
        yield from enum_cell(tm, state_in, symbol_in)


def write_adjacent(tm : Turing_Machine.Simple_Machine, writer, tnf_max_steps : int) -> None:
  Permute.write_perms(tm, writer, tnf_max_steps)
  for adj_tm in adjacent(tm):
    Permute.write_perms(adj_tm, writer, tnf_max_steps)

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm", nargs="?",
                      help="Literal Turing Machine. If missing read from stdin.")
  parser.add_argument("--tnf-max-steps", type=int, default=1_000,
                      help="Maximum number of steps to attempt to find TNF.")
  args = parser.parse_args()

  with IO.StdText.Writer(sys.stdout) as writer:
    if args.tm:
      tm = IO.parse_tm(args.tm)
      write_adjacent(tm, writer, args.tnf_max_steps)
    else:
      with IO.StdText.Reader(sys.stdin) as reader:
        for tm_record in reader:
          write_adjacent(tm_record.tm(), writer, args.tnf_max_steps)

if __name__ == "__main__":
  main()
