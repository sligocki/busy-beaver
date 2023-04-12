"""Library for representing very large integers of the form: a b^n + c"""

from fractions import Fraction


def is_simple(value):
  """Is `value` a "simple" numeric type (integer or Fraction)."""
  return isinstance(value, (int, Fraction))

def exp_int(*, base, exponent, coef, const):
  """Returns either int or ExpInt based on size of exponent."""
  if is_simple(exponent) and exponent < 1000:
    return coef * base**exponent + const
  else:
    return ExpInt(base, exponent, coef, const)

class ExpInt:
  def __init__(self, base, exponent, coef, const):
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
    raise NotImplementedError(f"Cannot eval {self} % {other}")


  # Basic arithmetic with simple numbers.
  def __add__(self, other):
    if is_simple(other):
      return ExpInt(self.base, self.exponent, self.coef,
                    self.const + other)
    else:
      raise NotImplementedError(f"Cannot eval {self} + {other}")

  def __mul__(self, other):
    if other == 0:
      return 0
    elif is_simple(other):
      return ExpInt(self.base, self.exponent,
                    self.coef * other,
                    self.const * other)
    else:
      raise NotImplementedError(f"Cannot eval {self} * {other}")

  # Boilerplate
  def __neg__(self):
    return self * -1
  def __sub__(self, other):
    return self + (-other)
  def __rsub__(self, other):
    return (-self) + other
  def __truediv__(self, other):
    return self * Fraction(1, other)
  __radd__ = __add__
  __rmul__ = __mul__
