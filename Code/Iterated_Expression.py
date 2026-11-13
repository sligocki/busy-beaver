from fractions import Fraction
from functools import cached_property
import math

from Algebraic_Expression import Expression, Variable, min_val, substitute, variables
from Big_Interval import BigInterval, Knuth10
from Exp_Int import ExpInt, ExpTerm, is_simple, sign, struct_eq, uparrow_size_approx
from NatExpr import NatExpr, expr_str, is_const, to_BigInterval


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

  def __setstate__(self, state):
    self.__dict__.update(state)
    self.is_const = is_const(self.start_val) and is_const(self.num_reps)

  def _str_tokens(self):
    return (f"((λ{self.var} → ", self.step_expr, ")^(", self.num_reps, ") (", self.start_val, "))")

  def __repr__(self):
    return expr_str(self)

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

  @cached_property
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

  def _bi_children(self, env):
    return (self.start_val, self.num_reps)

  def _bi_combine(self, resolve, env):
    return _iterated_to_big_interval_from_bounds(self, resolve(self.start_val), resolve(self.num_reps), env)

  def to_BigInterval(self, env=None):
    return to_BigInterval(self, env)


def _ceil_log10_bi(bi):
  v = bi.upper.try_eval()
  if v is not None:
    return BigInterval(0 if v <= 1 else len(str(v - 1)))
  return BigInterval(bi.upper)


def _const_tower_height(c_bi, level_k: int) -> int:
  """Return small t >= 1 such that c_bi <= g_{level_k}^t(10)."""
  cur = BigInterval(10)
  for t in range(1, 20):
    cur = cur.apply_uparrow(level_k)
    if c_bi.upper <= cur.lower:
      return t
  a = c_bi.upper.args
  if level_k == 1 and len(a) <= 2:
    return (a[1] if len(a) == 2 else 0) + 4
  return 100


def _apply_gk_reps(x_k, k: int, n_k, is_upper: bool):
  """Compute lower or upper bound for g_k^{n_k}(x_k)."""
  n_small = n_k.try_eval()
  if n_small is not None and n_small <= 1000:
    cur = x_k
    for _ in range(n_small):
      cur = cur.apply_gk(k, is_upper=is_upper)
    return cur

  if not is_upper:
    # Ensure base >= 10 using at most 2 concrete steps (since g_k(1) = 10)
    n_bi = BigInterval(n_k, n_k)
    while x_k < Knuth10(10) and n_bi.lower > Knuth10(0):
      x_k = x_k.apply_gk(k, is_upper=False)
      n_bi = n_bi - BigInterval(1)
    if n_bi.lower == Knuth10(0):
      return x_k
    n_k = n_bi.lower

  n_bi = BigInterval(n_k, n_k)
  bound = (lambda bi: bi.upper) if is_upper else (lambda bi: bi.lower)
  if len(x_k.args) <= k + 1:
    cur_k = x_k.args[k] if len(x_k.args) == k + 1 else 0
    extra = 3 if is_upper else (2 if (k == 1 and len(x_k.args) == 1 and x_k.args[0] >= 10**10) else 1)
    return bound(n_bi + BigInterval(cur_k + extra)).apply_gk(k + 1, is_upper=is_upper)
  if len(x_k.args) == k + 2 and (is_upper or x_k.args[k + 1] == 1):
    peeled = Knuth10(*x_k.args[: k + 1]) if x_k.args[k + 1] == 1 else Knuth10(*x_k.args[: k + 1], x_k.args[k + 1] - 1)
    return bound(BigInterval(peeled, peeled) + n_bi).apply_gk(k + 1, is_upper=is_upper)
  if not is_upper:
    return max(x_k, (n_bi + BigInterval(1)).lower.apply_gk(k + 1, is_upper=False))
  if (n_bi + BigInterval(2)).upper.apply_gk(k + 1, is_upper=True) < x_k:
    return x_k.safe_upper_bound()
  return (BigInterval(2) * n_bi + BigInterval(2)).upper.apply_gk(k + 1, is_upper=True)


