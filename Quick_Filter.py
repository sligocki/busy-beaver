#! /usr/bin/env python

import time, sys
import IO
import Macro_Simulator_Dev as Macro_Simulator
from Macro_Simulator import HALT_STATE, INF

filename = sys.argv[1]
macro_size = int(sys.argv[2]) - 1
delta_time = int(sys.argv[3])
delta_steps = int(sys.argv[4])

unknown = eval(sys.argv[5])

inf_list = []
halt_list = []
try:
  while not (inf_list or halt_list):
    infile = open(filename, "r")
    macro_size += 1
    print "Macro Size:", macro_size
    last_i = 0
    inf_list = []
    halt_list = []
    unknown_list = []
    max_speed = (0, 0)
    for i in unknown:
      TTable = IO.load_TTable(infile, i - last_i)
      last_i = i
      print i,
      sim = Macro_Simulator.Macro_Simulator()
      sim.init_new(TTable, macro_size, True)

      end_time = time.time() + delta_time
      while time.time() < end_time and sim.state not in (HALT_STATE, INF):
        sim.run(delta_steps)
      t = time.time() - end_time + delta_time
      if sim.state == HALT_STATE:
        print "Halt", sim.cur_step_num, sim.tape.get_nonzeros()
        halt_list.append(i)
      elif sim.state == INF:
        print "Inf", t
        inf_list.append(i)
      else:
        try:
          speed = sim.cur_step_num / t
        except OverflowError:
          speed = -1
        print "Unknown", speed
        unknown_list.append(i)
        if speed > max_speed[0]:
          max_speed = (speed, i)
    infile.close()
except Exception, e:
  print e

print
print "Macro Size:", macro_size
print len(halt_list), "Halt:", halt_list
print len(inf_list), "Inf:", inf_list
print len(unknown_list), "Unknown:", unknown_list
print "Max Speed:", max_speed
