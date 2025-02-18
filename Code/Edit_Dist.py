#! /usr/bin/env python3
"""
Compute "edit distance" between Turing machines.
Edit distance is the number of transitions that would have to be modified in
order to convert from one to the other modulo state/symbol permutations.
"""

import argparse
import itertools
from typing import Iterator

import IO
from Macro.Turing_Machine import Simple_Machine as TM
from TNF import permute_table


def enum_perms(tm : TM) -> Iterator[TM]:
  """Enumerate all permutations of `tm`."""
  for state_order in itertools.permutations(tm.states):
    # TODO: Should we require leaving 0 as 0?
    for symbol_order in itertools.permutations(tm.symbols):
      for swap_dirs in (False, True):
        yield permute_table(tm, state_order, symbol_order, swap_dirs)

def edit_dist_noperm(tm1 : TM, tm2 : TM) -> int:
  """Edit distance between `tm1` and `tm2` ignoring permutations."""
  # TODO: Support different sized TMs
  assert tm1.states == tm2.states
  assert tm1.symbols == tm2.symbols

  num_diffs = 0
  for state in tm1.states:
    for symbol in tm1.symbols:
      if not tm1.trans_table[state][symbol].equals(tm2.trans_table[state][symbol]):
        num_diffs += 1
  return num_diffs

def edit_dist(tm1 : TM, tm2 : TM) -> int:
  """Minimum edit distance between `tm1` and `tm2` modulo permutations."""
  return min(edit_dist_noperm(tm1_perm, tm2)
             for tm1_perm in enum_perms(tm1))

def compare(tm1 : TM, tm2 : TM) -> None:
  dist = edit_dist(tm1, tm2)
  print(dist, tm1.ttable_str(), tm2.ttable_str())

def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument("tm", nargs="+",
                      help="Turing Machine or file or file:record_num (0-indexed).")
  parser.add_argument("--max-tms", "-n", type=int, default=20,
                      help="Maximum number of TMs to compare.")
  args = parser.parse_args()

  tms : list[TM] = []
  for tm_str in args.tm:
    for tm in IO.iter_tms(tm_str):
      tms.append(tm)

  tms = tms[:args.max_tms]

  # Compare all combinations
  for tm1, tm2 in itertools.combinations(tms, 2):
    compare(tm1, tm2)

if __name__ == "__main__":
  main()
