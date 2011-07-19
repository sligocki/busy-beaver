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
  # Read each series - a line of input
  for line in sys.stdin:
    # Generate the series by splitting the line and making everything
    # an integer
    series = map(int,line.split())

    # Attempt to get a recurrence relation for the series (and print
    # it out)
    recur_fit(series)

    # Put blank lines between series
    print

