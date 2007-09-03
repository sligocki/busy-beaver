from __future__ import division
import random, math, sys
from copy import deepcopy

def safe_exp(x):
  if x > 0:
    return 1
  else:
    return math.exp(x)

def PT(B, neigh, E, C, steps, print_freq=0):
  """Runs parallel tempering with temperatures [1/b for b in B]
     to minimize E where neigh(s) returns a random neighbor to state s
     given initial configs C"""
  swaps = 0
  assert len(B) == len(C)
  n = len(C)
  for i in xrange(steps):
    if print_freq != 0 and (i % print_freq) == 0:
      print "Steps", i
      print "Swaps", swaps
      for c in C:
        print "%13.6e" % E(c),
      print
      print
      sys.stdout.flush()
    # Parallel Phase
    for k in range(n):
      new_state = neigh(C[k], 1/B[k])
      if random.random() < safe_exp( B[k]*(E(C[k]) - E(new_state)) ):
        C[k] = new_state
    # Swapping Phase
    k = random.randrange(n-1)
    if random.random() < safe_exp( (B[k] - B[k+1])*(E(C[k]) - E(C[k+1]))):
      swaps += 1
      C[k], C[k+1] = C[k+1], C[k]

  if print_freq != 0:
    print "Steps", steps
    print "Swaps", swaps
    print "Swaps / Step", swaps / steps
    for c in C:
      print "%f" % E(c),
    print
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

  res = PT(B, neigh, E, C, 10000, True)
  print [x[1] for x in res]
  print
  for k in range(2):
    for x in range(X):
      for y in range(Y):
        print ('X' if C[k][0][x][y] else ' '),
      print
    print

