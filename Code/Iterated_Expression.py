from NatExpr import NatExpr
from Algebraic_Expression import min_val, substitute, variables
from Exp_Int import uparrow_size_approx
from NatExpr import is_const


def get_step_growth(expr, var):
  """
  Returns `(arrows, count)` describing how `expr(var)` grows per application:
  `(arrows, count)` means `expr(var) ≈ (10 ↑^arrows)^count (var)`.
  Returns `None` if `var` is not found in `expr`.
  """
  if hasattr(expr, "terms"):
    growths = [get_step_growth(term, var) for term in expr.terms]
    if hasattr(expr, "const") and not isinstance(expr.const, int) and expr.const is not expr:
      growths.append(get_step_growth(expr.const, var))
    valid = [g for g in growths if g is not None]
    if valid:
      return max(valid)
    return None
  elif hasattr(expr, "vars") and isinstance(expr.vars, (list, tuple)):
    growths = [get_step_growth(vp, var) for vp in expr.vars]
    if hasattr(expr, "coef") and not isinstance(expr.coef, int):
      growths.append(get_step_growth(expr.coef, var))
    valid = [g for g in growths if g is not None]
    if valid:
      return max(valid)
    return None
  elif hasattr(expr, "var") and not hasattr(expr, "step_expr"):
    v = expr.var
    if v == var:
      return (1, 0)
    elif hasattr(v, "exponent"):
      g = get_step_growth(v.exponent, var)
      if g is not None:
        return (1, g[1] + 1) if g[0] == 1 else g
  elif hasattr(expr, "exponent"):
    g = get_step_growth(expr.exponent, var)
    if g is not None:
      return (1, g[1] + 1) if g[0] == 1 else g
  elif type(expr).__name__ == "Iterated_Math":
    return get_step_growth(expr.it_expr, var)
  elif type(expr).__name__ == "Iterated_Expression":
    g_reps = get_step_growth(expr.num_reps, var)
    if g_reps is not None:
      g_step = get_step_growth(expr.step_expr, expr.var) or (1, 1)
      arr_f = g_step[0] + 1
      arr_N, count_N = g_reps
      if arr_f > arr_N:
        return (arr_f, 1)
      elif arr_f == arr_N:
        return (arr_N, count_N + 1)
      else:
        return g_reps
  return None


def get_depth(expr, var):
  """
  Returns the exponentiation depth of `var` within `expr`.
  Returns None if `var` is not found.
  """
  g = get_step_growth(expr, var)
  if g is None:
    return None
  return g[1] if g[0] == 1 else g[0]


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
      substitute(self.num_reps, assignment),
    )

  def __rsub__(self, other):
    return Iterated_Math(other, -self)

  def __divmod__(self, other):
    if other == 1:
      return (self, 0)
    raise NotImplementedError("Cannot mod Iterated_Expression by non-1 value")

  def __neg__(self):
    return Iterated_Math(self, 0) * -1  # Not actually supported properly, but let's just do it
    # Wait, we need to multiply.
    raise NotImplementedError("Cannot negate Iterated_Expression")

  def __abs__(self):
    return self

  @property
  def uparrow_size_approx(self):
    g_step = get_step_growth(self.step_expr, self.var)
    if g_step is None or g_step == (1, 0):
      g_step = (1, 1)
    step_arrows, step_count = g_step

    val_start = uparrow_size_approx(self.start_val)
    top_start = val_start[-1]
    arr = step_arrows + 1
    try:
      n_val = int(self.num_reps)
      if val_start[0] == arr and isinstance(val_start[1], (int, float)):
        return (arr, val_start[1] + n_val * step_count, *val_start[2:])
    except Exception:
      pass

    val_reps = uparrow_size_approx(self.num_reps)
    if val_reps[0] > arr:
      # Iterating an arr-level operation N times when N is at a higher up-arrow
      # level is dominated by N itself (analogous to ExpTerm when val[0] > 2).
      return val_reps

    total_reps = self.num_reps * step_count if step_count > 1 else self.num_reps
    if val_start[0] == arr:
      return (arr, val_start[1] + total_reps, *val_start[2:])
    return (arr, total_reps, top_start)

  def __lt__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return True
    if not isinstance(other, (Iterated_Expression, Iterated_Math)):
      return False
    return self.uparrow_size_approx < uparrow_size_approx(other)

  def __gt__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return False
    if not isinstance(other, (Iterated_Expression, Iterated_Math)):
      return True
    return self.uparrow_size_approx > uparrow_size_approx(other)

  def __le__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return True
    if not isinstance(other, (Iterated_Expression, Iterated_Math)):
      return False
    return uparrow_size_approx(self) <= uparrow_size_approx(other)

  def __ge__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return False
    if not isinstance(other, (Iterated_Expression, Iterated_Math)):
      return True
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
    is_neg_const = isinstance(self.const, int) and self.const < 0
    if self.coef == 1 and self.const == 0:
      return f"{self.it_expr}"
    elif self.coef == 1:
      if is_neg_const:
        return f"({self.it_expr} - {-self.const})"
      return f"({self.it_expr} + {self.const})"
    elif self.const == 0:
      return f"({self.coef} * {self.it_expr})"
    else:
      if is_neg_const:
        return f"({self.coef} * {self.it_expr} - {-self.const})"
      return f"({self.coef} * {self.it_expr} + {self.const})"

  __str__ = __repr__

  def try_eval(self):
    return None

  @property
  def is_const(self):
    return is_const(self.it_expr) and is_const(self.const) and is_const(self.coef)

  def min_val(self):
    return self.coef * min_val(self.it_expr) + min_val(self.const)

  def variables(self):
    return variables(self.it_expr) | variables(self.const) | variables(self.coef)

  def substitute(self, assignment):
    return Iterated_Math(
      substitute(self.it_expr, assignment),
      substitute(self.const, assignment),
      substitute(self.coef, assignment),
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

  def __mod__(self, other):
    if other == 1:
      return 0
    other = int(other)
    if self.coef % other == 0:
      return self.const % other
    # TODO: Support general case when coef % other != 0 (by evaluating it_expr % other).
    raise NotImplementedError(f"Cannot mod Iterated_Math by {other}: {self}")

  def __divmod__(self, other):
    if other == 1:
      return (self, 0)
    other = int(other)
    if self.coef % other == 0:
      q, r = divmod(self.const, other)
      return (Iterated_Math(self.it_expr, q, self.coef // other), r)
    # TODO: Support general case when coef % other != 0.
    raise NotImplementedError(f"Cannot divmod Iterated_Math by {other}: {self}")

  def __abs__(self):
    return self

  @property
  def uparrow_size_approx(self):
    return self.it_expr.uparrow_size_approx

  def __lt__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return True
    if not isinstance(other, (Iterated_Expression, Iterated_Math)):
      return False
    return uparrow_size_approx(self) < uparrow_size_approx(other)

  def __gt__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return False
    if not isinstance(other, (Iterated_Expression, Iterated_Math)):
      return True
    return uparrow_size_approx(self) > uparrow_size_approx(other)

  def __le__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return True
    if not isinstance(other, (Iterated_Expression, Iterated_Math)):
      return False
    return uparrow_size_approx(self) <= uparrow_size_approx(other)

  def __ge__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return False
    if not isinstance(other, (Iterated_Expression, Iterated_Math)):
      return True
    return uparrow_size_approx(self) >= uparrow_size_approx(other)
