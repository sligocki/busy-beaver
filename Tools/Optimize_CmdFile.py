#! /usr/bin/env python
#
# Optimize_Cmdfile.py
#
"""
Use log files to produce optimized command files by determining TMs identified
per second for each filter and sorting by that rate.
"""

def getrate(x):
  return x[1][2]

import sys,string,operator

filters = {}

unknowns = 0

for line in sys.stdin:
  pieces = string.split(line,"|")
  
  if len(pieces) >= 5:
    number = string.split(pieces[5])

    commandline = pieces[2]
    splitline = string.split(commandline)

    command = splitline[0]

    runtime = int(pieces[4])
    delta_unknowns = int(number[3])

    unknowns += delta_unknowns

    if command not in ['Enumerate.py', 'Assign_Undecideds_Filter', 'mpirun']:
      if commandline in filters:
        filters[commandline][0] += -delta_unknowns
        filters[commandline][1] += runtime
      else:
        filters[commandline] = [-delta_unknowns,runtime]

for (filter,stats) in filters.items():
  delta_unknowns = stats[0]
  runtime = stats[1]

  if runtime == 0:
    stats.append(0.0)
  else:
    stats.append(float(delta_unknowns)/runtime)

# new_order = sorted(filters, key=filters.get, reverse=True)
new_order = sorted(iter(filters.items()), key=getrate, reverse=True)

for filter in new_order:
  print(filter[0])
