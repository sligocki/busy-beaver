"""
Func types used by Rules in Proof_System.
"""

from Algebraic_Expression import Expression, VariableToExpression, variables
from Exp_Int import ExpInt, exp_int
from Iterated_Expression import Iterated_Expression, Iterated_Math


def ceil_div(a, b):
  return ((a - 1) // b) + 1


class Func:
  """Abstract base class for various classes of functions."""

  def apply_rep(self, start, num_reps):
    raise NotImplementedError


class Iterated_Func(Func):
  """Represents a fallback function like: `x -> expr` applied N times."""

  def __init__(self, var, min_val, step_expr):
    self.var = var
    self.min = min_val
    self.step_expr = step_expr
    self.is_decreasing = False

    expr_vars = variables(step_expr)
    assert expr_vars.issubset({var}), f"step_expr {step_expr} contains other variables: {expr_vars}"

  def __repr__(self):
    return f"{self.step_expr}"

  __str__ = __repr__

  def apply_rep(self, start, num_reps):
    return Iterated_Expression(self.step_expr, self.var, start, num_reps)


class Subtract_Func(Func):
  """Represents a function like: `x -> x - c`"""

  def __init__(self, var, min, const):
    assert const > 0, const
    self.var = var
    self.min = min
    self.const = const
    self.is_decreasing = True
    self.has_collatz_decrease = self.const > 1

  def __repr__(self):
    return f"{self.var} - {self.const}"

  __str__ = __repr__

  def max_reps(self, start):
    # If start == self.min we can still apply_rep one more time.
    min_after = self.min - self.const
    num_reps, r = divmod(start - min_after, self.const)
    final_count = r + min_after
    return (num_reps, final_count)

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
    if self.const == 0:
      return start
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
    m_n = exp_int(base=self.coef, exponent=num_reps)
    numer = (a * m + self.const) * m_n - self.const
    assert isinstance(numer, (int, ExpInt, Expression, Iterated_Math)), numer
    if isinstance(numer, int):
      q, r = divmod(numer, m)
      assert r == 0, (numer, m, r)
      return q
    return numer / m