def _eval_tower_upper_bi(bound, level_k: int, x_bi):
  h, m, a = bound
  arg = a if m.upper == Knuth10(0) else m * x_bi + a
  for _ in range(h):
    arg = arg.apply_uparrow(level_k)
  return arg


def _bump_upper(bound, c_bi, level_k: int):
  """Upper bound for c_bi * g_{level_k}^h(M * x + A), with M, A as BigIntervals."""
  h, m, a = bound
  if c_bi.upper <= Knuth10(1):
    return bound
  if h == 0:
    return (0, c_bi * m, c_bi * a)
  log_c = _ceil_log10_bi(c_bi)
  log_v = log_c.upper.try_eval()
  if level_k == 1:
    bump = log_c if h == 1 else (BigInterval(len(str(log_v))) if log_v is not None else log_c)
  else:
    bump = BigInterval(1 if (log_v is not None and log_v <= 1000) else _const_tower_height(c_bi, level_k))
  return (h, m, a + bump)


def _add_upper(u1, u2, level_k: int, x_min_bi):
  h1, m1, a1 = u1
  h2, m2, a2 = u2
  if h1 == 0 and h2 == 0:
    return (0, m1 + m2, a1 + a2)
  if h1 < h2:
    h1, m1, a1, h2, m2, a2 = h2, m2, a2, h1, m1, a1
  if m2.upper == Knuth10(0):
    if a2.upper <= _eval_tower_upper_bi((h1, m1, a1), level_k, x_min_bi).upper:
      return _bump_upper((h1, m1, a1), BigInterval(2), level_k)
    bump = _ceil_log10_bi(a2) + BigInterval(1) if level_k == 1 else BigInterval(_const_tower_height(a2, level_k) + 1)
    return (h1, m1, a1 + bump)
  m_max = m1 if m1.upper >= m2.upper else m2
  a_max = a1 if a1.upper >= a2.upper else a2
  return _bump_upper((h1, m_max, a_max), BigInterval(2), level_k)


def _mul_upper(u1, u2, level_k: int):
  h1, m1, a1 = u1
  h2, m2, a2 = u2
  if m1.upper == Knuth10(0):
    return _bump_upper(u2, a1, level_k)
  if m2.upper == Knuth10(0):
    return _bump_upper(u1, a2, level_k)
  h = max(h1, h2)
  m_max = m1 if m1.upper >= m2.upper else m2
  a_max = a1 if a1.upper >= a2.upper else a2
  if h == 0 or (level_k == 1 and h == 1):
    return (1, BigInterval(2) * m_max, BigInterval(2) * a_max)
  return (h, m_max, a_max + BigInterval(1))


