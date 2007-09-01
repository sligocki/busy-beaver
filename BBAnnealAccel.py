#! /usr/bin/env python
"""
A Busy Beaver finder using Simulated Annealing optimization and accelerated 
TM simulation.
"""

class TMObject:
  def __init__(self,numStates,numSymbols,stepLimit,timeLimit,seed):
    import random

    self.random = random
    self.random.seed(seed)

    self.numStates  = numStates
    self.numSymbols = numSymbols

    self.stepLimit = stepLimit
    self.timeLimit = timeLimit

  def initConfig(self):
    print "# of states  = ",self.numStates
    print "# of symbols = ",self.numSymbols
    print ""

    newTM = [None] * self.numSymbols * self.numStates

    for i in xrange(self.numSymbols * self.numStates):
      symb = self.random.randrange(self.numSymbols)
      dir   = self.random.randrange(2)
      state = self.random.randrange(-1,self.numStates)

      newTM[i] = (symb,dir,state)

    return newTM

  def energyFunc(self,curTM):
    from Macro.Chain_Tape import INF
    import Macro_Simulator

    transTM = [curTM[i*self.numSymbols:(i+1)*self.numSymbols] \
                 for i in xrange(self.numStates)]

    # print transTM

    result = Macro_Simulator.run(transTM,INF,self.timeLimit)

    exitCond = result[0]

    if exitCond == Macro_Simulator.OVERSTEPS or \
       exitCond == Macro_Simulator.INFINITE  or \
       exitCond == Macro_Simulator.TIMEOUT:
      numSymbols = 0 
      numSteps   = 0 

    elif exitCond == Macro_Simulator.HALT:
      numSymbols = result[1][1] 
      numSteps   = result[1][0] 

    elif exitCond == Macro_Simulator.UNDEFINED:
      print "TM sim error: %s" % result[2]
      sys.exit(1)

    else:
      print "Unknown TM sim exit code: %s" % exitCond
      sys.exit(1)

    return (-math.log(numSteps+1),numSymbols,numSteps)

  def nextConfig(self,curTM):
    """Mutate a single element of one transition."""
    newTM = curTM[:]

    # Choose the transition
    i = self.random.randrange(len(newTM))
    delta = self.random.choice((-1, 1))

    (symb,dir,state) = newTM[i]

    # Choose the element of the transition (i.e. symbol, direction or state)
    j = self.random.randrange(3)

    if j == 0:
      symb += delta
      symb %= numSymbols
    elif j == 1:
      dir = 1 - dir
    else:
      state += delta
      if state < -1:
        state += (numStates+1)
      elif state >= numStates:
        state -= (numStates+1)

    newTM[i] = (symb, dir, state)

    return newTM

def usage():
  print "Usage:  BBAnnealAccel.py [--help] [--T0=] [--Tf=] [--iter=] [--reset=] [--seed=] [--freq=] [--steps=] [--time=] [--states=] [--symbols=]"

if __name__ == "__main__":
  import time,getopt,sys,math
  import SA

  numStates  = 5
  numSymbols = 2

  T0   = 1.0
  Tf   = 0.5

  iter  = 1000000000
  reset =    1000000

  seed = long(time.time())

  statFreq = 100000

  stepLimit = 10000
  timeLimit = 60

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
      statFreq = long(arg)
    if opt == "--steps":
      stepLimit = int(arg)
    if opt == "--time":
      timeLimit = int(arg)
    if opt == "--states":
      numStates = int(arg)
    if opt == "--symbols":
      numSymbols = int(arg)

  print "BBAnnealAccel.py --T0=%f --Tf=%f --iter=%d --reset=%d --seed=%s --freq=%d --steps=%d --time=%d --states=%d --symbols=%d" % \
        (T0,Tf,iter,reset,seed,statFreq,stepLimit,timeLimit,numStates,numSymbols)
  print

  a = 1.0/reset * (math.exp(math.pow(T0/Tf,reset/float(iter))) - math.e)
  print "a = ",a
  print

  tmObj = TMObject(numStates,numSymbols,stepLimit,timeLimit,seed)
  makeTMs = SA.SA(T0,Tf,a,tmObj,reset,statFreq,seed)

  (bestTM,bestEnergy,bestExtra) = makeTMs.run()
