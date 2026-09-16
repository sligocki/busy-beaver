import math

from Algebraic_Expression import Expression, min_val, variables, substitute
from Common import is_const
from Exp_Int import uparrow_size_approx

def get_depth(expr, var):
  """
  Returns the exponentiation depth of `var` within `expr`.
  Returns None if `var` is not found.
  """
  if hasattr(expr, 'terms'):
    depths = [get_depth(term, var) for term in expr.terms]
    valid_depths = [d for d in depths if d is not None]
    if valid_depths:
      return max(valid_depths)
    return None
  elif hasattr(expr, 'var_power') and expr.var_power is not None:
    return get_depth(expr.var_power, var)
  elif hasattr(expr, 'var'):
    v = expr.var
    if v == var:
      return 0
    elif hasattr(v, 'exponent'):
      d = get_depth(v.exponent, var)
      if d is not None:
        return 1 + d
  elif hasattr(expr, 'exponent'):
    d = get_depth(expr.exponent, var)
    if d is not None:
      return 1 + d
  elif type(expr).__name__ == 'Iterated_Math':
    return get_depth(expr.it_expr, var)
  elif type(expr).__name__ == 'Iterated_Expression':
    d_reps = get_depth(expr.num_reps, var)
    if d_reps is not None:
      D = get_depth(expr.step_expr, expr.var)
      if D is None or D < 1: D = 1
      arr_f = D + 1
      arr_N = d_reps + 1
      return max(arr_f, arr_N) - 1
  return None

from NatExpr import NatExpr

class Iterated_Expression(NatExpr):
  """An expression representing `f^n(x)`."""
  def __init__(self, step_expr, var, start_val, num_reps):
    # step_expr is the function f(x)
    # var is the variable x in step_expr
    # start_val is the initial value
    # num_reps is the number of times to apply f
    self.step_expr = step_expr
    self.var = var
    self.start_val = start_val
    self.num_reps = num_reps

    # Ensure step_expr only depends on var
    expr_vars = variables(self.step_expr)
    assert expr_vars.issubset({self.var}), f"step_expr {self.step_expr} contains other variables: {expr_vars}"

  def __repr__(self):
    return f"((λ{self.var} → {self.step_expr})^({self.num_reps}) ({self.start_val}))"
  __str__ = __repr__

  def try_eval(self):
    return None

  @property
  def is_const(self):
    return is_const(self.start_val) and is_const(self.num_reps)

  @property
  def const(self):
    # This is a hack so Expression(..., const=Iterated_Expression) doesn't break
    return self

  def min_val(self):
    # Assuming f(x) >= x, min(f^N(x)) >= min(x)
    return min_val(self.start_val)

  def variables(self):
    return variables(self.start_val) | variables(self.num_reps)

  def substitute(self, assignment):
    return Iterated_Expression(
      self.step_expr,
      self.var,
      substitute(self.start_val, assignment),
      substitute(self.num_reps, assignment)
    )

  def __add__(self, other):
    return Iterated_Math(self, other)

  def __radd__(self, other):
    return Iterated_Math(self, other)

  def __sub__(self, other):
    return Iterated_Math(self, -other)

  def __rsub__(self, other):
    return Iterated_Math(other, -self)

  def __divmod__(self, other):
    if other == 1:
      return (self, 0)
    raise NotImplementedError("Cannot mod Iterated_Expression by non-1 value")

  def __neg__(self):
    return Iterated_Math(self, 0) * -1 # Not actually supported properly, but let's just do it
    # Wait, we need to multiply.
    raise NotImplementedError("Cannot negate Iterated_Expression")

  def __abs__(self):
    return self

  @property
  def uparrow_size_approx(self):
    depth = get_depth(self.step_expr, self.var)
    if depth is None or depth < 1:
      depth = 1 # fallback
      
    val_start = uparrow_size_approx(self.start_val)
    top_start = val_start[-1]
    try:
      n_val = int(self.num_reps)
      return (val_start[0], val_start[1] + n_val * depth, *val_start[2:])
    except:
      return (depth + 1, self.num_reps, top_start)

  def __lt__(self, other):
    if isinstance(other, (int, NatExpr)):
      # Assume Iterated_Expressions are huge
      return False
    return self.uparrow_size_approx < uparrow_size_approx(other)
    
  def __gt__(self, other):
    if isinstance(other, (int, NatExpr)):
      return True
    return self.uparrow_size_approx > uparrow_size_approx(other)

  def __le__(self, other):
    if isinstance(other, (int, NatExpr)): return False
    return uparrow_size_approx(self) <= uparrow_size_approx(other)

  def __ge__(self, other):
    if isinstance(other, (int, NatExpr)): return True
    return uparrow_size_approx(self) >= uparrow_size_approx(other)

  def __mul__(self, other):
    if other == 0:
      return 0
    return Iterated_Math(self, 0, coef=other)

  def __rmul__(self, other):
    if other == 0:
      return 0
    return Iterated_Math(self, 0, coef=other)

  def __add__(self, other):
    return Iterated_Math(self, other, coef=1)

  def __radd__(self, other):
    return Iterated_Math(self, other, coef=1)

  def __sub__(self, other):
    return Iterated_Math(self, -other, coef=1)

