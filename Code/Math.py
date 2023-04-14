# Various math functions.

import math


def gcd(a : int, b : int) -> int:
  a = abs(a)
  b = abs(b)
  if b > a:
    a, b = b, a
  while b > 0:
    _, r = divmod(a, b)
    a, b = b, r
  return a

def lcm(a : int, b : int) -> int:
  return a * b // gcd(a, b)

def int_pow(n : int) -> (int, int):
  """Find smallest integer m such that n == m^k and return (m, k)"""
  for m in range(2, int(math.sqrt(n)) + 1):
    k = int(round(math.log(n, m)))
    if m**k == n:
      return (m, k)
  return (n, 1)

def prec_mult(n : int, x : float, prec : int = 10):
  """Approximate n * x even if result is too large to fit in float."""
  try:
    return n * x
  except OverflowError:
    # If n is too big to cast to float, we need to be a little more clever:
    x = int(x * 2**prec)
    return (n * x) >> prec