def _tower_upper(expr, var, level_k: int, x_min_bi, env=None):
  """Return (h, M_bi, A_bi) such that expr(x) <= g_{level_k}^h(M_bi * x + A_bi) for all x >= x_min_bi."""
  zero = BigInterval(0)
  one = BigInterval(1)
  if isinstance(expr, int):
    return (0, zero, BigInterval(max(0, expr)))
  if isinstance(expr, Variable):
    if expr == var:
      return (0, one, zero)
    c_u = to_BigInterval(expr, env).upper
    return (0, zero, BigInterval(c_u, c_u))
  if var not in variables(expr):
    c_u = to_BigInterval(expr, env).upper
    return (0, zero, BigInterval(c_u, c_u))

  def coef_bi(c):
    return BigInterval(c) if isinstance(c, int) else BigInterval(to_BigInterval(c, env).upper)

  if isinstance(expr, (Expression, ExpInt, Iterated_Math)):
    c_val = expr.const
    acc = (
      (0, zero, zero) if (isinstance(c_val, int) and c_val <= 0) else _tower_upper(c_val, var, level_k, x_min_bi, env)
    )
    for term in expr.terms:
      if isinstance(term.coef, int) and term.coef <= 0:
        continue
      if isinstance(expr, Expression):
        cur = (0, zero, one)
        for vp in term.vars:
          bu = _tower_upper(vp.var, var, level_k, x_min_bi, env)
          for _ in range(vp.pow):
            cur = _mul_upper(cur, bu, level_k)
      elif isinstance(expr, ExpInt):
        b_log = _ceil_log10_bi(to_BigInterval(term.base, env))
        exp_u = _tower_upper(term.exponent, var, level_k, x_min_bi, env)
        if level_k == 1:
          h_e, m_e, a_e = _bump_upper(exp_u, b_log, 1)
          cur = (h_e + 1, m_e, a_e)
        else:
          h_e, m_e, a_e = exp_u
          le_1 = b_log.upper <= Knuth10(1)
          if h_e == 0:
            bump = 1 if le_1 else _const_tower_height(b_log, level_k)
            cur = (1, m_e, a_e + BigInterval(bump))
          else:
            cur = (h_e, m_e, a_e + BigInterval(1 if le_1 else 2))
      else:
        cur = _tower_upper(term.it_expr, var, level_k, x_min_bi, env)
      acc = _add_upper(acc, _bump_upper(cur, coef_bi(term.coef), level_k), level_k, x_min_bi)
    if isinstance(expr, ExpInt) and expr.denom != 1 and acc[0] == 0:
      d_bi = to_BigInterval(expr.denom, env)
      m_div = zero if acc[1].upper == Knuth10(0) else acc[1] / d_bi
      a_div = zero if acc[2].upper == Knuth10(0) else acc[2] / d_bi
      return (0, m_div, a_div)
    return acc

  if isinstance(expr, Iterated_Expression):
    g_in = get_step_growth(expr.step_expr, expr.var)
    r_u = _tower_upper(expr.num_reps, var, level_k, x_min_bi, env)
    if g_in is None or g_in == (1, 0):
      return r_u
    k_in, m_in = g_in
    assert k_in + 1 <= level_k, (expr, level_k)
    t_s = (
      _const_tower_height(to_BigInterval(expr.start_val, env), max(1, level_k - 1))
      if var not in variables(expr.start_val)
      else 10
    )
    in_u = _tower_upper(expr.step_expr, expr.var, k_in, BigInterval(100), env)
    t_in = _const_tower_height(in_u[1] + in_u[2], k_in) + 2
    h_r, m_r, a_r = r_u
    if k_in + 1 == level_k:
      if h_r == 0:
        m_tot = BigInterval(m_in + 1)
        return (1, m_tot * m_r, m_tot * a_r + BigInterval(t_s + t_in))
      return (h_r + 1, m_r, a_r + BigInterval(2))
    return (max(1, h_r), m_r, a_r + BigInterval(t_s + t_in))

  raise NotImplementedError(f"_tower_upper unsupported for {type(expr)}: {expr}")


def _eval_tower_lower_bi(bound, level_k: int, x_bi):
  h, m, a = bound
  pos = (BigInterval(m.numerator) * x_bi) / BigInterval(m.denominator) if m > 0 else BigInterval(0)
  if isinstance(a, BigInterval):
    arg = pos + a
  elif a >= 0:
    arg = pos + BigInterval(int(a))
  else:
    neg = BigInterval(int(math.ceil(-a)))
    arg = pos - neg if pos.upper >= neg.lower else BigInterval(0)
  for _ in range(h):
    arg = BigInterval(2) ** arg if level_k == 1 else arg.apply_uparrow(level_k)
  return arg


