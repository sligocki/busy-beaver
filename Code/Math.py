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

def int_pow(n : int) -> tuple[int, int]:
  """Find smallest integer m such that n == m^k and return (m, k)"""
  for m in range(2, int(math.sqrt(n)) + 1):
    k = int(round(math.log(n, m)))
    if m**k == n:
      return (m, k)
  return (n, 1)


_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199, 211, 223, 227, 229, 233, 239, 241, 251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313, 317, 331, 337, 347, 349, 353, 359, 367, 373, 379, 383, 389, 397, 401, 409, 419, 421, 431, 433, 439, 443, 449, 457, 461, 463, 467, 479, 487, 491, 499, 503, 509, 521, 523, 541, 547, 557, 563, 569, 571, 577, 587, 593, 599, 601, 607, 613, 617, 619, 631, 641, 643, 647, 653, 659, 661, 673, 677, 683, 691, 701, 709, 719, 727, 733, 739, 743, 751, 757, 761, 769, 773, 787, 797, 809, 811, 821, 823, 827, 829, 839, 853, 857, 859, 863, 877, 881, 883, 887, 907, 911, 919, 929, 937, 941, 947, 953, 967, 971, 977, 983, 991, 997]

def prime_factor(n):
  """Returns list of pairs (p, k) for all p^k in the prime factorization of n."""
  assert n > 0
  res = []
  for p in _primes:
    k = 0
    while n % p == 0:
      k += 1
      n //= p
    if k:
      res.append((p, k))
    if n == 1:
      return res
  if n <= _primes[-1]**2:
    res.append((n, 1))
    return res
  raise NotImplementedError(f"Need more primes to factor {n}")


def carmichael(n: int) -> tuple[int, int]:
  """
  Carmichael's lambda function: https://en.wikipedia.org/wiki/Carmichael_function
  Returns a pair containing:
    1) The smallest m such that for all a coprime to n: a^m = 1 (mod n)
    2) The maximum power of any prime dividing n
  """
  res = 1
  max_k = 1
  for (p, k) in prime_factor(n):
    if p == 2 and k >= 3:
      lam_pk = 2**(k-2)
    else:
      lam_pk = (p-1) * p**(k-1)
    res = lcm(res, lam_pk)
    max_k = max(max_k, k)
  return res, max_k

def exp_mod(b: int, k, m: int) -> int:
  """Evaluate b^k % m efficiently for huge k."""
  kp, k0 = carmichael(m)
  # for all kn >= k0: b^kn = b^{kp+kn} (mod m)
  #   See: https://en.wikipedia.org/wiki/Carmichael_function#Exponential_cycle_length
  if k < k0:
    return pow(b, int(k), m)
  else:
    kn = (k - k0) % kp + k0
    # b^k = b^kn (mod m)
    return pow(b, kn, m)


def prec_mult(n : int, x : float):
  """Approximate n * x even if result is too large to fit in float."""
  if n.bit_length() < 50:
    # float provides more precision up to about 2**52.
    return n * x
  else:
    # int provides more precision above 2**52
    x = int(math.ldexp(x, 64))
    return (n * x) >> 64

def prec_add(n : int, x : float):
  """Approximate n + x even if result is too large to fit in float."""
  if not isinstance(n, int) or n.bit_length() < 50:
    # float provides more precision up to about 2**52.
    return n + x
  else:
    # int provides more precision above 2**52
    return n + int(x)
