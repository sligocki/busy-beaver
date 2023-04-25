"""
Func types used by Rules in Proof_System.
"""

import math

from Algebraic_Expression import VariableToExpression
from Exp_Int import exp_int


class Func:
  """Abstract base class for various classes of functions."""


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


class Add_Func(Func):
  """Represents a function like: `x -> x + c`"""
  def __init__(self, var, min, const):
    assert const > 0, const
    self.var = var
    self.min = min
    self.const = const
    self.is_decreasing = False

  def __repr__(self):
    return f"{self.var} + {self.const}"
  __str__ = __repr__


class Mult_Func(Func):
  """Represents a function like: `x -> m x + b`"""
  def __init__(self, var, min, coef, const):
    assert coef > 0, coef
    self.var = var
    self.base = base
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
      min_no_decr = math.ceil(-b / (m-1))
      return max(min, min_no_decr)


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
          min = math.ceil(x_bound)