def _tower_lower(expr, var, level_k: int, x_min_bi, env=None):
  """Return (h, m_frac, a) such that expr(x) >= tower_{level_k}(h, m_frac * x + a) for all x >= x_min_bi."""
  if isinstance(expr, int):
    return (0, Fraction(0), Fraction(max(0, expr)))
  if isinstance(expr, Variable):
    if expr == var:
      return (0, Fraction(1), Fraction(0))
    lo = to_BigInterval(expr, env).lower
    v = lo.try_eval()
    return (0, Fraction(0), Fraction(v) if v is not None else BigInterval(lo, lo))
  if var not in variables(expr):
    lo = to_BigInterval(expr, env).lower
    v = lo.try_eval()
    return (0, Fraction(0), Fraction(v) if v is not None else BigInterval(lo, lo))

  def a_lower_knuth(a):
    return a.lower if isinstance(a, BigInterval) else Knuth10(max(0, int(math.floor(a))))

  def pick_better(l1, l2):
    if (l1[0], l1[1]) != (l2[0], l2[1]):
      return l1 if (l1[0], l1[1]) > (l2[0], l2[1]) else l2
    return l1 if a_lower_knuth(l1[2]) >= a_lower_knuth(l2[2]) else l2

  def apply_sub_and_div(pos_l, neg_terms, neg_c, denom):
    h_p, m_p, a_p = pos_l
    if h_p == 0:
      if not isinstance(a_p, Fraction):
        if neg_terms or not isinstance(denom, int):
          return (0, Fraction(0), Fraction(0))
        return (0, Fraction(0), (a_p - BigInterval(neg_c)) / BigInterval(denom))
      a_p -= neg_c
      for nt in neg_terms:
        nu = _tower_upper(nt, var, level_k, x_min_bi, env)
        nu_m, nu_a = nu[1].upper.try_eval(), nu[2].upper.try_eval()
        if nu[0] != 0 or nu_m is None or nu_a is None:
          return (0, Fraction(0), Fraction(0))
        m_p -= nu_m
        a_p -= nu_a
      if denom != 1:
        if not isinstance(denom, int):
          return (0, Fraction(0), Fraction(0))
        m_p /= denom
        a_p /= denom
      return (0, max(Fraction(0), m_p), a_p)

    pos_at_min = _eval_tower_lower_bi(pos_l, level_k, x_min_bi)
    neg_ub = BigInterval(neg_c)
    for nt in neg_terms:
      nu = _tower_upper(nt, var, level_k, x_min_bi, env)
      if nu[0] >= h_p:
        return (0, Fraction(0), Fraction(0))
      neg_ub = neg_ub + _eval_tower_upper_bi(nu, level_k, x_min_bi)
    loss = 0
    if neg_ub.upper > Knuth10(0):
      if BigInterval(2) * neg_ub <= pos_at_min:
        loss += 1
      else:
        return (0, Fraction(0), Fraction(0))
    if denom != 1:
      d_bi = to_BigInterval(denom, env)
      d_val = d_bi.upper.try_eval()
      if level_k == 1 and h_p == 1 and d_val is not None:
        loss += (d_val - 1).bit_length() if d_val > 1 else 0
      elif BigInterval(2) * d_bi <= pos_at_min:
        loss += 1
      else:
        return (0, Fraction(0), Fraction(0))
    return (h_p, m_p, a_p - (BigInterval(loss) if isinstance(a_p, BigInterval) else loss))

  if isinstance(expr, Expression):
    best = (0, Fraction(0), Fraction(0))
    lin_m, lin_a = Fraction(0), Fraction(expr.const) if isinstance(expr.const, int) and expr.const > 0 else Fraction(0)
    neg_exprs = []
    for term in expr.terms:
      if isinstance(term.coef, int) and term.coef < 0:
        neg_exprs.append(Expression(terms=(term.__class__(term.vars, -term.coef),), constant=0))
        continue
      cur = (0, Fraction(0), Fraction(1))
      for vp in term.vars:
        tl = _tower_lower(vp.var, var, level_k, x_min_bi, env)
        if tl[0] > cur[0] or (tl[0] == 0 and tl[1] > cur[1]):
          cur = tl
      if cur[0] == 0:
        c_val = term.coef if isinstance(term.coef, int) else 1
        lin_m += c_val * cur[1]
        lin_a += c_val * (cur[2] if isinstance(cur[2], Fraction) else 0)
      else:
        best = pick_better(best, cur)
    best = pick_better(best, (0, lin_m, lin_a))
    neg_c = -expr.const if isinstance(expr.const, int) and expr.const < 0 else 0
    return best if (not neg_exprs and neg_c == 0) else apply_sub_and_div(best, neg_exprs, neg_c, 1)

  if isinstance(expr, ExpInt):
    best = (0, Fraction(0), Fraction(0))
    neg_exprs = []
    for term in expr.terms:
      if isinstance(term.coef, int) and term.coef < 0:
        neg_exprs.append(ExpInt([ExpTerm(term.base, term.exponent, -term.coef)], 0, 1))
        continue
      if var in variables(term.exponent):
        h_e, m_e, a_e = _tower_lower(term.exponent, var, level_k, x_min_bi, env)
        best = pick_better(best, (h_e + 1 if level_k == 1 else max(1, h_e), m_e, a_e))
      else:
        c_bi = BigInterval(max(1, term.coef)) if isinstance(term.coef, int) else BigInterval(1)
        term_bi = c_bi * (to_BigInterval(term.base, env) ** to_BigInterval(term.exponent, env))
        v = term_bi.lower.try_eval()
        best = pick_better(best, (0, Fraction(0), Fraction(v) if v is not None else BigInterval(term_bi.lower)))
    if best[0] == 0 and isinstance(expr.const, int) and expr.const > 0 and isinstance(best[2], Fraction):
      best = (0, best[1], best[2] + expr.const)
    neg_c = -expr.const if isinstance(expr.const, int) and expr.const < 0 else 0
    return apply_sub_and_div(best, neg_exprs, neg_c, expr.denom)

  if isinstance(expr, Iterated_Math):
    best = (0, Fraction(0), Fraction(0))
    neg_exprs = []
    for t in expr.terms:
      if isinstance(t.coef, int) and t.coef < 0:
        neg_exprs.append(Iterated_Math([Iterated_Term(t.it_expr, -t.coef)], 0))
        continue
      best = pick_better(best, _tower_lower(t.it_expr, var, level_k, x_min_bi, env))
    neg_c = -expr.const if isinstance(expr.const, int) and expr.const < 0 else 0
    return apply_sub_and_div(best, neg_exprs, neg_c, 1)

  if isinstance(expr, Iterated_Expression):
    g_in = get_step_growth(expr.step_expr, expr.var)
    r_l = _tower_lower(expr.num_reps, var, level_k, x_min_bi, env)
    if g_in is None or g_in == (1, 0):
      return r_l
    k_in, m_in = g_in
    if k_in + 1 == level_k:
      s_bi = to_BigInterval(expr.start_val, env) if var not in variables(expr.start_val) else BigInterval(0)
      in_x_min = max(BigInterval(20 if level_k == 2 else 10), s_bi)
      unroll_loss = 2 if s_bi.lower < in_x_min.lower else 0
      in_l = _tower_lower(expr.step_expr, expr.var, k_in, in_x_min, env)
      in_min_v = in_x_min.lower.try_eval()
      ge_x = in_l[1] >= 1 and (
        isinstance(in_l[2], BigInterval)
        or (in_min_v is not None and in_l[1] * in_min_v + int(math.floor(in_l[2])) >= in_min_v)
      )
      if in_l[0] == m_in and ge_x:
        h_r, m_r, a_r = r_l
        return (1, m_in * m_r, m_in * a_r - m_in * unroll_loss) if h_r == 0 else (h_r + 1, m_r, a_r - unroll_loss - 1)
    return r_l

  raise NotImplementedError(f"_tower_lower unsupported for {type(expr)}: {expr}")


