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

steps_example_sorted = sorted(steps_example.items())

for n, tm in steps_example_sorted:
  sys.stdout.write("{}\t{}\n".format(n,tm))

smallest_holes = []
total_holes = 0
for i in range(len(steps_example_sorted)-1):
  for j in range(steps_example_sorted[i][0]+1,steps_example_sorted[i+1][0]):
    total_holes += 1
    if len(smallest_holes) < 20:
      smallest_holes.append(j)

print("Min un-attained steps:", *smallest_holes, file=sys.stderr)
print("Total un-attained steps:", total_holes, file=sys.stderr)
