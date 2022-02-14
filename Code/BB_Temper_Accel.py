#! /usr/bin/env python3
#
# BB_Temper_Accel.py
#
"""
Experiments using parallel tempering to get Busy Beaver candidates, i.e.
search for a halting TM with maximum steps or non-zero tape entries.
"""

import math

from PT import PT
from BB_Anneal_Accel import TM_Object
import time, getopt, sys

def optimize(Ti, Tf, pt_loops, n, seed, print_freq, steps, time, states, symbols):
  """Temperatures Ti to Tf spaced so that 1/T are uniform.
     "loops" iterations through PT alg, with n replicas. ..."""

  # Inverse temperatures
  # Bi = 1/Ti; Bf = 1/Tf
  # B = [Bi + (Bf - Bi)*k/(n-1) for k in range(n)]

  LTi = math.log(Ti)
  LTf = math.log(Tf)
  LT = [LTi + (LTf - LTi)*k/(num-1) for k in range(num)]
  B = [1.0/math.exp(LT[k]) for k in range(num)]

  obj = TM_Object(states, symbols, steps, time, seed)
  C = [obj.init_config() for i in range(n)]
  energy_func = lambda tm: obj.energy_func(tm)
  return PT(B, obj.next_config, energy_func, C, pt_loops, print_freq)


def usage():
  print("Usage:  BB_Temper_Accel.py [--help] [--T0=] [--Tf=] [--iter=] [--num=] [--seed=] [--freq=] [--steps=] [--time=] [--states=] [--symbols=]")

if __name__ == "__main__":
  states  = 5
  symbols = 2

  T0   = 100.0
  Tf   =   0.1

  loops = 1000000000
  num = 12

  seed = int(1000*time.time())

  freq = 100000

  steps = 1000000
  time  = 30  # Seconds

  try:
    opts, args = getopt.getopt(sys.argv[1:],"", \
                               [                \
                                "help",         \
                                "T0=",          \
                                "Tf=",          \
                                "iter=",        \
                                "num=",         \
                                "seed=",        \
                                "freq=",        \
                                "steps=",       \
                                "time=",        \
                                "states=",      \
                                "symbols="      \
                               ]                \
                              )
  except getopt.GetoptError:
    usage()
    sys.exit(1)

  for opt, arg in opts:
    if opt == "--help":
      usage()
      sys.exit(0)
    if opt == "--T0":
      T0 = float(arg)
    if opt == "--Tf":
      Tf = float(arg)
    if opt == "--iter":
      iter = int(arg)
    if opt == "--num":
      num = int(arg)
    if opt == "--seed":
      seed = int(arg)
    if opt == "--freq":
      freq = int(arg)
    if opt == "--steps":
      steps = int(arg)
    if opt == "--time":
      time = int(arg)
    if opt == "--states":
      states = int(arg)
    if opt == "--symbols":
      symbols = int(arg)

  print("BB_Temper_Accel.py --T0=%f --Tf=%f --iter=%d --num=%d --seed=%s --freq=%d --steps=%d --time=%d --states=%d --symbols=%d" % \
        (T0, Tf, loops, num, seed, freq, steps, time, states, symbols))
  print()

  res = optimize(T0, Tf, loops, num, seed, freq, steps, time, states, symbols)
  print([x[1] for x in res])
  print()
  for k in range(2):
    for x in range(X):
      for y in range(Y):
        print(('X' if C[k][0][x][y] else ' '), end=' ')
      print()
    print()

