#! /usr/bin/env python
#
# Output_Machine.py
#
"""
Library for writing Turing Machine transition tables in a human readable format.

As an executable this converts from IO_old format to human readable output
(Deprecated).  Now it is used by IO to write the stored notation.
"""

import math
import string

def long_to_eng_str(number,left,right):
  """Represent a Long in scientific notation."""
  if number != 0:
    expo = int(math.log(abs(number))/math.log(10))
    number_str = str(int(number / 10**(expo-right)))

    if number < 0:
      return "-%s.%se+%d" % (number_str[1     :1+left      ],
                             number_str[1+left:1+left+right],
                             expo)
    else:
      return "%s.%se+%d" % (number_str[0     :0+left      ],
                            number_str[0+left:0+left+right],
                            expo)
  else:
    return "0.%se+00" % ("0" * right)

def get_ttable(string):
  """Load ttable from a string."""
  start = string.find("[[")
  end = string.rfind("]]") + len("]]")
  return eval(string[start:end])

def display_ttable(table):
  """Pretty print the ttable."""
  symbols = string.digits
  dirs = "LRS"
  states = string.ascii_uppercase
  s = ""
  for row in table:
    for cell in row:
      if cell[0] == -1:
        s += "--- "
      else:
        symbol = symbols[cell[0]]
        dir = dirs[cell[1]]
        # Note: we use python trickyness to map state = -1 -> "Z"
        state = states[cell[2]]
        s += "%c%c%c " % (symbol, dir, state)
    s += " "
  return s.strip()

def display_line(line):
  """Print ttable and other info from line of log file."""
  table = get_ttable(line)
  parts = line.split()
  try:
    ones = int(parts[6])
    steps = int(parts[7])
    print display_ttable(table), "# ",ones, "", steps, "", long_to_eng_str(ones,1,3), "", long_to_eng_str(steps,1,3)
  except:
    print display_ttable(table)

if __name__ == "__main__":
  import sys

  if not (2 <= len(sys.argv) <= 3):
    print >>sys.stderr, "usage: Output_Machine.py filename [line-num]"
    sys.exit(1)
  filename = sys.argv[1]
  if filename == "-":
    infile = sys.stdin
  else:
    infile = open(filename, "r")

  if len(sys.argv) >= 3:
    line_num = int(sys.argv[2])
    for n, line in enumerate(infile):
      if n == line_num - 1:  # line_num counds from 1
        display_line(line)
        break
  else:
    for line in infile:
      display_line(line)
