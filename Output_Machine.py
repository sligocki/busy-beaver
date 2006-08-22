#! /usr/bin/env python

import string

def get_ttable(string):
  start = string.find("[[")
  end = string.rfind("]]") + len("]]")
  return eval(string[start:end])

def display_ttable(table):
  symbols = string.digits
  dirs = "LR"
  states = string.ascii_uppercase[:7]
  s = ""
  for row in table:
    for cell in row:
      if cell[0] == -1:
        s += "--- "
      elif cell[2] == -1:
        s += "%c%cH " % (symbols[cell[0]], dirs[cell[1]])
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
  parts = line.split()
  #ones = int(parts[6])
  #steps = int(parts[7])
  table = get_ttable(line)
  print display_ttable(table)#, ones, "", steps
