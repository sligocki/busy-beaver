"""
Func types used by Rules in Proof_System.
"""

import math

from Algebraic_Expression import Expression, VariableToExpression
from Exp_Int import ExpInt, exp_int


def ceil_div(a, b):
  return ((a-1) // b) + 1

class Func:
  """Abstract base class for various classes of functions."""
  def apply_rep(self, start, num_reps):
    raise NotImplementedError


class Subtract_Func(Func):
  """Represents a function like: `x -> x - c`"""
  def __init__(self, var, min, const):
    assert const > 0, const
    self.var = var
    self.min = min
    self.const = const
    self.is_decreasing = True
    self.has_collatz_decrease = (self.const > 1)

  def __repr__(self):
    return f"{self.var} - {self.const}"
  __str__ = __repr__

  def max_reps(self, start):
    # If start == self.min we can still apply_rep one more time.
    return ((start - self.min) // self.const) + 1

  def apply_rep(self, start, num_reps):
    return start - num_reps * self.const


class Add_Func(Func):
  """Represents a function like: `x -> x + c`"""
  def __init__(self, var, min, const):
    assert const >= 0, const
    self.var = var
    self.min = min
    self.const = const
    self.is_decreasing = False

  def __repr__(self):
    return f"{self.var} + {self.const}"
  __str__ = __repr__

  def apply_rep(self, start, num_reps):
    return start + num_reps * self.const


class Mult_Func(Func):
  """Represents a function like: `x -> m x + b`"""
  def __init__(self, var, min, coef, const):
    assert coef > 0, coef
    self.var = var
    self.coef = coef
    self.const = const
    self.min = self.compute_min(min)
    self.is_decreasing = False
    self.expr = self.coef * VariableToExpression(self.var) + self.const

  def __repr__(self):
    return f"{self.expr}"
  __str__ = __repr__

  def compute_min(self, min):
    # Increase min enough to guarantee that this is a non-decreasing function.
    #   m x + b >= x -> x >= -b / (m-1)
    if self.const >= 0:
      return min
    else:
      min_no_decr = ceil_div(-self.const, self.coef - 1)
      return max(min, min_no_decr)

  def apply_rep(self, start, num_reps):
    # a --(1)--> (m+1) a + c  =>  a --(n)--> ((am + c) m^n - c) / m
    m = self.coef - 1
    a = start
    # We use a custom integer class for this since `num_reps` can
    # be very large!
    m_n = exp_int(base = self.coef, exponent = num_reps)
    numer = ((a*m + self.const) * m_n - self.const)
    assert isinstance(numer, (ExpInt, Expression)), numer
    return numer / m


class Pow_Func(Func):
  """Represents a function like: `x -> (a b^{u x + v} + c)/d`"""
  def __init__(self, var, min, base, coef_base, const_base, denom, coef_exp, const_exp):
    assert base > 1, base
    assert coef_base > 0, coef_base
    assert coef_exp > 0, coef_exp
    self.var = var
    self.base = base
    self.coef_base = coef_base
    self.const_base = const_base
    self.denom = denom
    self.coef_exp = coef_exp
    self.const_exp = const_exp
    self.min = self.compute_min(min)
    self.is_decreasing = False

    exp = self.coef_exp * VariableToExpression(self.var) + self.const_exp
    self.expr = (self.coef_base * exp_int(self.base, exp) + self.const_base) / self.denom

  def __repr__(self):
    return f"{self.expr}"
  __str__ = __repr__

  def compute_min(self, min):
    # Increase min enough to guarantee that this is an increasing function.
    #   (a b^{u x + v} + c)/d > x
    #   ux + v > log_b(dx-c) - log_b(a)
    #   x > (log_b(dx-c) - log_b(a) - v) / u
    av = self.const_exp + math.log(self.coef_base, self.base)
    while True:
      dxc = self.denom * min - self.const_base
      if dxc <= 0:
        return min
      else:
        x_bound = (math.log(dxc, self.base) - av) / self.coef_exp
        if min > x_bound:
          return min
        else:
          # TODO: Add tests that actually use this logic.
          min = math.ceil(x_bound)
