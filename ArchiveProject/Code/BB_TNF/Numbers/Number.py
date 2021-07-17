#
# Number.py
#
"""
Abstract the idea of a number.
"""

from __future__ import division

class Number(object):
  """Base class for user-defined number-like objects"""
  # Basic Laws of "Numbers"
  def __radd__(self, other):
    """x+y == y+x"""
    return self.__add__(other)
  def __rmul__(self, other):
    """x*y == y*x"""
    return self.__mul__(other)
  def __neg__(self):
    """-x == -1*x"""
    return self.__mul__(-1)
  def __sub__(self, other):
    """x - y == x + -y"""
    return self.__add__(other.__neg__())
  def __rsub__(self, other):
    """x - y == -y + x"""
    return (self.__neg__()).__add__(other)
  def __pow__(self, power):
    """x^n == x * x^(n-1)"""
    if power == 0:
      return 1
    elif is_int(power) and power > 0:
      return (self.__mul__(self.__pow__(power - 1)))
    else:
      return NotImplemented

def gcd(a, b):
  if a == 0:
    return b
  else:
    return gcd(b % a, a)

def is_int(value):
  return isinstance(value, (int, long))

class Rational(Number):
  def __init__(self, top, bottom):
    if not is_int(top) or not is_int(bottom):
      raise TypeError, "Number.Rational() - must have integer arguments."
    if bottom == 0:
      raise ZeroDivisionError, "Number.Rational() - cannot have 0 denominator."
    elif bottom < 0:
      top, bottom = -top, -bottom
    g = gcd(abs(top), bottom)
    if g != 1:
      top //= g
      bottom //= g
    self.top = top
    self.bottom = bottom
  def __repr__(self):
    if self.bottom != 1:
      return repr(self.top)+"/"+repr(self.bottom)
    else:
      return repr(self.top)
  def __coerce__(self, other):
    if is_int(other):
      return self, Rational(other, 1)
    else:
      return NotImplemented
  def __mul__(self, other):
    """a/b * c/d = (ac)/(bd)"""
    return Rational(self.top * other.top, self.bottom * other.bottom)
  def __truediv__(self, other):
    """a/b / c/d = (ad)/(bc)"""
    return Rational(self.top * other.bottom, self.bottom * other.top)
  def __pow__(self, power):
    if not is_int(power):
      return NotImplemented
    if power >= 0:
      return Rational(self.top ** power, self.bottom ** power)
    else:
      return Rational(self.bottom ** (-power), self.top ** (-power))
  def __add__(self, other):
    """a/b + c/d = (ad + cb)/(bd)"""
    return Rational(self.top*other.bottom + other.top*self.bottom,
                    self.bottom*other.bottom)
