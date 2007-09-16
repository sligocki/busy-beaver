#! /usr/bin/env python
"""
A generalized Rupert problem computation using Simulated Annealing optimization.
"""

import random, copy, math, time, getopt, sys

import SA

class Cube_Object:
  def __init__(self,m,n,sigma,seed):
    self.random = random
    self.random.seed(seed)

    self.m = m
    self.n = n

    self.sigma = sigma

  def init_config(self):
    identity = [[(1 if i == j else 0) for j in xrange(0,self.n)] for i in xrange(0,self.n)]

    return identity

  def energy_func(self,cur_matrix):
    max_sum = 0

    for i in xrange(0,self.n):
      sum = 0

      for j in xrange(0,self.m):
        sum += abs(cur_matrix[i][j])

      if sum > max_sum:
        max_sum = sum

    # print cur_matrix
    # print max_sum
    # print ""

    return (max_sum,1.0/max_sum)

  def next_config(self,cur_matrix,T):
    """Mutate a single element of one transition."""
    new_matrix = copy.deepcopy(cur_matrix)

    ai = self.random.randrange(0,self.n)
    aj = self.random.randrange(0,self.n)

    if ai != aj:
      t = self.random.gauss(0.0,self.sigma*T)

      ct = math.cos(t)
      st = math.sin(t)

      for i in xrange(0,self.n):
        new_matrix[i][ai] =  ct * cur_matrix[i][ai] + st * cur_matrix[i][aj]
        new_matrix[i][aj] = -st * cur_matrix[i][ai] + ct * cur_matrix[i][aj]

      # print cur_matrix
      # print new_matrix
      # print ""

    return new_matrix

def usage():
  print "Usage:  Cube_Cube_Anneal.py [--help] [--T0=] [--Tf=] [--iter=] [--reset=] [--seed=] [--freq=] [--m=] [--n=]"

if __name__ == "__main__":
  m = 2
  n = 3

  T0   = 1.0
  Tf   = 0.5

  iter  = 1000000000
  reset =    1000000

  seed = long(time.time())

  stat_freq = 100000

  try:
    opts, args = getopt.getopt(sys.argv[1:],"", \
                               [                \
                                "help",         \
                                "T0=",          \
                                "Tf=",          \
                                "iter=",        \
                                "reset=",       \
                                "seed=",        \
                                "freq=",        \
                                "m=",           \
                                "n=",           \
                               ]                \
                              )
  except getopt.GetoptError:
    usage()
    sys.exit(1)

  for opt, arg in opts:
    if opt == "--help":
      usage()
      sys.exit()
    if opt == "--T0":
      T0 = float(arg)
    if opt == "--Tf":
      Tf = float(arg)
    if opt == "--iter":
      iter = long(arg)
    if opt == "--reset":
      reset = long(arg)
    if opt == "--seed":
      seed = long(arg)
    if opt == "--freq":
      stat_freq = long(arg)
    if opt == "--m":
      m = int(arg)
    if opt == "--n":
      n = int(arg)

  print "Cube_Cube_Anneal.py --T0=%f --Tf=%f --iter=%d --reset=%d --seed=%s --freq=%d --m=%d --n=%d" % \
        (T0,Tf,iter,reset,seed,stat_freq,m,n)
  print

  a = 1.0/reset * (math.exp(math.pow(T0/Tf,reset/float(iter))) - math.e)
  print "a = ",a
  print

  cube_obj = Cube_Object(m,n,1.0,seed)
  make_cubes = SA.SA(T0,Tf,a,cube_obj,reset,stat_freq,seed)

  (best_cube,best_energy,best_extra) = make_cubes.run()
