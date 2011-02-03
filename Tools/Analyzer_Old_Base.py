#! /usr/bin/env python
import math

from Format_Old_Base import FIELD

def get_max(lines):
  max_steps = max_symbols = 0
  num_lines = 0
  for line in lines:
    max_steps = max(max_steps, FIELD.STEPS(line))
    max_symbols = max(max_symbols, FIELD.SYMBOLS(line))
    num_lines += 1
  return max_steps, max_symbols, num_lines

def count_lines(curfile):
  num_lines = 0
  for line in curfile:
    num_lines += 1
  return num_lines

if __name__ == "__main__":
  import sys

  usage = "Analyzer_Old_Base.py basename"

  # Load command line args
  try:
    basename = sys.argv[1]
  except IndexError:
    print usage
    sys.exit(1)

  # Open BB data files
  try:
    halt_file = file(basename + ".halt", "r")
    infinite_file = file(basename + ".infinite", "r")
    undecided_file = file(basename + ".undecided", "r")
    unknown_file = file(basename + ".unknown", "r")
  except IOError:
    print usage
    print "Error: basename (%s) not valid." % basename
    sys.exit(1)

  # Get Stats
  # Get max stats for halting machines
  max_steps, max_symbols, num_halt = get_max(halt_file)
  # Get number of machines in each category
  num_infinite = count_lines(infinite_file)
  num_undecided = count_lines(undecided_file)
  num_unknown = count_lines(unknown_file)
  num_total = num_halt + num_infinite + num_undecided + num_unknown
  # Derive percentages in each category
  percent_halt = 100.0*float(num_halt) / num_total
  percent_infinite = 100.0*float(num_infinite) / num_total
  percent_undecided = 100.0*float(num_undecided) / num_total
  percent_unknown = 100.0*float(num_unknown) / num_total

  digits = int(math.ceil(math.log10(num_total)))
  format_string = "%%%dd" % digits

  print basename
  print ""
  print "Max Steps         = ", max_steps
  print "Max Symbols       = ", max_symbols
  print ""
  print "Number Total      = ", format_string % num_total
  print "Number Halt       = ", format_string % num_halt
  print "Number Infinite   = ", format_string % num_infinite
  print "Number Undecided  = ", format_string % num_undecided
  print "Number Unknown    = ", format_string % num_unknown
  print ""
  print "Percent Halt      =", "%10.6f" % percent_halt
  print "Percent Infinite  =", "%10.6f" % percent_infinite
  print "Percent Undecided =", "%10.6f" % percent_undecided
  print "Percent Unknown   =", "%10.6f" % percent_unknown
