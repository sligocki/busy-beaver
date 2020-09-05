#!/usr/bin/env python3
"""
Merge a collection of steps_example output files to find the Lazy Beaver
after a parallel run.
"""

import argparse
import itertools
import sys


parser = argparse.ArgumentParser()
parser.add_argument("steps_example_files", nargs="+")
args = parser.parse_args()


steps_example = {}
for filename in args.steps_example_files:
  with open(filename, "r") as infile:
    for line in infile:
      steps, tm = line.split("\t")
      steps_example[int(steps)] = tm.strip()

for n, tm in sorted(steps_example.items()):
  sys.stdout.write("{}\t{}\n".format(n,tm))

smallest_holes = []
for n in itertools.count(1):
  if n not in steps_example:
    smallest_holes.append(n)
    if len(smallest_holes) >= 20:
      break
print("Min un-attained steps:", *smallest_holes, file=sys.stderr)
