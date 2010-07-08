#! /usr/bin/env python

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
      elif cell[2] == -1:
        s += "%c%cZ " % (symbols[cell[0]], dirs[cell[1]])
      else:
        s += "%c%c%c " % (symbols[cell[0]], dirs[cell[1]], states[cell[2]])
    s += " "
  return s

# Main script
import sys

filename = sys.argv[1]
if filename == "-":
  infile = sys.stdin
else:
  infile = open(filename, "r")

for line in infile:
  table = get_ttable(line)
  parts = line.split()
  try:
    ones = int(parts[6])
    steps = int(parts[7])
    print display_ttable(table), "# ",ones, "", steps, "", long_to_eng_str(ones,1,3), "", long_to_eng_str(steps,1,3)
  except:
    print display_ttable(table)
