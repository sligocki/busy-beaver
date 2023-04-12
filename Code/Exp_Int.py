"""Library for representing very large integers of the form: a b^n + c"""

from fractions import Fraction
import functools
import math


def exp_int(*, base, exponent):
  """Returns either int or ExpInt based on size of exponent."""
  if is_simple(exponent) and exponent < 1000:
    return base**exponent
  else:
    return ExpInt(base, exponent)


def is_simple(value):
  """Is `value` a "simple" numeric type (integer or Fraction)."""
  return isinstance(value, (int, Fraction))

def _struct_eq(self, other):
  """Test for structural equality (not math equality)."""
  if is_simple(self) and is_simple(other):
    return self == other
  elif isinstance(self, ExpInt) and isinstance(other, ExpInt):
    return (self.base == other.base and self.coef == other.coef and
            self.const == other.const and self.exponent == other.exponent)
  else:
    # Cannot compare
    return False


def gcd(a, b):
  if b > a:
    a, b = b, a
  while b > 0:
    _, r = divmod(a, b)
    a, b = b, r
  return a

def lcm(a, b):
  return a * b // gcd(a, b)

@functools.cache
def cycle(b, m):
  """Smallest i >= 0, p > 0 such that b^i+p ≡ b^i (mod m)."""
  vals = {}
  n = 1
  k = 0
  # print(f"   DEBUG: cycle({b}, {m})")
  while n not in vals:
    vals[n] = k
    n = (n * b) % m
    k += 1
  i = vals[n]
  p = k - i
  # print(f"   DEBUG: cycle({b}, {m}) = ({i}, {p})")
  return (i, p)

# Modular arithmetic on ExpInt is actually reasonable once you know the trick.
#   See: https://www.sligocki.com/2022/06/21/bb-6-2-t15.html
#    and https://www.sligocki.com/2022/06/23/period-3.html
def exp_mod(b, k, m):
  """Evaluate b^k % m efficiently."""
  (i, p) = cycle(b, m)
  if k < i:
    return b**k % m
  else:
    kr = (k - i) % p
    return (b**(i+kr)) % m


class ExpInt:
  def __init__(self, base, exponent, coef=1, const=0):
    assert isinstance(base, int)
    assert is_simple(coef) and is_simple(const)
    assert is_simple(exponent) or isinstance(exponent, ExpInt)
    self.base = base
    self.exponent = exponent
    self.coef = Fraction(coef)
    self.const = Fraction(const)

  def __str__(self):
    return f"({self.const} + {self.coef} * {self.base}^{self.exponent})"
  __repr__ = __str__


  def __mod__(self, other):
    if other == 1:
      return 0
    if isinstance(other, int):
      # (a b^k + c) / d = n other + r
      # a b^k = n (d other) + rd - c
      d = lcm(self.coef.denominator, self.const.denominator)
      a = int(self.coef * d)
      c = int(self.const * d)
      m = d * other
      bkr = exp_mod(self.base, self.exponent, m)
      rdc = (a * bkr) % m  # rd - c
      rd = rdc + c
      r, rdr = divmod(rd, d)
      assert rdr == 0, (rd, d, r, rdr)
      return r % other
    else:
      raise NotImplementedError(f"Cannot eval {self} % {other}")

  # Integer division
  def __floordiv__(self, other):
    r = self % other
    return (self - r) / other


  # Basic arithmetic with simple numbers.
  def __add__(self, other):
    if is_simple(other):
      return ExpInt(self.base, self.exponent, self.coef,
                    self.const + other)
    elif self.base == other.base and _struct_eq(self.exponent, other.exponent):
      if self.coef + other.coef == 0:
        return self.const + other.const
      else:
        return ExpInt(self.base, self.exponent,
                      self.coef + other.coef,
                      self.const + other.const)
    else:
      raise NotImplementedError(f"Cannot eval {self} + {other}")

  def __mul__(self, other):
    if other == 0:
      return 0
    elif is_simple(other):
      return ExpInt(self.base, self.exponent,
                    self.coef * other,
                    self.const * other)
    elif self.base == other.base and self.const == 0 == other.const:
      return ExpInt(self.base,
                    self.exponent + other.exponent,
                    self.coef * other.coef,
                    const = 0)
    else:
      raise NotImplementedError(f"Cannot eval {self} * {other}")

  def __gt__(self, other):
    if isinstance(other, int):
      # Expectation is that ExpInt > int, so just do a quick sanity check.
      log2_other = other.bit_length()
      if self.base >= 2 and self.coef >= 1 and self.exponent > log2_other:
        return True
    elif other == math.inf:
      return False
    elif other == -math.inf:
      return True
    raise NotImplementedError(f"Cannot eval {self} > {other}")

  # This is technically not true, but close enough ... at least until we compare ExpInts.
  __ge__ = __gt__

  # Boilerplate
  def __neg__(self):
    return self * -1
  def __sub__(self, other):
    return self + (-other)
  def __rsub__(self, other):
    return (-self) + other
  def __truediv__(self, other):
    return self * Fraction(1, other)
  def __lt__(self, other):
    return not (self >= other)
  def __le__(self, other):
    return not (self > other)
  __radd__ = __add__
  __rmul__ = __mul__