def _iterated_to_big_interval(it_expr: Iterated_Expression, env=None):
  start_bi = to_BigInterval(it_expr.start_val, env)
  reps_bi = to_BigInterval(it_expr.num_reps, env)
  return _iterated_to_big_interval_from_bounds(it_expr, start_bi, reps_bi, env)


def _iterated_to_big_interval_from_bounds(it_expr: Iterated_Expression, start_bi, reps_bi, env=None):
  base_env = {} if env is None else dict(env)

  n_hi = reps_bi.upper.try_eval()
  if n_hi is not None and n_hi <= 50:
    n_lo = reps_bi.lower.try_eval()
    assert n_lo is not None
    cur = start_bi
    lo_res = cur.lower if n_lo == 0 else None
    hi_res = cur.upper if n_lo == 0 else None
    for i in range(1, n_hi + 1):
      base_env[it_expr.var] = cur
      cur = to_BigInterval(it_expr.step_expr, base_env)
      if i >= n_lo:
        lo_res = cur.lower if lo_res is None else min(lo_res, cur.lower)
        hi_res = cur.upper if hi_res is None else max(hi_res, cur.upper)
    return BigInterval(lo_res, hi_res)

  if it_expr.var not in variables(it_expr.step_expr):
    return to_BigInterval(it_expr.step_expr, env)

  g_step = get_step_growth(it_expr.step_expr, it_expr.var)
  if g_step is None or g_step == (1, 0):
    if (
      isinstance(it_expr.step_expr, Expression)
      and len(it_expr.step_expr.terms) == 1
      and len(it_expr.step_expr.terms[0].vars) == 1
      and it_expr.step_expr.terms[0].vars[0].pow == 1
    ):
      a, b = it_expr.step_expr.terms[0].coef, it_expr.step_expr.const
      b_neg = isinstance(b, int) and b < 0
      b_bi = BigInterval(-b) if b_neg else to_BigInterval(b, env)
      if a == 1:
        return start_bi - reps_bi * b_bi if b_neg else start_bi + reps_bi * b_bi
      if isinstance(a, int) and a >= 2:
        a_pow = BigInterval(a) ** reps_bi
        delta = (b_bi * (a_pow - BigInterval(1))) / BigInterval(a - 1)
        return a_pow * start_bi - delta if b_neg else a_pow * start_bi + delta

  assert g_step is not None
  step_arrows, step_count = g_step
  if step_arrows == 1 and step_count == 0:
    raise NotImplementedError(f"Unsupported non-linear polynomial step: {it_expr.step_expr}")

  n_lo = reps_bi.lower.try_eval()
  while start_bi.lower < Knuth10(100) and (n_lo is None or n_lo > 4):
    base_env[it_expr.var] = start_bi
    start_bi = to_BigInterval(it_expr.step_expr, base_env)
    reps_bi = reps_bi - BigInterval(1)
    n_lo = reps_bi.lower.try_eval()

  x_min_bi = BigInterval(1) if start_bi.lower < Knuth10(1) else BigInterval(start_bi.lower, start_bi.lower)
  h_u, m_u, a_u = _tower_upper(it_expr.step_expr, it_expr.var, step_arrows, x_min_bi, env)
  h_l, m_l, a_l = _tower_lower(it_expr.step_expr, it_expr.var, step_arrows, x_min_bi, env)

  m_val, a_val, x_min_val = m_u.upper.try_eval(), a_u.upper.try_eval(), x_min_bi.lower.try_eval()
  if m_val is not None and a_val is not None:
    extra = (a_val + x_min_val - 1) // x_min_val if (x_min_val is not None and x_min_val > 0) else 1
    c_bi = BigInterval(max(1, m_val + extra))
  else:
    c_bi = BigInterval(max(1, m_val) if m_val is not None else m_u.upper) + a_u

  l_bi = (
    _ceil_log10_bi(c_bi)
    if step_arrows == 1
    else BigInterval(1 if c_bi.upper <= Knuth10(Knuth10.MAX_A0) else _const_tower_height(c_bi, step_arrows))
  )
  total_h_reps = BigInterval(max(1, h_u)) * reps_bi
  ub_start = c_bi * start_bi + (reps_bi - BigInterval(1)) * l_bi
  hi = _apply_gk_reps(ub_start.upper, step_arrows, total_h_reps.upper, is_upper=True)

  if h_l == 0 or m_l <= 0:
    return BigInterval(start_bi.lower, hi)

  eff_x = x_min_bi.lower.try_eval()
  ok_ge_x = False
  if isinstance(a_l, Fraction) and m_l >= 1:
    if a_l >= 0 or eff_x is None or m_l * eff_x + a_l >= eff_x:
      ok_ge_x = True
    else:
      d_loss = int(math.ceil(-a_l)) + 1
      if step_arrows >= 2 and start_bi.lower >= Knuth10(d_loss + 3):
        start_bi = start_bi - BigInterval(d_loss)
        ok_ge_x = True
      elif step_arrows == 1 and h_l >= 2 and (eff_x is None or eff_x >= d_loss + 10):
        h_l -= 1
        ok_ge_x = True

  if ok_ge_x:
    total_lo_reps = BigInterval(h_l) * reps_bi
    base_lo = (
      (BigInterval(10) if start_bi.lower < Knuth10(20) else start_bi / BigInterval(4)) if step_arrows == 1 else start_bi
    )
    lo = _apply_gk_reps(base_lo.lower, step_arrows, total_lo_reps.lower, is_upper=False)
  elif step_arrows == 1 and m_l > 0:
    k_div = max(4, int(math.ceil(2.0 / (float(m_l) * math.log10(2.0)))))
    base_lo = start_bi / BigInterval(k_div)
    lo = (
      start_bi.lower
      if base_lo.lower < Knuth10(k_div)
      else _apply_gk_reps(base_lo.lower, 1, (BigInterval(h_l) * reps_bi).lower, is_upper=False)
    )
  else:
    lo = start_bi.lower

  return BigInterval(lo, hi)


