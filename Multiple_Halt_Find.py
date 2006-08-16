#! /usr/bin/env python

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
import sys

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
print
for n in range(max(count.keys()) + 1):
  print "Machines with %d halts: %d" % (n, count.get(n, 0))
