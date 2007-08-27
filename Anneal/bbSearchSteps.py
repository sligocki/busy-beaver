#! /usr/bin/env python
#
# A Busy Beaver finder using Simulated Annealing optimization.
#

class TMObject:
####
#
# An example "object" class to test the SA class
#
class testObject:
  def __init__(self,numStates,numSymbols,stepLimit,timeLimit):
    self.numStates  = numStates
    self.numSymbols = numSymbols

    self.stepLimit = stepLimit
    self.timeLimit = timeLimit

  def initConfig(self):
    import random

    print "# of states  = ",self.numStates
    print "# of symbols = ",self.numSymbols

    newTM = [None] * self.numSymbols * self.numStates

    if i in xrange(self.numSymbols * self.numStates):
      digit = random.randrange(self.numSymbols)
      dir   = random.randrange(2)
      state = random.randrange(-1,self.numStates)

      newTM[i] = (digit,dir,state)

    return newTM

  def energyFunc(self,config):
    return sum(config)

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

    newTM[i] = (digit, direction, state)

    return newTM

def usage():
  print "Usage:  bbSearchSteps.py [--help] [--T0=] [--Tf=] [--iter=] [--seed=] [--freq=] [--steps=] [--time=] [--states=] [--symbols=]"

if __name__ == "__main__"

import SA

numStates  = 5
numSymbols = 2

T0   = 1.0
Tf   = 0.5
iter = 1000000000

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

print "bbSearchSteps.py --T0=%f --Tf=%f --iter=%d --seed=%s --freq=%d --steps=%d --time=%d --states=%d --symbols=%d" % \
      (T0,Tf,iter,seed,statFreq,stepLimit,timeLimit,numStates,numSymbols)
print

a = 1.0/iter * (math.exp(T0/Tf) - math.e)
print "a = ",a
print

tmObj = TMObject(numStates,numSymbols,stepLimit,timeLimit)
makeTMs = SA.SA(T0,Tf,a,tmObj,iter,statFreq)

(bestTM,bestEnergy) = makeTMs.run()
