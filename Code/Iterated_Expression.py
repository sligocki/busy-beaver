from NatExpr import NatExpr, is_const
from Algebraic_Expression import Expression, min_val, substitute, variables
from Exp_Int import ExpInt, is_simple, sign, struct_eq, uparrow_size_approx


def get_step_growth(expr, var):
  """
  Returns `(arrows, count)` describing how `expr(var)` grows per application:
  `(arrows, count)` means `expr(var) ≈ (10 ↑^arrows)^count (var)`.
  Returns `None` if `var` is not found in `expr`.
  """
  if type(expr).__name__ == "Iterated_Math":
    growths = [get_step_growth(term.it_expr, var) for term in expr.terms]
    if hasattr(expr, "const") and not isinstance(expr.const, int) and expr.const is not expr:
      growths.append(get_step_growth(expr.const, var))
    valid = [g for g in growths if g is not None]
    if valid:
      return max(valid)
    return None
  elif type(expr).__name__ == "Iterated_Term":
    return get_step_growth(expr.it_expr, var)
  elif hasattr(expr, "terms"):
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
    growths = [get_step_growth(term.it_expr, var) for term in expr.terms]
    if hasattr(expr, "const") and not isinstance(expr.const, int) and expr.const is not expr:
      growths.append(get_step_growth(expr.const, var))
    valid = [g for g in growths if g is not None]
    if valid:
      return max(valid)
    return None
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
    self.is_const = is_const(self.start_val) and is_const(self.num_reps)

    # Ensure step_expr only depends on var
    expr_vars = variables(self.step_expr)
    assert expr_vars.issubset({self.var}), f"step_expr {self.step_expr} contains other variables: {expr_vars}"

  def __repr__(self):
    return f"((λ{self.var} → {self.step_expr})^({self.num_reps}) ({self.start_val}))"

  __str__ = __repr__

  def __eq__(self, other):
    if not isinstance(other, Iterated_Expression):
      return False
    return (
      self.step_expr == other.step_expr
      and self.var == other.var
      and struct_eq(self.start_val, other.start_val)
      and struct_eq(self.num_reps, other.num_reps)
    )

  def try_eval(self):
    return None

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

  def __divmod__(self, other):
    if other == 1:
      return (self, 0)
    raise NotImplementedError("Cannot mod Iterated_Expression by non-1 value")

  def __neg__(self):
    return Iterated_Math([Iterated_Term(self, -1)], 0)

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
    return self.uparrow_size_approx < uparrow_size_approx(other)

  def __gt__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return False
    return self.uparrow_size_approx > uparrow_size_approx(other)

  def __le__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return True
    return self.uparrow_size_approx <= uparrow_size_approx(other)

  def __ge__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return False
    return self.uparrow_size_approx >= uparrow_size_approx(other)

  def __mul__(self, other):
    if other == 0:
      return 0
    return Iterated_Math([Iterated_Term(self, other)], 0)

  def __rmul__(self, other):
    return self.__mul__(other)

  def __add__(self, other):
    if isinstance(other, Iterated_Math):
      return other + self
    if isinstance(other, Iterated_Expression):
      return Iterated_Math([Iterated_Term(self, 1), Iterated_Term(other, 1)], 0)
    return Iterated_Math([Iterated_Term(self, 1)], other)

  def __radd__(self, other):
    return self.__add__(other)

  def __sub__(self, other):
    if isinstance(other, Iterated_Math):
      return (-other) + self
    if isinstance(other, Iterated_Expression):
      return Iterated_Math([Iterated_Term(self, 1), Iterated_Term(other, -1)], 0)
    return Iterated_Math([Iterated_Term(self, 1)], -other)

  def __rsub__(self, other):
    return (-self) + other


