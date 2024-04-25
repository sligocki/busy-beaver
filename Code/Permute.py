#! /usr/bin/env python3
# Enumerate permutations of a Turing Machine.

import argparse
import sys
from typing import Iterator

import IO
from Macro import Turing_Machine
import TNF


def try_tnf(tm : Turing_Machine.Simple_Machine, tnf_max_steps : int) -> Turing_Machine.Simple_Machine:
  """Attempt to convert a TM to TNF, return original if it fails."""
  tnf_tm = TNF.to_TNF(tm, tnf_max_steps)
  if tnf_tm:
    return tnf_tm
  return tm

def permute_start_state(tm : Turing_Machine.Simple_Machine, tnf_max_steps : int) -> Iterator[Turing_Machine.Simple_Machine]:
  """Enumerate all TMs with the same ttable (just different start states)."""
  old_start_state = 0
  symbol_order = list(range(tm.num_symbols))
  for new_start_state in range(tm.num_states):
    state_order = list(range(tm.num_states))
    state_order[new_start_state] = old_start_state
    state_order[old_start_state] = new_start_state
    perm_tm = TNF.permute_table(tm, state_order, symbol_order)
    yield try_tnf(perm_tm, tnf_max_steps)

def write_perms(tm : Turing_Machine.Simple_Machine, writer, tnf_max_steps : int) -> None:
  for perm_tm in permute_start_state(tm, tnf_max_steps):
    writer.write_tm(perm_tm)


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
      write_perms(tm, writer, args.tnf_max_steps)
    else:
      with IO.StdText.Reader(sys.stdin) as reader:
        for tm_record in reader:
          write_perms(tm_record.tm(), writer, args.tnf_max_steps)

if __name__ == "__main__":
  main()