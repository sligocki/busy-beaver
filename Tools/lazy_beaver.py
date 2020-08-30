#!/usr/bin/env python3

import sys

nextSteps = 2

found = False
for line in sys.stdin:
  if line != "Halt\n":
    steps = int(line)

    if steps == nextSteps:
      nextSteps = steps + 1
    elif steps > nextSteps:
      print("Lazy Beaver:",nextSteps)
      found = True
      break

if not found:
  print("Lazy Beaver (max):",steps+1)