class Iterated_Term:
  """A term in an Iterated_Math expression: `coef * it_expr`"""

  def __init__(self, it_expr: Iterated_Expression, coef=1):
    self.it_expr = it_expr
    self.coef = coef

  def copy(self):
    return Iterated_Term(self.it_expr, self.coef)

  def __eq__(self, other):
    return isinstance(other, Iterated_Term) and self.coef == other.coef and self.it_expr == other.it_expr

  def _str_tokens(self):
    if self.coef == 1:
      return (self.it_expr,)
    return (self.coef, " * ", self.it_expr)

  def __repr__(self):
    return expr_str(self)

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

  def __setstate__(self, state):
    self.__dict__.update(state)
    if "terms" not in self.__dict__:
      it_expr = self.__dict__.pop("it_expr", None)
      coef = self.__dict__.pop("coef", 1)
      self.terms = [Iterated_Term(it_expr, coef)] if it_expr is not None and coef != 0 else []
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

  def _str_tokens(self):
    if not self.terms:
      return (self.const,)
    tokens = []
    for i, term in enumerate(self.terms):
      if i > 0:
        tokens.append(" + ")
      if term.coef == 1:
        tokens.append(term.it_expr)
      elif term.coef == -1:
        tokens.extend(("-", term.it_expr))
      else:
        tokens.extend((term.coef, " * ", term.it_expr))
    if self.const != 0:
      is_neg_const = (isinstance(self.const, int) and self.const < 0) or getattr(self.const, "sign", 1) < 0
      if is_neg_const:
        return ["(", *tokens, " - ", -self.const, ")"]
      return ["(", *tokens, " + ", self.const, ")"]
    if len(self.terms) > 1 or (len(self.terms) == 1 and self.terms[0].coef != 1):
      return ["(", *tokens, ")"]
    return tokens

  def __repr__(self):
    return expr_str(self)

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

  def to_BigInterval(self, env=None):
    return to_BigInterval(self, env)

  def _bi_children(self, env):
    for term in self.terms:
      yield term.it_expr
      if not (isinstance(term.coef, int) and term.coef < 0):
        yield term.coef
    if not (isinstance(self.const, int) and self.const < 0):
      yield self.const

  def _bi_combine(self, resolve, env):
    pos_bi = BigInterval(0)
    neg_bi = BigInterval(0)
    for term in self.terms:
      term_bi = resolve(term.it_expr)
      coef_val = term.coef
      if isinstance(coef_val, int) and coef_val < 0:
        neg_bi = neg_bi + term_bi * BigInterval(-coef_val)
      else:
        pos_bi = pos_bi + term_bi * resolve(coef_val)
    if isinstance(self.const, int) and self.const < 0:
      neg_bi = neg_bi + BigInterval(-self.const)
    else:
      pos_bi = pos_bi + resolve(self.const)
    return pos_bi - neg_bi

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

  @cached_property
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
