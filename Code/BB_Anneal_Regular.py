#! /usr/bin/env python
#
# BB_Anneal_Regular.py
#
"""
A Busy Beaver finder using Simulated Annealing optimization and regular TM
simulation.
"""

class TM_Object:
  def __init__(self,num_states,num_symbols,step_limit,tape_limit,seed):
    import random

    self.random = random
    self.random.seed(seed)

    self.num_states  = num_states
    self.num_symbols = num_symbols

    self.step_limit = step_limit
    self.tape_limit = tape_limit

  def init_config(self):
    # print "# of states  = ",self.num_states
    # print "# of symbols = ",self.num_symbols
    # print ""

    new_TM = [None] * self.num_symbols * self.num_states

    for i in xrange(self.num_symbols * self.num_states):
      digit = self.random.randrange(self.num_symbols)
      dir   = self.random.randrange(2)
      state = self.random.randrange(-1,self.num_states)

      new_TM[i] = (digit,dir,state)

    return new_TM

  def energy_func(self,cur_TM):
    from Turing_Machine_Sim import Turing_Machine_Sim
    import sys,math

    trans_TM = [cur_TM[i*self.num_symbols:(i+1)*self.num_symbols] \
                 for i in xrange(self.num_states)]

    result = Turing_Machine_Sim(trans_TM,self.num_states,self.num_symbols, \
                                self.tape_limit,self.step_limit)

    exit_cond = int(result[0])

    if exit_cond < 0:
      print "TM sim error: %s" % result[2]
      sys.exit(1)

    elif exit_cond <= 2:
      if exit_cond == 0:
        num_symbols = int(result[1])
        num_steps   = int(result[2])
      else:
        num_symbols = 0
        num_steps   = 0

    elif exit_cond == 3:
      bad_state  = int(result[1])
      bad_symbol = int(result[2])

      print "TM sim invalid table entry - state: %d, symbol: %d" % (bad_state,bad_symbol)
      sys.exit(1)

    elif exit_cond == 4:
      print "TM sim result: %s" % result[2]
      sys.exit(1)

    else:
      print "Unknown TM sim exit code: %d" % exit_cond
      sys.exit(1)

    return (-math.log(num_steps+1),num_symbols,num_steps)

  def next_config(self,cur_TM,T):
    new_TM = cur_TM[:]

    i = self.random.randrange(len(new_TM))
    delta = int(2*self.random.randrange(2) - 1)

    (digit,dir,state) = new_TM[i]

    j = self.random.randrange(3)

    if j == 0:
      digit += delta
      if digit < 0:
        digit += num_symbols
      elif digit >= num_symbols:
        digit -= num_symbols
    elif j == 1:
      dir = 1 - dir
    else:
      state += delta
      if state < -1:
        state += (num_states+1)
      elif state >= num_states:
        state -= (num_states+1)

    new_TM[i] = (digit, dir, state)

    return new_TM

def usage():
  print "Usage:  BB_Anneal_Regular.py [--help] [--T0=] [--Tf=] [--iter=] [--reset=] [--seed=] [--freq=] [--steps=] [--tape=] [--states=] [--symbols=]"

if __name__ == "__main__":
  import time,getopt,sys,math
  import SA

  num_states  = 5
  num_symbols = 2

  T0   = 1.0
  Tf   = 0.5

  iter  = 1000000000
  reset =    1000000

  seed = long(1000*time.time())

  stat_freq = 100000

  step_limit = 10000
  tape_limit = 40000

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
                                "steps=",       \
                                "tape=",        \
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
    if opt == "--steps":
      step_limit = int(arg)
    if opt == "--tape":
      tape_limit = int(arg)
    if opt == "--states":
      num_states = int(arg)
    if opt == "--symbols":
      num_symbols = int(arg)

  print "BB_Anneal_Regular.py --T0=%f --Tf=%f --iter=%d --reset=%d --seed=%s --freq=%d --steps=%d --tape=%d --states=%d --symbols=%d" % \
        (T0,Tf,iter,reset,seed,stat_freq,step_limit,tape_limit,num_states,num_symbols)
  print

  a = 1.0/reset * (math.exp(math.pow(T0/Tf,reset/float(iter))) - math.e)
  print "a = ",a
  print

  tm_obj = TM_Object(num_states,num_symbols,step_limit,tape_limit,seed)
  make_TMs = SA.SA(T0,Tf,a,tm_obj,reset,stat_freq,seed)

  (best_TM,best_energy,best_extra) = make_TMs.run()
