#! /usr/bin/env python

from __future__ import division

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
import sys, math

infile = open(sys.argv[1], "r")

count = {}
for line in infile:
  ttable = get_ttable(line)
  halts = count_halts(ttable)
  count[halts] = count.get(halts, 0) + 1
  if halts > 1:
    # Print the multiple ones
    print line,

# Output stats
total_count = sum(count.values())
width = int(math.log(total_count, 10)) + 2
print
for n in range(max(count.keys()) + 1):
  print ("%"+`width`+"d machines with %d halts (%.1f%%)") % (count.get(n, 0), n, count.get(n, 0) * 100 / total_count)
print
print ("%"+`width`+"d total machines") % total_count
