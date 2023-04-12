"""Library for representing very large integers of the form: a b^n + c"""

from fractions import Fraction
import math


def is_simple(value):
  """Is `value` a "simple" numeric type (integer or Fraction)."""
  return isinstance(value, (int, Fraction))

def exp_int(*, base, exponent):
  """Returns either int or ExpInt based on size of exponent."""
  if is_simple(exponent) and exponent < 1000:
    return base**exponent
  else:
    return ExpInt(base, exponent)

def struct_eq(self, other):
  """Test for structural equality (not math equality)."""
  if is_simple(self) and is_simple(other):
    return self == other
  elif isinstance(self, ExpInt) and isinstance(other, ExpInt):
    return (self.base == other.base and self.coef == other.coef and
            self.const == other.const and self.exponent == other.exponent)
  else:
    # Cannot compare
    return False

class ExpInt:
  def __init__(self, base, exponent, coef=1, const=0):
    assert is_simple(base) and is_simple(coef) and is_simple(const)
    assert is_simple(exponent) or isinstance(exponent, ExpInt)
    self.base = base
    self.exponent = exponent
    self.coef = coef
    self.const = const

  def __str__(self):
    return f"({self.coef} * {self.base}^{self.exponent} + {self.const})"
  __repr__ = __str__


  # Modular arithmetic on ExpInt is actually reasonable once you know the trick.
  #   See: https://www.sligocki.com/2022/06/21/bb-6-2-t15.html
  #    and https://www.sligocki.com/2022/06/23/period-3.html
  def __mod__(self, other):
    if other == 1:
      return 0
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
    elif self.base == other.base and struct_eq(self.exponent, other.exponent):
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
    if is_simple(other):
      other_exp = (other - self.const) / self.coef
      if other_exp < self.base:
        return True
      return self.exponent > math.log(other_exp, self.base)
    else:
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
