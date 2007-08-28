#! /usr/bin/env python
#
# A Busy Beaver finder using Simulated Annealing optimization and regular TM
# simulation.
#

class TMObject:
  def __init__(self,numStates,numSymbols,stepLimit,tapeLimit):
    self.numStates  = numStates
    self.numSymbols = numSymbols

    self.stepLimit = stepLimit
    self.tapeLimit = tapeLimit

  def initConfig(self):
    import random

    print "# of states  = ",self.numStates
    print "# of symbols = ",self.numSymbols
    print ""

    newTM = [None] * self.numSymbols * self.numStates

    for i in xrange(self.numSymbols * self.numStates):
      digit = random.randrange(self.numSymbols)
      dir   = random.randrange(2)
      state = random.randrange(-1,self.numStates)

      newTM[i] = (digit,dir,state)

    return newTM

  def energyFunc(self,curTM):
    from Turing_Machine_Sim import Turing_Machine_Sim
    import sys,math

    transTM = [curTM[i*self.numSymbols:(i+1)*self.numSymbols] \
                 for i in xrange(self.numStates)]

    result = Turing_Machine_Sim(transTM,self.numStates,self.numSymbols, \
                                self.tapeLimit,self.stepLimit)

    exitCond = int(result[0])

    if exitCond < 0:
      print "TM sim error: %s" % result[2]
      sys.exit(1)

    elif exitCond <= 2:
      if exitCond == 0:
        numSymbols = int(result[1])
        numSteps   = int(result[2])
      else:
        numSymbols = 0
        numSteps   = 0

    elif exitCond == 3:
      badState  = int(result[1])
      badSymbol = int(result[2])

      print "TM sim invalid table entry - state: %d, symbol: %d" % (badState,badSymbol)
      sys.exit(1)

    elif exitCond == 4:
      print "TM sim result: %s" % result[2]
      sys.exit(1)

    else:
      print "Unknown TM sim exit code: %d" % exitCond
      sys.exit(1)

    return (-math.log(numSteps+1),numSymbols,numSteps)

  def nextConfig(self,curTM):
    import random

    newTM = curTM[:]

    i = random.randrange(len(newTM))
    delta = int(2*random.randrange(2) - 1)

    (digit,dir,state) = newTM[i]

    j = random.randrange(3)

    if j == 0:
      digit += delta
      if digit < 0:
        digit += numSymbols
      elif digit >= numSymbols:
        digit -= numSymbols
    elif j == 1:
      dir = 1 - dir
    else:
      state += delta
      if state < -1:
        state += (numStates+1)
      elif state >= numStates:
        state -= (numStates+1)

    newTM[i] = (digit, dir, state)

    return newTM

def usage():
  print "Usage:  BBAnnealRegular.py [--help] [--T0=] [--Tf=] [--iter=] [--reset=] [--seed=] [--freq=] [--steps=] [--tape=] [--states=] [--symbols=]"

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
  tapeLimit = 40000

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
      statFreq = long(arg)
    if opt == "--steps":
      stepLimit = int(arg)
    if opt == "--tape":
      tapeLimit = int(arg)
    if opt == "--states":
      numStates = int(arg)
    if opt == "--symbols":
      numSymbols = int(arg)

  print "BBAnnealRegular.py --T0=%f --Tf=%f --iter=%d --reset=%d --seed=%s --freq=%d --steps=%d --tape=%d --states=%d --symbols=%d" % \
        (T0,Tf,iter,reset,seed,statFreq,stepLimit,tapeLimit,numStates,numSymbols)
  print

  a = 1.0/reset * (math.exp(math.pow(T0/Tf,reset/float(iter))) - math.e)
  print "a = ",a
  print

  tmObj = TMObject(numStates,numSymbols,stepLimit,tapeLimit)
  makeTMs = SA.SA(T0,Tf,a,tmObj,reset,statFreq)

  (bestTM,bestEnergy,bestExtra) = makeTMs.run()
