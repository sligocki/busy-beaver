#! /usr/bin/env python3
"""
Enumerate all adjacent machines to an input one.
"""

import argparse
import copy
from pathlib import Path
import sys

import IO
from IO.TM_Record import TM_Record
from Macro import Turing_Machine
from TM_Enum import TM_Enum
import TNF


def enum_cell(old_tm : Turing_Machine.Simple_Machine,
              state_in, symbol_in):
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

def adjacent(tm : Turing_Machine.Simple_Machine):
  # All TMs which differ in only one cell are adjacent.
  for state_in in range(tm.num_states):
    for symbol_in in range(tm.num_symbols):
      # Don't modify Halt since this will most likely lead to a machine with no halts.
      if tm.trans_table[state_in][symbol_in].condition == Turing_Machine.RUNNING:
        for new_tm in enum_cell(tm, state_in, symbol_in):
          yield new_tm

def permute_start_state(tm : Turing_Machine.Simple_Machine):
  """Enumerate all TMs with the same ttable (just different start states)."""
  old_start_state = 0
  symbol_order = list(range(tm.num_symbols))
  for new_start_state in range(tm.num_states):
    state_order = list(range(tm.num_states))
    state_order[new_start_state] = old_start_state
    state_order[old_start_state] = new_start_state
    yield TNF.permute_table(tm, state_order, symbol_order)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("infile", type=Path)
  parser.add_argument("outfile", type=Path)

  parser.add_argument("--only-perms", action="store_true",
                      help="Only list permutations.")
  args = parser.parse_args()

  with IO.StdText.Writer(args.outfile) as writer:
    with IO.Reader(args.infile) as reader:
      for tm_record in reader:
        allow_no_halt = tm_record.tm_enum().allow_no_halt
        for perm_tm in permute_start_state(tm_record.tm()):
          new_tm_enum = TM_Enum(perm_tm, allow_no_halt = allow_no_halt)
          new_tm_record = TM_Record(tm_enum = new_tm_enum)
          writer.write_record(new_tm_record)
        if not args.only_perms:
          for adj_tm in adjacent(tm_record.tm()):
            for perm_tm in permute_start_state(adj_tm):
              new_tm_enum = TM_Enum(perm_tm, allow_no_halt = allow_no_halt)
              new_tm_record = TM_Record(tm_enum = new_tm_enum)
              writer.write_record(new_tm_record)

if __name__ == "__main__":
  main()
