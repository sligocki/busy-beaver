#! /usr/bin/env python3
"""Convert TMs from generic form to Lexicographic Normal Form."""

import argparse
import sys

import IO
from Macro import Turing_Machine
import TNF


def permute(old_tm, state_order, symbol_order):
  # L < R
  swap_dirs = (old_tm.trans_table[state_order[0]][0].dir_out == Turing_Machine.RIGHT)
  perm_tm = TNF.permute_table(old_tm, state_order, symbol_order, swap_dirs)

  # Find new state number corresponding to start state (old 0) and symbol.
  new_start_state = state_order.index(0)
  assert new_start_state != -1, state_order
  perm_tm.init_state = Turing_Machine.Simple_Machine_State(new_start_state)

  new_start_symb = symbol_order.index(0)
  assert new_start_symb != -1, symbol_order
  perm_tm.init_symbol = new_start_symb

  return perm_tm


def iter_perms(xs):
  if len(xs) <= 1:
    yield xs
  else:
    for i, x in enumerate(xs):
      for sub in iter_perms(xs[:i] + xs[i+1:]):
        yield [x] + sub


def brute_lnf(old_tm):
  """Calculate LNF using brute-force method."""
  best_str = old_tm.ttable_str()
  best_tm = old_tm
  for post_state_order in iter_perms(list(range(1, old_tm.num_states))):
    # Never change first state
    state_order = [0] + post_state_order
    for post_symbol_order in iter_perms(list(range(1, old_tm.num_symbols))):
      # Never change blank symbol
      symbol_order = [0] + post_symbol_order
      perm_tm = permute(old_tm, state_order, symbol_order)
      perm_str = perm_tm.ttable_str()
      # print(f" Debug: {state_order} / {perm_str}")
      if perm_str < best_str:
        best_str = perm_str
        best_tm = perm_tm
  return best_tm


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm", nargs="?",
                      help="Literal Turing Machine. If missing read from stdin.")
  args = parser.parse_args()

  with IO.StdText.Writer(sys.stdout) as writer:
    if args.tm:
      tm = IO.parse_tm(args.tm)
      new_tm = brute_lnf(tm)
      writer.write_tm(new_tm)
    else:
      with IO.StdText.Reader(sys.stdin) as reader:
        for tm_record in reader:
          new_tm = brute_lnf(tm_record.tm())
          writer.write_tm(new_tm)

if __name__ == "__main__":
  main()
