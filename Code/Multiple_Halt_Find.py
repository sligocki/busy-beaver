#! /usr/bin/env python
"""
Find how many halt (or undefined cells) all TMs in a file have.

Prints out all TMs with more than one halt state and lists the number of TMs that
have each number of halts.
"""

from __future__ import division
import math
import sys

from IO import IO

def get_ttable(string):
  start = string.find("[[")
  end = string.rfind("]]") + len("]]")
  return eval(string[start:end])

def count_halts(ttable):
  halts = 0
  for row in ttable:
    for cell in row:
      if cell[2] == -1:
        halts += 1
  return halts

# Main
infile = open(sys.argv[1], "r")
io = IO(infile, sys.stdout)

count = {}
for io_record in io:
  halts = count_halts(io_record.ttable)
  count[halts] = count.get(halts, 0) + 1
  if halts > 1:
    # Print the multiple ones
    io.write_record(io_record)

# Output stats
total_count = sum(count.values())
width = int(math.log(total_count, 10)) + 2

print
for n in range(1, max(count.keys()) + 1):
  print ("%"+`width`+"d machines with %d halts (%.1f%%)") % (
    count.get(n, 0), n, count.get(n, 0) * 100 / total_count)
print
print ("%"+`width`+"d total machines") % total_count
