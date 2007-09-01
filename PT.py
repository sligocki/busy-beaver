from __future__ import division
import random, math
from copy import deepcopy

def PT(B, neigh, f, C, steps):
  """Runs parallel tempering with temperatures [1/b for b in B]
     to maximize f where neigh(s) returns a random neighbor to state s
     given initial configs C"""
  #swaps = 0
  assert len(B) == len(C)
  n = len(C)
  for i in range(steps):
    # Parallel Phase
    for k in range(n):
      state = neigh(C[k])
      if random.random() < math.exp( B[k]*(f(state) - f(C[k])) ):
        C[k] = state
    # Swapping Phase
    k = random.randrange(n-1)
    if random.random() < math.exp( (B[k] - B[k+1])*(f(C[k+1]) - f(C[k]))):
      #swaps += 1
      C[k], C[k+1] = C[k+1], C[k]

  #print swaps, steps, swaps/steps
  return C

if __name__ == "__main__":
  ## Example: Hard Sphere Model
  Bi = 5.; Bf = 0.; n = 12
  B = [Bi + (Bf - Bi)*k/(n-1) for k in range(n)]

  X = Y = 20
  C = [ ([ [False]*Y for x in range(X)], 0) for k in range(n)]

  f = lambda s: s[1]

  def neigh((c, E)):
    x = random.randrange(X)
    y = random.randrange(Y)
    # If there are neighbors, we can't do anything, stay put.
    if ( (x > 0 and c[x-1][y]) or (x < X-1 and c[x+1][y]) or
         (y > 0 and c[x][y-1]) or (y < Y-1 and c[x][y+1]) ):
      return c, E
    # Otherwise toggle this location
    else:
      E -= (1 if c[x][y] else -1)
      c = deepcopy(c)
      c[x][y] = not c[x][y]
      return c, E

  res = PT(B, neigh, f, C, 10000)
  print [x[1] for x in res]
  print
  for k in range(1):
    for x in range(X):
      for y in range(Y):
        print ('X' if C[k][0][x][y] else ' '),
      print
    print