class Iterated_Term:
  """A term in an Iterated_Math expression: `coef * it_expr`"""

  def __init__(self, it_expr: Iterated_Expression, coef=1):
    self.it_expr = it_expr
    self.coef = coef

  def copy(self):
    return Iterated_Term(self.it_expr, self.coef)

  def __eq__(self, other):
    return isinstance(other, Iterated_Term) and self.coef == other.coef and self.it_expr == other.it_expr

  def __repr__(self):
    if self.coef == 1:
      return f"{self.it_expr}"
    return f"{self.coef} * {self.it_expr}"

  __str__ = __repr__


def normalize_terms(terms: list[Iterated_Term]) -> list[Iterated_Term]:
  combined: list[Iterated_Term] = []
  for term in terms:
    if term.coef == 0:
      continue
    found = False
    for c in combined:
      if c.it_expr == term.it_expr:
        c.coef += term.coef
        found = True
        break
    if not found:
      combined.append(term.copy())
  combined = [t for t in combined if t.coef != 0]
  try:
    combined.sort(key=lambda t: uparrow_size_approx(t.it_expr), reverse=True)
  except Exception:
    pass
  return combined


class Iterated_Math(NatExpr):
  """A linear combination of Iterated_Expressions + const:
  `coef_1 * it_expr_1 + coef_2 * it_expr_2 + ... + const`
  """

  def __init__(self, it_expr_or_terms, const=0, coef=1):
    terms = []
    actual_const = const
    if isinstance(it_expr_or_terms, (list, tuple)):
      terms = [t.copy() if hasattr(t, "copy") else t for t in it_expr_or_terms]
    elif it_expr_or_terms is not None:
      terms = [Iterated_Term(it_expr_or_terms, coef)]

    # If const happens to be an Iterated_Expression or Iterated_Math, flatten it into terms!
    if isinstance(actual_const, Iterated_Expression):
      terms.append(Iterated_Term(actual_const, 1))
      actual_const = 0
    elif isinstance(actual_const, Iterated_Math):
      terms.extend([t.copy() for t in actual_const.terms])
      actual_const = actual_const.const

    self.terms = normalize_terms(terms)
    self.const = actual_const
    self.is_const = all(is_const(t.it_expr) and is_const(t.coef) for t in self.terms) and is_const(self.const)

  @property
  def it_expr(self):
    """Backwards compatibility property returning single or dominant Iterated_Expression."""
    if len(self.terms) == 1:
      return self.terms[0].it_expr
    elif len(self.terms) == 0:
      return None
    try:
      return max(self.terms, key=lambda t: uparrow_size_approx(t.it_expr)).it_expr
    except Exception:
      return self.terms[0].it_expr

  @property
  def coef(self):
    """Backwards compatibility property returning coefficient."""
    if len(self.terms) == 1:
      return self.terms[0].coef
    elif len(self.terms) == 0:
      return 0
    return 1

  def _copy_terms(self):
    return [t.copy() for t in self.terms]

  def __repr__(self):
    parts = []
    for term in self.terms:
      if term.coef == 1:
        parts.append(f"{term.it_expr}")
      elif term.coef == -1:
        parts.append(f"-{term.it_expr}")
      else:
        parts.append(f"{term.coef} * {term.it_expr}")

    if not parts:
      return repr(self.const)

    s = " + ".join(parts)
    if self.const != 0:
      is_neg_const = (isinstance(self.const, int) and self.const < 0) or getattr(self.const, "sign", 1) < 0
      if is_neg_const:
        s = f"({s} - {-self.const})"
      else:
        s = f"({s} + {self.const})"
    elif len(self.terms) > 1 or (len(self.terms) == 1 and self.terms[0].coef != 1):
      s = f"({s})"
    return s

  __str__ = __repr__

  def __eq__(self, other):
    if not isinstance(other, Iterated_Math):
      return False
    if len(self.terms) != len(other.terms):
      return False
    if not struct_eq(self.const, other.const):
      return False
    return all(t1 == t2 for t1, t2 in zip(self.terms, other.terms))

  def try_eval(self):
    return None

  def min_val(self):
    res = min_val(self.const) if hasattr(self.const, "min_val") else self.const
    for term in self.terms:
      res = res + term.coef * min_val(term.it_expr)
    return res

  def variables(self):
    vars_set = set()
    for term in self.terms:
      vars_set.update(variables(term.it_expr))
    if hasattr(self.const, "variables"):
      vars_set.update(self.const.variables())
    elif hasattr(self.const, "vars"):
      vars_set.update(self.const.vars)
    return vars_set

  def substitute(self, assignment):
    new_terms = [Iterated_Term(substitute(t.it_expr, assignment), substitute(t.coef, assignment)) for t in self.terms]
    return Iterated_Math(new_terms, substitute(self.const, assignment))

  def __add__(self, other):
    if is_simple(other) or isinstance(other, (ExpInt, Expression)):
      return Iterated_Math(self._copy_terms(), self.const + other)

    if isinstance(other, Iterated_Expression):
      new_terms = self._copy_terms()
      new_terms.append(Iterated_Term(other, 1))
      return Iterated_Math(new_terms, self.const)

    if isinstance(other, Iterated_Math):
      new_terms = self._copy_terms() + other._copy_terms()
      return Iterated_Math(new_terms, self.const + other.const)

    return NotImplemented

  def __radd__(self, other):
    return self.__add__(other)

  def __sub__(self, other):
    if is_simple(other) or isinstance(other, (ExpInt, Expression)):
      return Iterated_Math(self._copy_terms(), self.const - other)

    if isinstance(other, Iterated_Expression):
      new_terms = self._copy_terms()
      new_terms.append(Iterated_Term(other, -1))
      return Iterated_Math(new_terms, self.const)

    if isinstance(other, Iterated_Math):
      neg_other_terms = [Iterated_Term(t.it_expr, -t.coef) for t in other.terms]
      new_terms = self._copy_terms() + neg_other_terms
      return Iterated_Math(new_terms, self.const - other.const)

    return NotImplemented

  def __rsub__(self, other):
    return (-self) + other

  def __neg__(self):
    neg_terms = [Iterated_Term(t.it_expr, -t.coef) for t in self.terms]
    return Iterated_Math(neg_terms, -self.const)

  def __mul__(self, other):
    if other == 0:
      return 0
    if is_simple(other):
      new_terms = [Iterated_Term(t.it_expr, t.coef * other) for t in self.terms]
      return Iterated_Math(new_terms, self.const * other)
    return NotImplemented

  def __rmul__(self, other):
    return self.__mul__(other)

  def __mod__(self, other):
    if other == 1:
      return 0
    other = int(other)
    if all(t.coef % other == 0 for t in self.terms):
      return self.const % other
    # TODO: Support general case when coef % other != 0 (by evaluating it_expr % other).
    raise NotImplementedError(f"Cannot mod Iterated_Math by {other}: {self}")

  def __divmod__(self, other):
    if other == 1:
      return (self, 0)
    other = int(other)
    if all(t.coef % other == 0 for t in self.terms):
      q, r = divmod(self.const, other)
      new_terms = [Iterated_Term(t.it_expr, t.coef // other) for t in self.terms]
      return (Iterated_Math(new_terms, q), r)
    # TODO: Support general case when coef % other != 0.
    raise NotImplementedError(f"Cannot divmod Iterated_Math by {other}: {self}")

  def __abs__(self):
    return self

  @property
  def uparrow_size_approx(self):
    sizes = [t.it_expr.uparrow_size_approx for t in self.terms]
    if self.const:
      try:
        if sign(self.const) > 0:
          sizes.append(uparrow_size_approx(self.const))
      except Exception:
        pass
    if sizes:
      return max(sizes)
    return uparrow_size_approx(self.const)

  def __lt__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return True
    return uparrow_size_approx(self) < uparrow_size_approx(other)

  def __gt__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return False
    return uparrow_size_approx(self) > uparrow_size_approx(other)

  def __le__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return True
    return uparrow_size_approx(self) <= uparrow_size_approx(other)

  def __ge__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return False
    return uparrow_size_approx(self) >= uparrow_size_approx(other)
