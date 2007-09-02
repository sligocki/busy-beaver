#! /usr/bin/env python
"""
A Busy Beaver finder using Simulated Annealing optimization and accelerated 
TM simulation.
"""

class TM_Object:
  def __init__(self,num_states,num_symbols,step_limit,time_limit,seed):
    import random

    self.random = random
    self.random.seed(seed)

    self.num_states  = num_states
    self.num_symbols = num_symbols

    self.step_limit = step_limit
    self.time_limit = time_limit

  def init_Config(self):
    print "# of states  = ",self.num_states
    print "# of symbols = ",self.num_symbols
    print ""

    new_TM = [None] * self.num_symbols * self.num_states

    for i in xrange(self.num_symbols * self.num_states):
      symb = self.random.randrange(self.num_symbols)
      dir   = self.random.randrange(2)
      state = self.random.randrange(-1,self.num_states)

      new_TM[i] = (symb,dir,state)

    return new_TM

  def energy_Func(self,cur_TM):
    from Macro.Chain_Tape import INF
    import Macro_Simulator

    trans_TM = [cur_TM[i*self.num_symbols:(i+1)*self.num_symbols] \
                 for i in xrange(self.num_states)]

    # print trans_TM

    result = Macro_Simulator.run(trans_TM,INF,self.time_limit)

    exit_cond = result[0]

    if exit_cond == Macro_Simulator.OVERSTEPS or \
       exit_cond == Macro_Simulator.INFINITE  or \
       exit_cond == Macro_Simulator.TIMEOUT:
      num_symbols = 0 
      num_steps   = 0 

    elif exit_cond == Macro_Simulator.HALT:
      num_symbols = result[1][1] 
      num_steps   = result[1][0] 

    elif exit_cond == Macro_Simulator.UNDEFINED:
      print "TM sim error: %s" % result[2]
      sys.exit(1)

    else:
      print "Unknown TM sim exit code: %s" % exit_cond
      sys.exit(1)

    return (-math.log(num_steps+1),num_symbols,num_steps)

  def next_config(self,cur_TM,T):
    """Mutate a single element of one transition."""
    new_TM = cur_TM[:]

    # Choose the transition
    i = self.random.randrange(len(new_TM))
    delta = self.random.choice((-1, 1))

    (symb,dir,state) = new_TM[i]

    # Choose the element of the transition (i.e. symbol, direction or state)
    j = self.random.randrange(3)

    if j == 0:
      symb += delta
      symb %= num_symbols
    elif j == 1:
      dir = 1 - dir
    else:
      state += delta
      if state < -1:
        state += (num_states+1)
      elif state >= num_states:
        state -= (num_states+1)

    new_TM[i] = (symb, dir, state)

    return new_TM

def usage():
  print "Usage:  BB_Anneal_Accel.py [--help] [--T0=] [--Tf=] [--iter=] [--reset=] [--seed=] [--freq=] [--steps=] [--time=] [--states=] [--symbols=]"

if __name__ == "__main__":
  import time,getopt,sys,math
  import SA

  num_states  = 5
  num_symbols = 2

  T0   = 1.0
  Tf   = 0.5

  iter  = 1000000000
  reset =    1000000

  seed = long(time.time())

  stat_freq = 100000

  step_limit = 10000
  time_limit = 60

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
    if opt == "--time":
      time_limit = int(arg)
    if opt == "--states":
      num_states = int(arg)
    if opt == "--symbols":
      num_symbols = int(arg)

  print "BB_Anneal_Accel.py --T0=%f --Tf=%f --iter=%d --reset=%d --seed=%s --freq=%d --steps=%d --time=%d --states=%d --symbols=%d" % \
        (T0,Tf,iter,reset,seed,stat_freq,step_limit,time_limit,num_states,num_symbols)
  print

  a = 1.0/reset * (math.exp(math.pow(T0/Tf,reset/float(iter))) - math.e)
  print "a = ",a
  print

  tm_obj = TMObject(num_states,num_symbols,step_limit,time_limit,seed)
  make_TMs = SA.SA(T0,Tf,a,tm_obj,reset,stat_freq,seed)

  (best_TM,best_energy,best_extra) = make_TMs.run()
