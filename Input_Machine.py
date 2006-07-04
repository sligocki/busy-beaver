#! /usr/bin/env python

import string

num_states = int(raw_input("Num States? "))
num_symbols = int(raw_input("Num Symbols? "))
name = raw_input("Name? ")

format = """symbol-dir-state (e.g. 2RA or 210)
            symbol must be an integer 0-9 less than num_symbols
            dir must be R, r, 1 for right or L, l, 0 for left
            state must be letter A-G or integer 0-9 less than num_states (Halt = H or - or Z)"""

TTable = [None] * num_states
for state in range(num_states):
  TTable[state] = [None] * num_symbols
  for symbol in range(num_symbols):
    have_input = False
    while not have_input:
      temp = raw_input("State %d, Symbol %d: " % (state, symbol))
      # Get Symbol
      try:
        next_symbol = int(temp[0])
      except ValueError:
        print "Bad Symbol input, please enter state information in this form:"
        print format
        continue
      # Get Dir
      if   temp[1] in "Rr1": next_dir = 1
      elif temp[1] in "Ll0": next_dir = 0
      else:
        print "Bad Direction input, please enter state information in this form:"
        print format
        continue
      # Get State
      if temp[2] in "HhZz-": next_state = -1
      elif temp[2] in string.ascii_lowercase: next_state = string.ascii_lowercase.find(temp[2])
      elif temp[2] in string.ascii_uppercase: next_state = string.ascii_uppercase.find(temp[2])
      elif temp[2] in string.digits: next_state = string.digits.find(temp[2])
      else:
        print "Bad State input, please enter state information in this form:"
        print format
        continue
      TTable[state][symbol] = (next_symbol, next_dir, next_state)
      have_input = True

filename = "Machines/%dx%d-%s.bb" % (num_states, num_symbols, name)
table_file = open(filename, "w")
table_file.write(`TTable`)
table_file.close()
print "Successfully wrote %s" % filename
