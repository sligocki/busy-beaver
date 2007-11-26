#! /usr/bin/env python
#
# Balance_Parallel.py
#
# Balance the unknown machines resulting from a parallel run of "Enumerate..."
#

import sys, random

# Command line interpretter code
if __name__ == "__main__":
  base = sys.argv[1]
  num = int(sys.argv[2])

  lines = []

  for i in xrange(num):
    filename = base + (".%05d" % i) + ".unknown"

    file = open(filename,"r")
    lines.extend(file.readlines())
    file.close()

    if i % 100 == 0:
      print i,len(lines)
      sys.stdout.flush()

  random.seed()
  random.shuffle(lines)

  numLines = len(lines)
  numPer   = float(numLines)/float(num)

  print numLines,numPer
  sys.stdout.flush()

  for i in xrange(num):
    start = int( i   *numPer)
    end   = int((i+1)*numPer)

    filename = base + (".%05d" % i) + ".unknown.new"

    file = open(filename,"w")
    file.writelines(lines[start:end])
    file.close()

    if i % 100 == 0:
      print i,start,end
      sys.stdout.flush()
