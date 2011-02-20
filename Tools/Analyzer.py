#! /usr/bin/env python
"""
Analyze a turing machine file.

Counts the number of Halting, Infinite, Unknown and Undefined machines.
Also finds maximum steps and symbols.
"""

import math
import sys

# Add ../Code/ to python path so we can load Common and IO
parent_dir = sys.path[0][:sys.path[0].rfind("/")]
sys.path.insert(1, parent_dir + "/Code/")

from Common import Exit_Condition
from IO import IO

usage = "Analyzer.py filename"

try:
  filename = sys.argv[1]
except:
  print usage
  sys.exit(1)

infile = file(filename, "r")

io = IO(infile, None)

num_total = 0
count = {Exit_Condition.HALT: 0,
         Exit_Condition.INFINITE: 0,
         Exit_Condition.UNDEF_CELL: 0,
         Exit_Condition.ERROR: 0,
         # Various Unknown types:
         Exit_Condition.UNKNOWN: 0,
         Exit_Condition.MAX_STEPS: 0,
         Exit_Condition.OVER_TAPE: 0,
         Exit_Condition.TIME_OUT: 0}
max_symbols = -1
max_steps = -1
for result in io.catch_error_iter():
  if result:
    num_total += 1
    count[result.category] += 1
    if result.category == Exit_Condition.HALT:
      symbols, steps = result.category_reason
      max_symbols = max(max_symbols, symbols)
      max_steps = max(max_steps, steps)

num_halt = count[Exit_Condition.HALT]
num_infinite = count[Exit_Condition.INFINITE]
num_unknown = sum(count[x] for x in Exit_Condition.UNKNOWN_SET)
num_undecided = count[Exit_Condition.UNDEF_CELL]
num_error = count[Exit_Condition.ERROR]

digits = int(math.ceil(math.log10(num_total)))
format_string = "%%%dd" % digits

print filename
print
print "Max Steps         = ", max_steps
print "Max Symbols       = ", max_symbols
print
print "Number Total      = ", format_string % num_total
print "Number Halt       = ", format_string % num_halt
print "Number Infinite   = ", format_string % num_infinite
print "Number Unknown    = ", format_string % num_unknown
print "Number Undecided  = ", format_string % num_undecided
print "Number Error      = ", format_string % num_error
print
print "Percent Halt      =", "%10.6f" % (100.0 * num_halt / num_total)
print "Percent Infinite  =", "%10.6f" % (100.0 * num_infinite / num_total)
print "Percent Unknown   =", "%10.6f" % (100.0 * num_unknown / num_total)
print "Percent Undecided =", "%10.6f" % (100.0 * num_undecided / num_total)
print "Percent Error     =", "%10.6f" % (100.0 * num_error / num_total)
