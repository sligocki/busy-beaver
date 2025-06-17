#! /usr/bin/env python3
"""
Decider for Translated Cyclers (Lin Recurrence) using the Transcript algorithm:
https://www.sligocki.com/2024/06/12/tm-transcripts.html

See also: Lin_Recur_Detect.py for the traditional algorithm.
"""


import argparse
from dataclasses import dataclass
import math
import time

import IO
from Transcript import Transcript, TM


@dataclass(frozen=True)
class TCResult:
  decided: bool
  start_step: int
  period: int

def has_blank(ts: Transcript, start: int, delta: int) -> bool:
  """Does the sequence ts.history[start:start+delta] have any "blank" (not written) symbols?"""
  for step in range(start, start+delta):
    if ts.history[step].symbol.is_blank:
      return True
  return False


def find_cycle_not_min(tm: TM, max_steps: int, verbose: bool = False) -> TCResult:
  """Search for a Translated Cycle without knowing period or start step.
  If cycle found, start_step may not be minimal.
  """
  ts = Transcript(tm)
  ts.extend_history(1)

  while len(ts) < max_steps:
    ref_step = len(ts)
    ts.extend_history(ref_step)
    if verbose:
      print(f"Simulated {len(ts):_d} steps ({time.process_time():_.1f}s)")

    # Search for a delta such that
    #   ts.history[ref_step:ref_step+delta] == ts.history[ref_step+delta:ref_step+delta*2]
    match_deltas : list[int] = []
    for step in range(ref_step + 1, ref_step * 2):
      new_deltas : list[int] = []
      # Keep checking all matching deltas
      for delta in match_deltas + [step - ref_step]:
        if ts.history[step] == ts.history[step - delta]:
          if step - ref_step >= delta * 2:
            if has_blank(ts, ref_step, delta):
              # Success, we found a repeat including 
              return TCResult(True, ref_step, delta)
          else:
            new_deltas.append(delta)
      match_deltas = new_deltas

  return TCResult(False, 0, 0)

def minimize_cycle(tm: TM, result: TCResult) -> TCResult:
  """Take result from find_cycle_not_min() and minimize the start_step."""
  if not result.decided:
    return result

  # Align start_step (upper bound) with period to simplify calculation of `cycle_step`
  start_step = (result.start_step // result.period + 1) * result.period
  assert start_step % result.period == 0

  ts = Transcript(tm)
  ts.extend_history(start_step + result.period)

  # Load an example of the cycle (from an arbitrary starting point).
  cycle = ts.history[start_step:]
  assert len(cycle) == result.period

  num_match = 0
  for step in range(start_step + result.period):
    cycle_step = step % result.period
    if ts.history[step] == cycle[cycle_step]:
      num_match += 1
      if num_match == result.period:
        return TCResult(True, step - result.period + 1, result.period)
    else:
      num_match = 0

  raise ValueError("TM did not cycle")

def find_min_cycle(tm: TM, max_steps: int, verbose: bool) -> TCResult:
  result = find_cycle_not_min(tm, max_steps, verbose)
  result = minimize_cycle(tm, result)
  return result


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm", help="Turing Machine or file or file:record_num (0-indexed).")
  parser.add_argument("--max-steps", type=int, default = math.inf)
  args = parser.parse_args()

  tm = IO.get_tm(args.tm)
  result = find_min_cycle(tm, args.max_steps, verbose=True)

  print(result)

if __name__ == "__main__":
  main()
