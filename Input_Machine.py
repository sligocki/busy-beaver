#! /usr/bin/env python

import string

symbols = string.digits
dirs = "LR"
states = string.ascii_uppercase[:7]
halt_state = "HZ"

def get_from_list(l1, l2):
  for item in l1:
    pos = l2.find(item)
    if pos != -1:
      return pos
  return -1

def get_alpha(cell):
  next_symbol = get_from_list(cell, symbols)
  if next_symbol == -1:
    return False
  next_dir = get_from_list(cell, dirs)
  if next_dir == -1:
    return False
  next_state = get_from_list(cell, states)
  if next_state == -1:
    if get_from_list(cell, halt_state) == -1:
      return False
    else:
      next_state = -1
  return next_symbol, next_dir, next_state

def get_numeric(cell):
  try:
    next_symbol = int(cell[0])
    next_dir = int(cell[1])
    next_state = int(cell[2])
    return next_symbol, next_dir, next_state
  except ValueError:
    return False

if __name__ == "__main__":
  num_states = int(raw_input("Num States? "))
  num_symbols = int(raw_input("Num Symbols? "))
  name = raw_input("Name? ")

  format = """Numberic: symbol-dir-state (e.g. 210 for 2RA, 11- for 1RH)
  or any order with letters (e.g. RA2 or A2R or ... for 2RA)
  symbol must be an integer 0-9 less than num_symbols
  dir must be R for right or L for left
  state must be letter A-G less than num_states (Halt = H or Z)"""

  parts = []
  TTable = [None] * num_states
  for state in range(num_states):
    TTable[state] = [None] * num_symbols
    for symbol in range(num_symbols):
      have_input = False
      while not have_input:
        if not parts:
          temp = raw_input("State %c, Symbol %d: " % (state+ord("A"), symbol))
          temp = temp.strip().upper()
          parts = temp.split()
        if len(parts[0]) != 3:
          print format
          parts = []
          continue
        result = get_alpha(parts[0])
        if not result:
          result = get_numeric(parts[0])
        if not result:
          print "Bad Symbol input, please enter state information in this form:"
          print format
          parts = []
          continue
        TTable[state][symbol] = result
        have_input = True
        del parts[0]
    print

  filename = "Machines/%dx%d-%s.bb" % (num_states, num_symbols, name)
  table_file = open(filename, "w")
  table_file.write(`TTable`+'\n')
  table_file.close()
  print "Successfully wrote %s" % filename
