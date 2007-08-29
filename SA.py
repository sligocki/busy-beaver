#! /usr/bin/env python
"""
SA.py

Simulated annealing - general class.
"""

def separate(result):
  """If tuple, break into 2 peices, result[0] and result[1:]."""
  extra = None

  if isinstance(result,tuple):
    if len(result) > 1:
      extra = result[1:]
    result = result[0]

  return (result,extra)

class SA(object):
  """Simulated Annealing class"""

  def __init__(self,initT,miniT,coolingRate,obj,reset,report,seed):
    """Initialize Simulated annealing on object obj with initial temperature initT, 
       minimum temperature miniT, ..."""
    import random

    self.random = random
    self.random.seed(seed)

    self.initT = initT
    self.miniT = miniT

    self.coolingRate = coolingRate

    self.obj = obj

    self.reset = reset
    self.report = report

  def run(self):
    """Run Simulated Annealing algorithm."""
    import sys
    import math

    config0 = self.obj.initConfig()
    (energy0,extra0) = separate(self.obj.energyFunc(config0))

    print energy0,extra0
    print
    sys.stdout.flush()

    configMin = config0
    energyMin = energy0
    extraMin = extra0

    initT = self.initT
    T = initT

    count = 0
    totalCount = 0

    energyTotal = 0

    while T > self.miniT:
      config1 = self.obj.nextConfig(config0)
      (energy1,extra1) = separate(self.obj.energyFunc(config1))

      if energy1 < energyMin:
        configMin = config1
        energyMin = energy1
        extraMin  = extra1

      if self.approve(energy0,energy1,T):
        config0 = config1
        energy0 = energy1
        extra0  = extra1

      count += 1
      totalCount += 1

      energyTotal += energy0

      if totalCount % self.report == 0:
        print totalCount,T,energyTotal/self.report,energyMin,extraMin
        sys.stdout.flush()

        energyTotal = 0

      T = initT / math.log(math.e + self.coolingRate * count)

      if count == self.reset:
        print
        print configMin
        print
        sys.stdout.flush()
        initT = T
        count = 0

    print
    print energyMin,extraMin
    sys.stdout.flush()

    return (configMin,energyMin,extraMin)

  def approve(self,energy0,energy1,T):
    """The approval function.
       Stocastically approves of the transition from energy0 to energy1 based on temperature T."""
    import math

    delta = energy1 - energy0

    if (delta/T > 700): # Protects against overloading math.exp function.
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
class testObject(object):
  #
  # Remember the object length
  #
  def __init__(self,length):
    self.length = length

  def initConfig(self):
    import random

    return [random.randrange(2) for i in xrange(self.length)]

  def energyFunc(self,config):
    return sum(config)

  def nextConfig(self,curConfig):
    import random
    import copy

    nextConfig = copy.deepcopy(curConfig)

    index = random.randrange(self.length)

    nextConfig[index] = random.randrange(2)

    return nextConfig

if __name__ == "__main__":
  import sys,time

  length = int(sys.argv[1])

  obj = testObject(length)
  sa = SA(50.0,50.0/(length*10000.0),0.1,obj,3*length,length,time.time());

  (bestConfig,bestEnergy,bestExtra) = sa.run()