class Iterated_Math(NatExpr):
  """A shifted iterated expression: `Iterated_Expression + const`"""
  def __init__(self, it_expr, const, coef=1):
    self.it_expr = it_expr
    self.const = const
    self.coef = coef

  def __repr__(self):
    if self.coef == 1 and self.const == 0:
      return f"{self.it_expr}"
    elif self.coef == 1:
      if self.const < 0:
        return f"({self.it_expr} - {-self.const})"
      return f"({self.it_expr} + {self.const})"
    elif self.const == 0:
      return f"({self.coef} * {self.it_expr})"
    else:
      if self.const < 0:
        return f"({self.coef} * {self.it_expr} - {-self.const})"
      return f"({self.coef} * {self.it_expr} + {self.const})"
  __str__ = __repr__

  def try_eval(self):
    return None

  @property
  def is_const(self):
    return is_const(self.it_expr)

  def min_val(self):
    return self.coef * min_val(self.it_expr) + min_val(self.const)

  def variables(self):
    return variables(self.it_expr) | variables(self.const)

  def substitute(self, assignment):
    return Iterated_Math(
      substitute(self.it_expr, assignment),
      substitute(self.const, assignment),
      self.coef
    )

  def __add__(self, other):
    return Iterated_Math(self.it_expr, self.const + other, self.coef)
  
  def __radd__(self, other):
    return Iterated_Math(self.it_expr, self.const + other, self.coef)

  def __sub__(self, other):
    return Iterated_Math(self.it_expr, self.const - other, self.coef)

  def __rsub__(self, other):
    raise NotImplementedError("Cannot rsub Iterated_Math")

  def __mul__(self, other):
    if other == 0:
      return 0
    return Iterated_Math(self.it_expr, self.const * other, self.coef * other)

  def __rmul__(self, other):
    if other == 0:
      return 0
    return Iterated_Math(self.it_expr, self.const * other, self.coef * other)

  def __divmod__(self, other):
    if other == 1:
      return (self, 0)
    raise NotImplementedError(f"Cannot mod Iterated_Math by non-1 value: {other}")

  def __abs__(self):
    return self

  @property
  def uparrow_size_approx(self):
    return self.it_expr.uparrow_size_approx

  def __lt__(self, other):
    if isinstance(other, (int, NatExpr)):
      return False
    return uparrow_size_approx(self) < uparrow_size_approx(other)
    
  def __gt__(self, other):
    if isinstance(other, (int, NatExpr)):
      return True
    return uparrow_size_approx(self) > uparrow_size_approx(other)

  def __le__(self, other):
    if isinstance(other, (int, NatExpr)): return False
    return uparrow_size_approx(self) <= uparrow_size_approx(other)

  def __ge__(self, other):
    if isinstance(other, (int, NatExpr)): return True
    return uparrow_size_approx(self) >= uparrow_size_approx(other)


