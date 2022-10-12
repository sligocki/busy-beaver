"""
Look at n-gram entropy for TMs as a heuristic to classify their behavior.

An n-gram means a block/sequence of n symbols on the tape.
n-gram entropy is a measure of how random (high entropy) to predictable (low entropy) these n-grams are.

In this program we specifically look at the entropy of n-grams around the TM head over the course of many steps.
"""

import argparse
import collections
import math
from pathlib import Path

import Direct_Simulator
import IO
from Macro import Turing_Machine


def extract_window(sim, window_size : int):
  # window is centered on TM head.
  start = sim.tape.position - (window_size // 2)
  end = start + window_size
  tape_window = tuple(sim.tape.read(pos) for pos in range(start, end))
  return (sim.state, tape_window)

def entropy(counts) -> float:
  total = sum(counts.values())
  freqs = [count / total for count in counts.values()]
  return sum(-p * math.log2(p) for p in freqs)

def window_entropy(tm, window_size : int, num_samples : int):
  sim = Direct_Simulator.DirectSimulator(tm)
  # Skip ahead to avoid startup behavior which is often different from later
  # common runtime behavior.
  sim.seek(num_samples)

  trans_counts = collections.Counter()
  window_counts = collections.Counter()
  for _ in range(num_samples):
    sim.step()
    trans = (sim.state, sim.tape.read())
    trans_counts[trans] += 1
    window = extract_window(sim, window_size)
    window_counts[window] += 1

  return entropy(trans_counts), entropy(window_counts)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("infile", type=Path)
  parser.add_argument("--window-size", type=int, default=5)
  parser.add_argument("--num-samples", type=int)
  args = parser.parse_args()

  if not args.num_samples:
    # Large enough that we would expect to see every possible window 100x times
    # if they were completely random.
    # NOTE: This hardcodes num_states = 5 an num_symbols = 2.
    num_possible_windows = 5 * 2**args.window_size
    args.num_samples = 100 * num_possible_windows

  with IO.Reader(args.infile) as reader:
    for tm_record in reader:
      trans_h, window_h = window_entropy(tm_record.tm(),
                                         args.window_size, args.num_samples)
      # The average increase in entropy from each additional symbol added.
      h_per_symbol = (window_h - trans_h) / (args.window_size - 1)
      print(f"{tm_record.ttable_str()}  {h_per_symbol:10.6f} {trans_h:10.6f} {window_h:10.6f}")

if __name__ == "__main__":
  main()
