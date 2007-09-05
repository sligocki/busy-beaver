from __future__ import division
import random, math, sys
from copy import deepcopy

def safe_exp(x):
  if x > 0:
    return 1
  else:
    return math.exp(x)

def separate(result):
  """If tuple, break into 2 peices, result[0] and result[1:]."""
  extra = None

  if isinstance(result,tuple):
    if len(result) > 1:
      extra = result[1:]
    result = result[0]

  return (result,extra)

def PT(B, neigh, E, C, steps, print_freq=0):
  """Runs parallel tempering with temperatures [1/b for b in B]
     to minimize E where neigh(s) returns a random neighbor to state s
     given initial configs C"""
  import time

  swaps = 0
  assert len(B) == len(C)
  n = len(C)

  for k in xrange(n):
    (energy,extra) = separate(E(C[k]))
    C[k] = (C[k],energy) + extra
    if k == 0:
      best = C[k]
    else:
      if C[k][1] < best[1]:
        best = C[k]

  start_time = time.time()

  for i in xrange(steps):
    if print_freq != 0 and (i % print_freq) == 0:
      end_time = time.time()
      print "Steps", i
      print "Swaps", swaps
      for c in C:
        print "%13.6e" % c[1],
      print "(%.3f)" % (end_time - start_time)
      print
      print best[1:],best[0]
      print
      sys.stdout.flush()
      start_time = time.time()
    # Parallel Phase
    for k in range(n):
      new_state = neigh(C[k][0], 1/B[k])
      (new_energy,new_extra) = separate(E(new_state))
      new_state = (new_state, new_energy) + new_extra
      if random.random() < safe_exp( B[k]*(C[k][1] - new_state[1])):
        C[k] = new_state
        if C[k][1] < best[1]:
          best = C[k]
    # Swapping Phase
    k = random.randrange(n-1)
    if random.random() < safe_exp( (B[k] - B[k+1])*(C[k][1] - C[k+1][1])):
      swaps += 1
      C[k], C[k+1] = C[k+1], C[k]

  if print_freq != 0:
    print "Steps", steps
    print "Swaps", swaps
    print "Swaps / Step", swaps / steps
    for c in C:
      print "%f" % c[1],
    print
    print best[1:],best[0]
    print
  return C

if __name__ == "__main__":
  ## Example: Hard Sphere Model
  Bi = 5.; Bf = 0.0001; n = 12
  B = [Bi + (Bf - Bi)*k/(n-1) for k in range(n)]

  X = Y = 20
  C = [ ([ [False]*Y for x in range(X)], 0) for k in range(n)]

  E = lambda s: -s[1]

  def neigh((c, n), T):
    x = random.randrange(X)
    y = random.randrange(Y)
    # If there are neighbors, we can't do anything, stay put.
    if ( (x > 0 and c[x-1][y]) or (x < X-1 and c[x+1][y]) or
         (y > 0 and c[x][y-1]) or (y < Y-1 and c[x][y+1]) ):
      return c, n
    # Otherwise toggle this location
    else:
      n -= (1 if c[x][y] else -1) # Number of spheres
      c = deepcopy(c)
      c[x][y] = not c[x][y]
      return c, n

  res = PT(B, neigh, E, C, 10000, 1000)
  print [x[1] for x in res]
  print
  for k in range(2):
    for x in range(X):
      for y in range(Y):
        print ('X' if C[k][0][0][x][y] else ' '),
      print
    print

