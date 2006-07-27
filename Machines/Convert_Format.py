#! /usr/bin/env python

import sys, string

for infilename in sys.argv[1:]:
  infile = open(infilename, "r")

  line = infile.readline()
  if line[0:11] == "%% Format: ":
    format = line[11:-1]
  else:
    # TODO: Attempt to decipher format (Example Ligocki1 or Ligocki2/Default)
    sys.stderr.write("No format tag\n")
    continue

  if format == "Marxen2":
    states = string.ascii_uppercase
    symbols = string.digits
    directions = "LR"
    while line[0:3] != "A: ":
      line = infile.readline()
    state = 0
    TTable = []
    while line:
      temp = []
      for rule in line.split()[1:]:
        assert len(rule) is 3
        if rule[0] == "Z":
          state = -1
        else:
          state = states.find(rule[0])
        symbol = symbols.find(rule[1])
        dir = directions.find(rule[2])
        temp.append((symbol, dir, state))
      TTable.append(temp)
      line = infile.readline()
  else:
    sys.stderr.write("Improper format (%s)\n" % repr(format))
    continue

  outfilename = infilename[:-4]
  outfile = open(outfilename, "w")
  outfile.write(repr(TTable))
