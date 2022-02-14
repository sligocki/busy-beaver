#! /usr/bin/env python3
#
# Random_Sample.py
#
"""
Get a random sample from a very large set of machines.
"""

import sys, random

try:
  infilename = sys.argv[1]
  length = int(sys.argv[2])
  sample_size = int(sys.argv[3])
except:
  print("Random_Sample.py filename in_lines out_lines")
  sys.exit(1)
outfilename = infilename + ".sample"

# If your sample is too large this algorithm could take forever...
# This algorithm is only meant for much smaller samples.
assert sample_size <= length // 2

# Select random machines
sample_nums = random.sample(range(1, length+1), sample_size)
sample_nums.sort()

infile = open(infilename, "r")
outfile = open(outfilename, "w")
last = 0
for num, i in zip(sample_nums, list(range(len(sample_nums)))):
  #print num, i+1, "of", sample_size
  for j in range(num - last):
    line = infile.readline()
  outfile.write(line)
  last = num

infile.close()
outfile.close()
