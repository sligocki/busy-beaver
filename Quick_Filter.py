#! /usr/bin/env python

import time
from sys import argv
import IO, Macro_Simulator
from Macro_Simulator import HALT_STATE, INF

filename = argv[1]
macro_size = int(argv[2])
delta_time = int(argv[3])
delta_steps = int(argv[4])

i = 0
inf_list = []
halt_list = []
unknown_list = []
while True:
  try:
    TTable = IO.load_TTable_filename(filename, i)
  except:
    break
  print i,
  sim = Macro_Simulator.Macro_Simulator()
  sim.init_new(TTable, macro_size)

  end_time = time.time() + delta_time
  while time.time() < end_time and sim.state not in (HALT_STATE, INF):
    sim.run(delta_steps)
  if sim.state == INF:
    print "Inf"
    inf_list.append(i)
  elif sim.state == HALT_STATE:
    print "Halt"
    halt_list.append(i)
  else:
    print "Unknown"
    unknown_list.append(i)
  i += 1

print
print len(inf_list), "Inf:", inf_list
print len(halt_list), "Halt:", halt_list
print len(unknown_list), "Unknown:", unknown_list
