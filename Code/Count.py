#! /usr/bin/env python3
"""
Count the number of distinct TM represented by machines in tree-normal-form
with the restriction that A0->1RB and Halt=1RH and either:
 A) Exactly 1 halt if allow-no-halts is False or
 B) 1 or fewer halts if allow-no-halts is True

For the entire space of Q-state, S-symbol TMs, the number of distinct TM's is:
 A) (QS-1) * (2QS)^(QS-2)
 B) (QS-1) * (2QS)^(QS-2) + (2QS)^(QS-1)
"""

import argparse

import IO
from Macro import Turing_Machine
from pathlib import Path


def fact2(n, m):
  """Computes n!/m! = n*(n-1)*...*(m+1)"""
  assert n >= m >= 0
  if n == m:
    return 1
  else:
    return n*fact2(n-1, m)


def count(tm : Turing_Machine.Simple_Machine,
          allow_no_halt : bool) -> int:
  """Count the number of TM's that are equivalent to this one.
     With the restriction that A0->1RB and Halt=1RH."""
  num_undefs = 0
  has_halt = False
  max_symbol = 0
  max_state = 0
  # Get stats.  Number of undefined transitions, whether there is a halt
  # and the max-symbol/states
  for state_in in range(tm.num_states):
    for symbol_in in range(tm.num_symbols):
      trans = tm.get_trans_object(symbol_in = symbol_in, state_in = state_in)
      if trans.condition == Turing_Machine.UNDEFINED:
        num_undefs += 1
      elif trans.condition == Turing_Machine.HALT:
        has_halt = True
      else:
        assert trans.condition == Turing_Machine.RUNNING, trans.condition
        max_symbol = max(max_symbol, trans.symbol_out)
        max_state = max(max_state, trans.state_out)
  num_symbols_used = max_symbol + 1
  num_states_used = max_state + 1
  # Count the number of permutations of symbols/states possible
  num_tms = fact2(tm.num_symbols - 2, tm.num_symbols - num_symbols_used) \
          * fact2(tm.num_states  - 2, tm.num_states  - num_states_used)
  if has_halt:
    # All possible assignments of trans for each undefined transition.
    # num_dirs * num_states * num_symbols for each trans.
    num_tms *= (2*tm.num_states*tm.num_symbols)**num_undefs
  else:
    this_mult = 0
    if num_undefs >= 1:
      # Count with 1 halt added.
      this_mult += num_undefs * (2*tm.num_states*tm.num_symbols)**(num_undefs - 1)
    if allow_no_halt:
      # Count with 0 halts added.
      this_mult += (2*tm.num_states*tm.num_symbols)**num_undefs
    num_tms *= this_mult
  return num_tms


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm_file", nargs="+", type=Path)
  parser.add_argument("--allow-no-halt", action="store_true")
  args = parser.parse_args()

  total = 0
  for filename in args.tm_file:
    with IO.Reader(filename) as reader:
      for tm_record in reader:
        total += count(tm_record.tm(), args.allow_no_halt)

  print(total)

if __name__ == "__main__":
  main()
