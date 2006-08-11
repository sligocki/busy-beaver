#! /usr/bin/env python

from __future__ import division

import sys, math, IO
from Turing_Machine import Turing_Machine
from Turing_Machine_Sim_Py import Turing_Machine_Sim

def get_times(ttable, steps=10000):
  """Records time machine takes to use n space on tape."""
  machine = Turing_Machine(ttable)
  sim = Turing_Machine_Sim(machine)
  times = [0, 0]
  bound = [sim.position, sim.position]
  while sim.step_num < steps:
    sim.step()
    if sim.position < bound[0]:
      times.append(sim.step_num)
      bound[0] -= 1
    elif sim.position > bound[1]:
      times.append(sim.step_num)
      bound[1] += 1
  return times

# Main script
if len(sys.argv) >= 3:
  line = int(sys.argv[2])
else:
  line = 1

ttable = IO.load_TTable_filename(sys.argv[1], line)

seq = get_times(ttable)[2:]
print seq
print
print [x / n for x, n in zip(seq, range(len(seq))) if n]
print
print [x / n**2 for x, n in zip(seq, range(len(seq))) if n]
print
log = [math.log(x, 2) for x, n in zip(seq, range(len(seq))) if x]
print log
print [y - x for x, y in zip(log, log[1:])]
print
print [y / x for x, y in zip(seq, seq[1:]) if x]
print
print [y - x for x, y in zip(seq, seq[1:])]
