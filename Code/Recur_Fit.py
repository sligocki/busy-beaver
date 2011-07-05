#! /usr/bin/env python
#
# Recur_Fit.py
#
"""
For each input line, attempt to fit a recurrence relation to a list of integers
for that input line.  Integers are space separated.
"""

import sys, string, copy, numpy
from Recur import recur_fit

if __name__ == "__main__":
  for line in sys.stdin:
    sequence = map(int,line.split())
    recur_fit(sequence)
    print

