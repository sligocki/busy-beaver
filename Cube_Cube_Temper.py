#! /usr/bin/env python

from PT import PT
from Cube_Cube_Anneal import Cube_Object
import time, getopt, sys

def optimize(Ti, Tf, pt_loops, num, seed, print_freq, m, n, sigma):
  """Temperatures Ti to Tf spaced so that 1/T are uniform.
     "loops" iterations through PT alg, with n replicas. ..."""
  import math

  # Inverse temperatures
  # Bi = 1/Ti; Bf = 1/Tf
  # B = [Bi + (Bf - Bi)*k/(num-1) for k in range(num)]

  LTi = math.log(Ti)
  LTf = math.log(Tf)
  LT = [LTi + (LTf - LTi)*k/(num-1) for k in range(num)]
  B = [1.0/math.exp(LT[k]) for k in range(num)]
  
  obj = Cube_Object(m, n, sigma, seed)
  C = [obj.init_config() for i in range(num)]
  energy_func = lambda cube: obj.energy_func(cube)
  return PT(B, obj.next_config, energy_func, C, pt_loops, print_freq)


def usage():
  print "Usage:  Cube_Cube_Temper.py [--help] [--T0=] [--Tf=] [--iter=] [--num=] [--seed=] [--freq=] [--m=] [--n=]"

if __name__ == "__main__":
  m = 2
  n = 3

  T0   = 1.000
  Tf   = 0.001

  loops = 1000000000
  num = 12

  seed = long(time.time())

  freq = 100000

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
                                "m=",           \
                                "n="            \
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
      iter = long(arg)
    if opt == "--num":
      num = long(arg)
    if opt == "--seed":
      seed = long(arg)
    if opt == "--freq":
      freq = long(arg)
    if opt == "--m":
      m = int(arg)
    if opt == "--n":
      n = int(arg)

  print "Cube_Cube_Temper.py --T0=%f --Tf=%f --iter=%d --num=%d --seed=%s --freq=%d --m=%d --n=%d" % \
        (T0, Tf, loops, num, seed, freq, m, n)
  print
  
  res = optimize(T0, Tf, loops, num, seed, freq, m, n, 1.0)
  print [x[1] for x in res]
  print
  for k in range(2):
    for x in range(X):
      for y in range(Y):
        print ('X' if C[k][0][x][y] else ' '),
      print
    print
