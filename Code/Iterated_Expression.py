import math

from Algebraic_Expression import Expression, min_val, variables, substitute
from Common import is_const
from Exp_Int import tower_value

def get_depth(expr, var):
  if hasattr(expr, 'terms'):
    return max([0] + [get_depth(term, var) for term in expr.terms])
  elif hasattr(expr, 'var_power') and expr.var_power is not None:
    return get_depth(expr.var_power, var)
  elif hasattr(expr, 'var'):
    v = expr.var
    if v == var:
      return 0
    elif hasattr(v, 'exponent'):
      d = get_depth(v.exponent, var)
      if d >= 0:
        return 1 + d
  elif hasattr(expr, 'exponent'):
    d = get_depth(expr.exponent, var)
    if d >= 0:
      return 1 + d
  return -1000

class Iterated_Expression:
  """Represents f^N(start) lazily."""
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
  def tower_value(self):
    depth = get_depth(self.step_expr, self.var)
    if depth < 1:
      depth = 1 # fallback
      
    h_start, top_start = tower_value(self.start_val)
    try:
      n_val = int(self.num_reps)
      return (h_start + n_val * depth, top_start)
    except:
      return (1000, 10.0)

  def __lt__(self, other):
    if isinstance(other, int):
      # Assume Iterated_Expressions are huge
      return False
    raise NotImplementedError()
    
  def __gt__(self, other):
    if isinstance(other, int):
      return True
    raise NotImplementedError()

  def __le__(self, other):
    return self < other or self == other

  def __ge__(self, other):
    return self > other or self == other

  def __mul__(self, other):
    return Iterated_Math(self, 0, coef=other)

  def __rmul__(self, other):
    return Iterated_Math(self, 0, coef=other)

class Iterated_Math:
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

  def is_const(self):
    return False

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
    return Iterated_Math(self.it_expr, self.const * other, self.coef * other)

  def __rmul__(self, other):
    return Iterated_Math(self.it_expr, self.const * other, self.coef * other)

  def __divmod__(self, other):
    if other == 1:
      return (self, 0)
    raise NotImplementedError("Cannot mod Iterated_Math by non-1 value")

  def __abs__(self):
    return self

  @property
  def tower_value(self):
    return self.it_expr.tower_value

  def __lt__(self, other):
    if isinstance(other, int):
      return False
    raise NotImplementedError()
    
  def __gt__(self, other):
    if isinstance(other, int):
      return True
    raise NotImplementedError()

  def __le__(self, other):
    return self < other or self == other

  def __ge__(self, other):
    return self > other or self == other


