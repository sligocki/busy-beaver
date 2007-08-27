#! /usr/bin/env python
#
# SA.py
#
# Simulated annealing - general class.
#

#
# A class do the simulated annealing.
#
class SA:
  #
  # Initialize the run
  #
  def __init__(self,initT,miniT,coolingRate,object,reset,report):
    import random

    self.random = random
    self.random.seed()

    self.initT = initT
    self.miniT = miniT

    self.coolingRate = coolingRate

    self.object = object

    self.reset = reset
    self.report = report

  #
  # Make a run
  #
  def run(self):
    import sys
    import math

    config0 = self.object.initConfig()
    energy0 = self.object.energyFunc(config0)

    print energy0
    print ''
    sys.stdout.flush()

    configMin = config0
    energyMin = energy0

    initT = self.initT
    T = initT

    count = 0
    totalCount = 0

    energyTotal = 0

    while T > self.miniT:
      config1 = self.object.nextConfig(config0)
      energy1 = self.object.energyFunc(config1)

      if energy1 < energyMin:
        configMin = config1
        energyMin = energy1

      if self.approve(energy0,energy1,T):
        config0 = config1
        energy0 = energy1

      count += 1
      totalCount += 1

      energyTotal += energy0

      if totalCount % self.report == 0:
        print totalCount,T,energyTotal/self.report,energyMin
        sys.stdout.flush()

        energyTotal = 0

      T = initT / math.log(math.e + self.coolingRate * count)

      if count == self.reset:
        print ''
        print configMin
        print ''
        sys.stdout.flush()
        initT = T
        count = 0

    print ''
    print energyMin
    sys.stdout.flush()

    return (configMin,energyMin)

  #
  # The approval function.
  #
  def approve(self,energy0,energy1,T):
    import math

    delta = energy1 - energy0

    if (delta/T > 700):
      threshold = 0.0
    else:
      threshold = 1 / (1 + math.exp(delta/T))

    if self.random.random() < threshold:
      return True
    else:
      return False

#
# An example "object" class to test the SA class
#
class testObject:
  #
  # Remember the object length
  #
  def __init__(self,length):
    self.length = length

  def initConfig(self):
    import random

    return [random.randint(0,1) for i in xrange(0,self.length)]

  def energyFunc(self,config):
    return sum(config)

  def nextConfig(self,curConfig):
    import random
    import copy

    nextConfig = copy.deepcopy(curConfig)

    index = random.randint(0,self.length-1)

    nextConfig[index] = random.randint(0,1)

    return nextConfig

if __name__ == "__main__":
  import sys

  length = int(sys.argv[1])

  object = testObject(length)
  sa = SA(50.0,50.0/(length*10000.0),0.1,object,3*length,length);

  (bestConfig,bestEnergy) = sa.run()
