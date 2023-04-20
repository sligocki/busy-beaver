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

def prec_mult(n : int, x : float):
  """Approximate n * x even if result is too large to fit in float."""
  if n.bit_length() < 50:
    # float provides more precision up to about 2**52.
    return n * x
  else:
    # int provides more precision above 2**52
    x = int(math.ldexp(x, 64))
    return (n * x) >> 64
