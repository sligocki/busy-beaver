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

  def __init__(self,init_T,mini_T,cooling_rate,obj,reset,report,seed):
    """Initialize Simulated annealing on object obj with initial temperature
       init_T, minimum temperature mini_T, ..."""
    import random

    self.random = random
    self.random.seed(seed)

    self.init_T = init_T
    self.mini_T = mini_T

    self.cooling_rate = cooling_rate

    self.obj = obj

    self.reset = reset
    self.report = report

  def run(self):
    """Run Simulated Annealing algorithm."""
    import sys
    import math

    config0 = self.obj.init_config()
    (energy0,extra0) = separate(self.obj.energy_func(config0))

    print energy0,extra0
    print
    sys.stdout.flush()

    config_min = config0
    energy_min = energy0
    extra_min = extra0

    init_T = self.init_T
    T = init_T

    count = 0
    total_count = 0

    energy_total = 0

    while T > self.mini_T:
      config1 = self.obj.next_config(config0,T)
      (energy1,extra1) = separate(self.obj.energy_func(config1))

      if energy1 < energy_min:
        config_min = config1
        energy_min = energy1
        extra_min  = extra1

      if self.approve(energy0,energy1,T):
        config0 = config1
        energy0 = energy1
        extra0  = extra1

      count += 1
      total_count += 1

      energy_total += energy0

      if total_count % self.report == 0:
        print total_count,T,energy_total/self.report,energy_min,extra_min
        sys.stdout.flush()

        energy_total = 0

      T = init_T / math.log(math.e + self.cooling_rate * count)

      if count == self.reset:
        print
        print config_min
        print
        sys.stdout.flush()
        init_T = T
        count = 0

    print
    print energy_min,extra_min
    sys.stdout.flush()

    return (config_min,energy_min,extra_min)

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
class test_object(object):
  #
  # Remember the object length
  #
  def __init__(self,length):
    self.length = length

  def init_config(self):
    import random

    return [random.randrange(2) for i in xrange(self.length)]

  def energy_func(self,config):
    return sum(config)

  def next_config(self,cur_config,T):
    import random
    import copy

    next_config = copy.deepcopy(cur_config)

    index = random.randrange(self.length)

    next_config[index] = random.randrange(2)

    return next_config

if __name__ == "__main__":
  import sys,time

  length = int(sys.argv[1])

  obj = test_object(length)
  sa = SA(50.0,50.0/(length*10000.0),0.1,obj,3*length,length,time.time());

  (best_config,best_energy,best_extra) = sa.run()
