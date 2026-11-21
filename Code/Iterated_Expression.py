from fractions import Fraction
from functools import cached_property
import math

from Algebraic_Expression import Expression, Variable, VariableToExpression, div, min_val, substitute, variables
from Big_Interval import BigInterval, Knuth10
from Exp_Int import ExpInt, ExpTerm, is_simple, sign, struct_eq, try_eval, uparrow_size_approx
from Math import carmichael
from NatExpr import ConstInt, NatExpr, cmp_expr, expr_str, is_const, to_BigInterval


class IteratedExprGaveUp(Exception):
  """Raised when an operation on Iterated_Expression / Iterated_Math is unsupported."""

  pass


def _int_val(x):
  if isinstance(x, int):
    return x
  if isinstance(x, ConstInt):
    return x.val
  return None


def get_step_growth(expr, var, _memo=None):
  """
  Returns `(arrows, count)` describing how `expr(var)` grows per application:
  `(arrows, count)` means `expr(var) ≈ (10 ↑^arrows)^count (var)`.
  Returns `None` if `var` is not found in `expr`.
  """
  if _memo is None:
    _memo = _ACTIVE_SG_MEMO if _ACTIVE_SG_MEMO is not None else {}
  root_key = (id(expr), id(var))
  if root_key in _memo:
    return _memo[root_key]

  stack = [(expr, var, 0)]
  while stack:
    cur, cur_var, state = stack.pop()
    key = (id(cur), id(cur_var))
    if key in _memo:
      continue
    tname = type(cur).__name__

    if state == 0:
      if tname == "Iterated_Math":
        children = [term.it_expr for term in cur.terms]
        if hasattr(cur, "const") and not isinstance(cur.const, int) and cur.const is not cur:
          children.append(cur.const)
        if not children:
          _memo[key] = None
        else:
          stack.append((cur, cur_var, 1))
          for ch in children:
            if (id(ch), id(cur_var)) not in _memo:
              stack.append((ch, cur_var, 0))
      elif tname == "Iterated_Term":
        ch = cur.it_expr
        if (id(ch), id(cur_var)) in _memo:
          _memo[key] = _memo[(id(ch), id(cur_var))]
        else:
          stack.append((cur, cur_var, 1))
          stack.append((ch, cur_var, 0))
      elif hasattr(cur, "terms"):
        children = list(cur.terms)
        if hasattr(cur, "const") and not isinstance(cur.const, int) and cur.const is not cur:
          children.append(cur.const)
        if not children:
          _memo[key] = None
        else:
          stack.append((cur, cur_var, 1))
          for ch in children:
            if (id(ch), id(cur_var)) not in _memo:
              stack.append((ch, cur_var, 0))
      elif hasattr(cur, "vars") and isinstance(cur.vars, (list, tuple)):
        children = list(cur.vars)
        if hasattr(cur, "coef") and not isinstance(cur.coef, int):
          children.append(cur.coef)
        if not children:
          _memo[key] = None
        else:
          stack.append((cur, cur_var, 1))
          for ch in children:
            if (id(ch), id(cur_var)) not in _memo:
              stack.append((ch, cur_var, 0))
      elif hasattr(cur, "var") and not hasattr(cur, "step_expr"):
        v = cur.var
        if v == cur_var:
          _memo[key] = (1, 0)
        elif hasattr(v, "exponent"):
          ch = v.exponent
          if (id(ch), id(cur_var)) in _memo:
            g = _memo[(id(ch), id(cur_var))]
            _memo[key] = ((1, g[1] + 1) if g[0] == 1 else g) if g is not None else None
          else:
            stack.append((cur, cur_var, 1))
            stack.append((ch, cur_var, 0))
        else:
          _memo[key] = None
      elif hasattr(cur, "exponent"):
        ch = cur.exponent
        if (id(ch), id(cur_var)) in _memo:
          g = _memo[(id(ch), id(cur_var))]
          _memo[key] = ((1, g[1] + 1) if g[0] == 1 else g) if g is not None else None
        else:
          stack.append((cur, cur_var, 1))
          stack.append((ch, cur_var, 0))
      elif tname == "Iterated_Expression":
        stack.append((cur, cur_var, 1))
        if (id(cur.num_reps), id(cur_var)) not in _memo:
          stack.append((cur.num_reps, cur_var, 0))
      else:
        _memo[key] = None
    elif state == 1:
      res = None
      if tname == "Iterated_Math":
        growths = [_memo[(id(term.it_expr), id(cur_var))] for term in cur.terms]
        if hasattr(cur, "const") and not isinstance(cur.const, int) and cur.const is not cur:
          growths.append(_memo[(id(cur.const), id(cur_var))])
        valid = [g for g in growths if g is not None]
        if valid:
          res = max(valid)
      elif tname == "Iterated_Term":
        res = _memo[(id(cur.it_expr), id(cur_var))]
      elif hasattr(cur, "terms"):
        growths = [_memo[(id(term), id(cur_var))] for term in cur.terms]
        if hasattr(cur, "const") and not isinstance(cur.const, int) and cur.const is not cur:
          growths.append(_memo[(id(cur.const), id(cur_var))])
        valid = [g for g in growths if g is not None]
        if valid:
          res = max(valid)
      elif hasattr(cur, "vars") and isinstance(cur.vars, (list, tuple)):
        growths = [_memo[(id(vp), id(cur_var))] for vp in cur.vars]
        if hasattr(cur, "coef") and not isinstance(cur.coef, int):
          growths.append(_memo[(id(cur.coef), id(cur_var))])
        valid = [g for g in growths if g is not None]
        if valid:
          res = max(valid)
      elif hasattr(cur, "var") and not hasattr(cur, "step_expr"):
        g = _memo[(id(cur.var.exponent), id(cur_var))]
        if g is not None:
          res = (1, g[1] + 1) if g[0] == 1 else g
      elif hasattr(cur, "exponent"):
        g = _memo[(id(cur.exponent), id(cur_var))]
        if g is not None:
          res = (1, g[1] + 1) if g[0] == 1 else g
      elif tname == "Iterated_Expression":
        g_reps = _memo[(id(cur.num_reps), id(cur_var))]
        if g_reps is not None:
          if (id(cur.step_expr), id(cur.var)) not in _memo:
            stack.append((cur, cur_var, 2))
            stack.append((cur.step_expr, cur.var, 0))
            continue
          g_step = _memo[(id(cur.step_expr), id(cur.var))] or (1, 1)
          arr_f = g_step[0] + 1
          arr_N, count_N = g_reps
          if arr_f > arr_N:
            res = (arr_f, 1)
          elif arr_f == arr_N:
            res = (arr_N, count_N + 1)
          else:
            res = g_reps
      _memo[key] = res
    else:  # state == 2 for Iterated_Expression
      g_reps = _memo[(id(cur.num_reps), id(cur_var))]
      g_step = _memo[(id(cur.step_expr), id(cur.var))] or (1, 1)
      arr_f = g_step[0] + 1
      arr_N, count_N = g_reps
      if arr_f > arr_N:
        res = (arr_f, 1)
      elif arr_f == arr_N:
        res = (arr_N, count_N + 1)
      else:
        res = g_reps
      _memo[key] = res

  return _memo[root_key]


def get_depth(expr, var):
  """
  Returns the exponentiation depth of `var` within `expr`.
  Returns None if `var` is not found.
  """
  g = get_step_growth(expr, var)
  if g is None:
    return None
  return g[1] if g[0] == 1 else g[0]


def _unwrap_const_expr(x):
  while isinstance(x, Expression) and x.is_const:
    x = x.const
  return x


def _expr_frac_denom(expr: Expression) -> int:
  d = 1
  if isinstance(expr.const, Fraction):
    d = math.lcm(d, expr.const.denominator)
  for term in expr.terms:
    if isinstance(term.coef, Fraction):
      d = math.lcm(d, term.coef.denominator)
  return d


def _req_mod(expr, var, m: int, max_mod: int = 100_000) -> int:
  """Return modulus k on `var` sufficient to determine `expr(var) % m` (above Carmichael tails)."""
  if m <= 1:
    return 1
  expr = _unwrap_const_expr(expr)
  if var not in variables(expr):
    return 1
  if isinstance(expr, Variable):
    assert expr == var
    return m
  if isinstance(expr, Expression):
    d = _expr_frac_denom(expr)
    m_num = m * d
    if m_num > max_mod * 100:
      raise IteratedExprGaveUp(f"Modulus too large in _req_mod: {m_num}")
    res = 1
    for term in expr.terms:
      has_var_in_vars = any(vp.var == var for vp in term.vars)
      has_var_in_coef = var in variables(term.coef)
      if not has_var_in_vars and not has_var_in_coef:
        continue
      if isinstance(term.coef, (int, Fraction)):
        c = int(term.coef * d)
        g = math.gcd(m_num, abs(c))
        m_term = m_num // g
        if m_term == 1:
          continue
        if has_var_in_vars:
          res = math.lcm(res, m_term)
      else:
        if has_var_in_vars:
          res = math.lcm(res, m_num)
        if has_var_in_coef:
          res = math.lcm(res, _req_mod(term.coef, var, m_num, max_mod))
    if var in variables(expr.const):
      res = math.lcm(res, _req_mod(expr.const, var, m_num, max_mod))
    return res
  if isinstance(expr, ExpInt):
    m_num = m * expr.denom
    if m_num > max_mod * 100:
      raise IteratedExprGaveUp(f"Modulus too large in _req_mod: {m_num}")
    res = 1
    for term in expr.terms:
      if var not in term.vars:
        continue
      if isinstance(term.coef, int):
        g = math.gcd(m_num, abs(term.coef))
        m_term = m_num // g
        if m_term == 1:
          continue
      else:
        m_term = m_num
        if var in variables(term.coef):
          res = math.lcm(res, _req_mod(term.coef, var, m_num, max_mod))
      kp, _k0 = carmichael(m_term)
      res = math.lcm(res, _req_mod(term.exponent, var, kp, max_mod))
    if var in variables(expr.const):
      res = math.lcm(res, _req_mod(expr.const, var, m_num, max_mod))
    return res
  raise IteratedExprGaveUp(f"Unsupported expression type in _req_mod: {type(expr).__name__}")


def _closure_mod(step_expr, var, target_mod: int, max_mod: int = 100_000) -> int:
  L = target_mod
  while True:
    req = _req_mod(step_expr, var, L, max_mod=max_mod)
    new_L = math.lcm(L, req)
    if new_L == L:
      return L
    if new_L > max_mod:
      raise IteratedExprGaveUp(f"Closure modulus exceeded {max_mod} for mod {target_mod}")
    L = new_L


def _exponents_above_tail(expr, var, m: int, x_lb: int) -> bool:
  """Check whether all ExpTerm exponents in `expr` are >= Carmichael tail k0 for all var >= x_lb."""
  if m <= 1:
    return True
  expr = _unwrap_const_expr(expr)
  if var not in variables(expr):
    return True
  if isinstance(expr, Variable):
    return True
  if isinstance(expr, Expression):
    d = _expr_frac_denom(expr)
    m_num = m * d
    for term in expr.terms:
      if var in variables(term.coef):
        if not _exponents_above_tail(term.coef, var, m_num, x_lb):
          return False
    if var in variables(expr.const):
      if not _exponents_above_tail(expr.const, var, m_num, x_lb):
        return False
    return True
  if isinstance(expr, ExpInt):
    m_num = m * expr.denom
    for term in expr.terms:
      if var not in term.vars:
        continue
      if isinstance(term.coef, int):
        g = math.gcd(m_num, abs(term.coef))
        m_term = m_num // g
        if m_term == 1:
          continue
      else:
        m_term = m_num
        if var in variables(term.coef):
          if not _exponents_above_tail(term.coef, var, m_num, x_lb):
            return False
      kp, k0 = carmichael(m_term)
      shifted_exp = term.exponent if x_lb == 0 else substitute(term.exponent, {var: VariableToExpression(var) + x_lb})
      if _unwrap_const_expr(min_val(shifted_exp)) < k0:
        return False
      if not _exponents_above_tail(term.exponent, var, kp, x_lb):
        return False
    if var in variables(expr.const):
      if not _exponents_above_tail(expr.const, var, m_num, x_lb):
        return False
    return True
  return False


def _eval_mod(expr, var, x_mod: int, m: int) -> int:
  """Evaluate `expr(x) % m` given `x ≡ x_mod (mod L)` (assuming all exponents >= Carmichael tails)."""
  if m <= 1:
    return 0
  expr = _unwrap_const_expr(expr)
  if var not in variables(expr):
    return int(expr % m)
  if isinstance(expr, Variable):
    assert expr == var
    return x_mod % m
  if isinstance(expr, Expression):
    d = _expr_frac_denom(expr)
    m_num = m * d
    if isinstance(expr.const, Fraction):
      total = int(expr.const * d) % m_num
    else:
      total = (_eval_mod(expr.const, var, x_mod, m_num) * d) % m_num
    for term in expr.terms:
      var_part = 1
      for vp in term.vars:
        v_mod = _eval_mod(vp.var, var, x_mod, m_num)
        var_part = (var_part * pow(v_mod, vp.pow, m_num)) % m_num
      if isinstance(term.coef, Fraction):
        c_mod = int(term.coef * d) % m_num
      else:
        c_mod = (_eval_mod(term.coef, var, x_mod, m_num) * d) % m_num
      total = (total + c_mod * var_part) % m_num
    q, rem = divmod(total, d)
    if rem != 0:
      raise IteratedExprGaveUp(f"Non-integer Expression in _eval_mod: {expr}")
    return q % m
  if isinstance(expr, ExpInt):
    m_num = m * expr.denom
    total = _eval_mod(expr.const, var, x_mod, m_num)
    for term in expr.terms:
      if var not in term.vars:
        total = (total + term.mod(m_num)) % m_num
      elif isinstance(term.coef, int):
        g = math.gcd(m_num, abs(term.coef))
        m_term = m_num // g
        if m_term == 1:
          continue
        kp, k0 = carmichael(m_term)
        e_mod = _eval_mod(term.exponent, var, x_mod, kp)
        kn = (e_mod - k0) % kp + k0
        p_mod = pow(term.base, kn, m_term)
        total = (total + term.coef * p_mod) % m_num
      else:
        kp, k0 = carmichael(m_num)
        c_mod = _eval_mod(term.coef, var, x_mod, m_num)
        e_mod = _eval_mod(term.exponent, var, x_mod, kp)
        kn = (e_mod - k0) % kp + k0
        p_mod = pow(term.base, kn, m_num)
        total = (total + c_mod * p_mod) % m_num
    q, rem = divmod(total, expr.denom)
    if rem != 0:
      raise IteratedExprGaveUp(f"Non-integer ExpInt in _eval_mod: {expr}")
    return q % m
  raise IteratedExprGaveUp(f"Unsupported expression type in _eval_mod: {type(expr).__name__}")


def _lower_bound_int(val, cap: int = 1000) -> int:
  val = _unwrap_const_expr(val)
  v = try_eval(val)
  if v is not None:
    return v
  if val >= cap:
    return cap
  mv = _unwrap_const_expr(min_val(val))
  mv_int = try_eval(mv)
  if mv_int is not None:
    return mv_int
  return 0


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

  def try_eval(self):
    return None

  @property
  def const(self):
    # This is a hack so Expression(..., const=Iterated_Expression) doesn't break
    return self

  def _min_children(self):
    return (self.start_val,)

  def _min_combine(self, resolve):
    return resolve(self.start_val)

  def min_val(self):
    # Assuming f(x) >= x, min(f^N(x)) >= min(x)
    return min_val(self)

  def _var_children(self):
    return (self.start_val, self.num_reps)

  def _var_combine(self, resolve):
    return resolve(self.start_val) | resolve(self.num_reps)

  def variables(self):
    return variables(self)

  def _sub_children(self):
    return (self.start_val, self.num_reps)

  def _sub_combine(self, resolve, assignment):
    return Iterated_Expression(
      self.step_expr,
      self.var,
      resolve(self.start_val),
      resolve(self.num_reps),
    )

  def substitute(self, assignment):
    return substitute(self, assignment)

  def __mod__(self, other):
    other = int(other)
    if other == 1:
      return 0
    if not self.is_const:
      raise IteratedExprGaveUp(f"Cannot mod non-const Iterated_Expression: {self}")

    cache = self.__dict__.get("_mod_cache")
    if cache is not None and other in cache:
      return cache[other]

    res = self._compute_mod(other)
    if cache is None:
      cache = {}
      self._mod_cache = cache
    cache[other] = res
    return res

  def _compute_mod(self, other: int) -> int:
    start_val = _unwrap_const_expr(self.start_val)
    num_reps = _unwrap_const_expr(self.num_reps)
    n_int = try_eval(num_reps)
    if n_int == 0:
      return int(start_val % other)
    if n_int == 1:
      return int(_unwrap_const_expr(substitute(self.step_expr, {self.var: start_val})) % other)

    L = _closure_mod(self.step_expr, self.var, other)

    # Advance concrete steps until all ExpTerm exponents are guaranteed >= their Carmichael tails.
    cur_val = start_val
    rem_reps = num_reps
    x_lb = _lower_bound_int(cur_val)
    warmup_seen = {}
    warmup_seq = []
    max_warmup = 50
    while not _exponents_above_tail(self.step_expr, self.var, L, x_lb):
      rem_int = try_eval(rem_reps)
      if rem_int == 0:
        return int(cur_val % other)
      v_cur = try_eval(cur_val)
      if v_cur is not None:
        if v_cur in warmup_seen:
          c_start = warmup_seen[v_cur]
          c_len = len(warmup_seq) - c_start
          if c_len == 1:
            return warmup_seq[c_start] % other
          idx = c_start + int(rem_reps % c_len)
          return warmup_seq[idx] % other
        warmup_seen[v_cur] = len(warmup_seq)
        warmup_seq.append(v_cur)
      if len(warmup_seq) >= max_warmup:
        raise IteratedExprGaveUp(f"Warmup exceeded {max_warmup} steps for {self} % {other}")
      cur_val = _unwrap_const_expr(substitute(self.step_expr, {self.var: cur_val}))
      rem_reps = rem_reps - 1
      x_lb = _lower_bound_int(cur_val)

    # Ensure future iterates remain >= x_lb (trivial if x_lb <= 0).
    if x_lb > 0:
      shifted_step = substitute(self.step_expr, {self.var: VariableToExpression(self.var) + x_lb})
      if _unwrap_const_expr(min_val(shifted_step)) < x_lb:
        raise IteratedExprGaveUp(f"Step expression may drop below tail threshold {x_lb}: {self}")

    rem_int = try_eval(rem_reps)
    if rem_int == 0:
      return int(cur_val % other)

    r = int(cur_val % L)
    seen = {}
    seq = []
    while r not in seen:
      if rem_int is not None and len(seq) == rem_int:
        return r % other
      seen[r] = len(seq)
      seq.append(r)
      r = _eval_mod(self.step_expr, self.var, r, L)

    cycle_start = seen[r]
    cycle_len = len(seq) - cycle_start
    if rem_int is not None and rem_int < cycle_start:
      return seq[rem_int] % other
    if rem_int is None and rem_reps < cycle_start:
      return seq[int(rem_reps)] % other
    if cycle_len == 1:
      return seq[cycle_start] % other
    idx = cycle_start + int((rem_reps - cycle_start) % cycle_len)
    return seq[idx] % other

  def __divmod__(self, other):
    if other == 1:
      return (self, 0)
    raise IteratedExprGaveUp(f"Cannot divmod Iterated_Expression by {other}: {self}")

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
    n_val = try_eval(self.num_reps)
    if n_val is not None:
      if val_start[0] == arr and isinstance(val_start[1], (int, float)):
        return (arr, val_start[1] + n_val * step_count, *val_start[2:])
      total_reps = n_val * step_count if step_count > 1 else n_val
      return (arr, total_reps, top_start)

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
    return cmp_expr(self, other) < 0

  def __gt__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return False
    return cmp_expr(self, other) > 0

  def __le__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return True
    return cmp_expr(self, other) <= 0

  def __ge__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return False
    return cmp_expr(self, other) >= 0

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


_CONST_TOWER_CACHE: dict[tuple[int, int], list[Knuth10]] = {}


def _const_tower_height(c_bi, level_k: int) -> int:
  """Return small t >= 1 such that c_bi <= g_{level_k}^t(10)."""
  key = (Knuth10.C, level_k)
  thresholds = _CONST_TOWER_CACHE.get(key)
  if thresholds is None:
    thresholds = []
    cur = Knuth10(10)
    for _ in range(1, 20):
      cur = cur.apply_gk(level_k, is_upper=False)
      thresholds.append(cur)
    _CONST_TOWER_CACHE[key] = thresholds
  u = c_bi.upper
  for t, thresh in enumerate(thresholds, 1):
    if u <= thresh:
      return t
  a = u.args
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


_ACTIVE_TU_MEMO: dict | None = None
_ACTIVE_TL_MEMO: dict | None = None
_ACTIVE_SG_MEMO: dict | None = None
_BI_100 = BigInterval(100)


def _env_cache_key(env):
  if not env:
    return ()
  return tuple(
    sorted(
      (id(k), v.lower.args, v.upper.args) if isinstance(v, BigInterval) else (id(k), id(v)) for k, v in env.items()
    )
  )


def _tower_upper(expr, var, level_k: int, x_min_bi, env=None, _memo=None):
  """Return (h, M_bi, A_bi) such that expr(x) <= g_{level_k}^h(M_bi * x + A_bi) for all x >= x_min_bi."""
  if _memo is None:
    _memo = _ACTIVE_TU_MEMO if _ACTIVE_TU_MEMO is not None else {}
  env_key = _env_cache_key(env)
  zero = BigInterval(0)
  one = BigInterval(1)

  def make_key(e, v, lk, xm):
    return (id(e), id(v), lk, xm.lower.args, xm.upper.args, env_key)

  def coef_bi(c):
    c_int = _int_val(c)
    return BigInterval(c_int) if c_int is not None else BigInterval(to_BigInterval(c, env).upper)

  root_key = make_key(expr, var, level_k, x_min_bi)
  if root_key in _memo:
    return _memo[root_key]

  stack = [(expr, var, level_k, x_min_bi, False, None)]
  while stack:
    cur_expr, cur_var, cur_k, cur_x_min, visited, payload = stack.pop()
    key = make_key(cur_expr, cur_var, cur_k, cur_x_min)
    if key in _memo:
      continue

    if not visited:
      if isinstance(cur_expr, int):
        _memo[key] = (0, zero, BigInterval(max(0, cur_expr)))
        continue
      if isinstance(cur_expr, Variable):
        if cur_expr == cur_var:
          _memo[key] = (0, one, zero)
        else:
          c_u = to_BigInterval(cur_expr, env).upper
          _memo[key] = (0, zero, BigInterval(c_u, c_u))
        continue
      if cur_var not in variables(cur_expr):
        c_u = to_BigInterval(cur_expr, env).upper
        _memo[key] = (0, zero, BigInterval(c_u, c_u))
        continue

      if isinstance(cur_expr, (Expression, ExpInt, Iterated_Math)):
        stack.append((cur_expr, cur_var, cur_k, cur_x_min, True, None))
        c_val = cur_expr.const
        c_int = _int_val(c_val)
        if not (c_int is not None and c_int <= 0):
          if make_key(c_val, cur_var, cur_k, cur_x_min) not in _memo:
            stack.append((c_val, cur_var, cur_k, cur_x_min, False, None))
        for term in cur_expr.terms:
          t_c = _int_val(term.coef)
          if t_c is not None and t_c <= 0:
            continue
          if isinstance(cur_expr, Expression):
            for vp in term.vars:
              if make_key(vp.var, cur_var, cur_k, cur_x_min) not in _memo:
                stack.append((vp.var, cur_var, cur_k, cur_x_min, False, None))
          elif isinstance(cur_expr, ExpInt):
            if make_key(term.exponent, cur_var, cur_k, cur_x_min) not in _memo:
              stack.append((term.exponent, cur_var, cur_k, cur_x_min, False, None))
          else:
            if make_key(term.it_expr, cur_var, cur_k, cur_x_min) not in _memo:
              stack.append((term.it_expr, cur_var, cur_k, cur_x_min, False, None))
      elif isinstance(cur_expr, Iterated_Expression):
        g_in = get_step_growth(cur_expr.step_expr, cur_expr.var)
        stack.append((cur_expr, cur_var, cur_k, cur_x_min, True, g_in))
        if make_key(cur_expr.num_reps, cur_var, cur_k, cur_x_min) not in _memo:
          stack.append((cur_expr.num_reps, cur_var, cur_k, cur_x_min, False, None))
        if g_in is not None and g_in != (1, 0):
          k_in, _ = g_in
          assert k_in + 1 <= cur_k, (cur_expr, cur_k)
          if make_key(cur_expr.step_expr, cur_expr.var, k_in, _BI_100) not in _memo:
            stack.append((cur_expr.step_expr, cur_expr.var, k_in, _BI_100, False, None))
      else:
        raise NotImplementedError(f"_tower_upper unsupported for {type(cur_expr)}: {cur_expr}")
    else:
      if isinstance(cur_expr, (Expression, ExpInt, Iterated_Math)):
        c_val = cur_expr.const
        c_int = _int_val(c_val)
        acc = (
          (0, zero, zero) if (c_int is not None and c_int <= 0) else _memo[make_key(c_val, cur_var, cur_k, cur_x_min)]
        )
        for term in cur_expr.terms:
          t_c = _int_val(term.coef)
          if t_c is not None and t_c <= 0:
            continue
          if isinstance(cur_expr, Expression):
            cur = (0, zero, one)
            for vp in term.vars:
              bu = _memo[make_key(vp.var, cur_var, cur_k, cur_x_min)]
              for _ in range(vp.pow):
                cur = _mul_upper(cur, bu, cur_k)
          elif isinstance(cur_expr, ExpInt):
            b_log = _ceil_log10_bi(to_BigInterval(term.base, env))
            exp_u = _memo[make_key(term.exponent, cur_var, cur_k, cur_x_min)]
            if cur_k == 1:
              h_e, m_e, a_e = _bump_upper(exp_u, b_log, 1)
              cur = (h_e + 1, m_e, a_e)
            else:
              h_e, m_e, a_e = exp_u
              le_1 = b_log.upper <= Knuth10(1)
              if h_e == 0:
                bump = 1 if le_1 else _const_tower_height(b_log, cur_k)
                cur = (1, m_e, a_e + BigInterval(bump))
              else:
                cur = (h_e, m_e, a_e + BigInterval(1 if le_1 else 2))
          else:
            cur = _memo[make_key(term.it_expr, cur_var, cur_k, cur_x_min)]
          acc = _add_upper(acc, _bump_upper(cur, coef_bi(term.coef), cur_k), cur_k, cur_x_min)
        if isinstance(cur_expr, ExpInt) and _int_val(cur_expr.denom) != 1 and acc[0] == 0:
          d_bi = to_BigInterval(cur_expr.denom, env)
          m_div = zero if acc[1].upper == Knuth10(0) else acc[1] / d_bi
          a_div = zero if acc[2].upper == Knuth10(0) else acc[2] / d_bi
          _memo[key] = (0, m_div, a_div)
        else:
          _memo[key] = acc
      else:  # Iterated_Expression
        g_in = payload
        r_u = _memo[make_key(cur_expr.num_reps, cur_var, cur_k, cur_x_min)]
        if g_in is None or g_in == (1, 0):
          _memo[key] = r_u
        else:
          k_in, m_in = g_in
          t_s = (
            _const_tower_height(to_BigInterval(cur_expr.start_val, env), max(1, cur_k - 1))
            if cur_var not in variables(cur_expr.start_val)
            else 10
          )
          in_u = _memo[make_key(cur_expr.step_expr, cur_expr.var, k_in, _BI_100)]
          t_in = _const_tower_height(in_u[1] + in_u[2], k_in) + 2
          h_r, m_r, a_r = r_u
          if k_in + 1 == cur_k:
            if h_r == 0:
              m_tot = BigInterval(m_in + 1)
              _memo[key] = (1, m_tot * m_r, m_tot * a_r + BigInterval(t_s + t_in))
            else:
              _memo[key] = (h_r + 1, m_r, a_r + BigInterval(2))
          else:
            _memo[key] = (max(1, h_r), m_r, a_r + BigInterval(t_s + t_in))

  return _memo[root_key]


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


def _tower_lower(expr, var, level_k: int, x_min_bi, env=None, _memo=None, _upper_memo=None):
  """Return (h, m_frac, a) such that expr(x) >= tower_{level_k}(h, m_frac * x + a) for all x >= x_min_bi."""
  if _memo is None:
    _memo = _ACTIVE_TL_MEMO if _ACTIVE_TL_MEMO is not None else {}
  if _upper_memo is None:
    _upper_memo = _ACTIVE_TU_MEMO if _ACTIVE_TU_MEMO is not None else {}
  env_key = _env_cache_key(env)

  def make_key(e, v, lk, xm):
    return (id(e), id(v), lk, xm.lower.args, xm.upper.args, env_key)

  def a_lower_knuth(a):
    return a.lower if isinstance(a, BigInterval) else Knuth10(max(0, int(math.floor(a))))

  def pick_better(l1, l2):
    if (l1[0], l1[1]) != (l2[0], l2[1]):
      return l1 if (l1[0], l1[1]) > (l2[0], l2[1]) else l2
    return l1 if a_lower_knuth(l1[2]) >= a_lower_knuth(l2[2]) else l2

  def apply_sub_and_div(pos_l, neg_terms, neg_c, denom, cur_var, cur_k, cur_x_min):
    h_p, m_p, a_p = pos_l
    denom_int = _int_val(denom)
    if h_p == 0:
      if not isinstance(a_p, Fraction):
        if neg_terms or denom_int is None:
          return (0, Fraction(0), Fraction(0))
        return (0, Fraction(0), (a_p - BigInterval(neg_c)) / BigInterval(denom_int))
      a_p -= neg_c
      for nt in neg_terms:
        nu = _tower_upper(nt, cur_var, cur_k, cur_x_min, env, _upper_memo)
        nu_m, nu_a = nu[1].upper.try_eval(), nu[2].upper.try_eval()
        if nu[0] != 0 or nu_m is None or nu_a is None:
          return (0, Fraction(0), Fraction(0))
        m_p -= nu_m
        a_p -= nu_a
      if denom_int != 1:
        if denom_int is None:
          return (0, Fraction(0), Fraction(0))
        m_p /= denom_int
        a_p /= denom_int
      return (0, max(Fraction(0), m_p), a_p)

    pos_at_min = _eval_tower_lower_bi(pos_l, cur_k, cur_x_min)
    neg_ub = BigInterval(neg_c)
    for nt in neg_terms:
      nu = _tower_upper(nt, cur_var, cur_k, cur_x_min, env, _upper_memo)
      if nu[0] >= h_p:
        return (0, Fraction(0), Fraction(0))
      neg_ub = neg_ub + _eval_tower_upper_bi(nu, cur_k, cur_x_min)
    loss = 0
    if neg_ub.upper > Knuth10(0):
      if (BigInterval(2) * neg_ub).upper <= pos_at_min.lower:
        loss += 1
      else:
        return (0, Fraction(0), Fraction(0))
    if denom != 1:
      d_bi = to_BigInterval(denom, env)
      d_val = d_bi.upper.try_eval()
      if cur_k == 1 and h_p == 1 and d_val is not None:
        loss += (d_val - 1).bit_length() if d_val > 1 else 0
      elif (BigInterval(2) * d_bi).upper <= pos_at_min.lower:
        loss += 1
      else:
        return (0, Fraction(0), Fraction(0))
    return (h_p, m_p, a_p - (BigInterval(loss) if isinstance(a_p, BigInterval) else loss))

  root_key = make_key(expr, var, level_k, x_min_bi)
  if root_key in _memo:
    return _memo[root_key]

  stack = [(expr, var, level_k, x_min_bi, False, None)]
  while stack:
    cur_expr, cur_var, cur_k, cur_x_min, visited, payload = stack.pop()
    key = make_key(cur_expr, cur_var, cur_k, cur_x_min)
    if key in _memo:
      continue

    if not visited:
      if isinstance(cur_expr, int):
        _memo[key] = (0, Fraction(0), Fraction(max(0, cur_expr)))
        continue
      if isinstance(cur_expr, Variable):
        if cur_expr == cur_var:
          _memo[key] = (0, Fraction(1), Fraction(0))
        else:
          lo = to_BigInterval(cur_expr, env).lower
          v = lo.try_eval()
          _memo[key] = (0, Fraction(0), Fraction(v) if v is not None else BigInterval(lo, lo))
        continue
      if cur_var not in variables(cur_expr):
        lo = to_BigInterval(cur_expr, env).lower
        v = lo.try_eval()
        _memo[key] = (0, Fraction(0), Fraction(v) if v is not None else BigInterval(lo, lo))
        continue

      if isinstance(cur_expr, Expression):
        stack.append((cur_expr, cur_var, cur_k, cur_x_min, True, None))
        for term in cur_expr.terms:
          t_c = _int_val(term.coef)
          if t_c is not None and t_c < 0:
            continue
          for vp in term.vars:
            if make_key(vp.var, cur_var, cur_k, cur_x_min) not in _memo:
              stack.append((vp.var, cur_var, cur_k, cur_x_min, False, None))
      elif isinstance(cur_expr, ExpInt):
        stack.append((cur_expr, cur_var, cur_k, cur_x_min, True, None))
        for term in cur_expr.terms:
          t_c = _int_val(term.coef)
          if t_c is not None and t_c < 0:
            continue
          if cur_var in variables(term.exponent):
            if make_key(term.exponent, cur_var, cur_k, cur_x_min) not in _memo:
              stack.append((term.exponent, cur_var, cur_k, cur_x_min, False, None))
      elif isinstance(cur_expr, Iterated_Math):
        stack.append((cur_expr, cur_var, cur_k, cur_x_min, True, None))
        for t in cur_expr.terms:
          t_c = _int_val(t.coef)
          if t_c is not None and t_c < 0:
            continue
          if make_key(t.it_expr, cur_var, cur_k, cur_x_min) not in _memo:
            stack.append((t.it_expr, cur_var, cur_k, cur_x_min, False, None))
      elif isinstance(cur_expr, Iterated_Expression):
        g_in = get_step_growth(cur_expr.step_expr, cur_expr.var)
        if g_in is not None and g_in != (1, 0) and g_in[0] + 1 == cur_k:
          k_in, _ = g_in
          s_bi = (
            to_BigInterval(cur_expr.start_val, env) if cur_var not in variables(cur_expr.start_val) else BigInterval(0)
          )
          min_thresh = 20 if cur_k == 2 else 10
          unroll_loss = 0
          if cur_var not in variables(cur_expr.start_val):
            step_env = {} if env is None else dict(env)
            while s_bi.lower < Knuth10(min_thresh) and unroll_loss < 2:
              step_env[cur_expr.var] = s_bi
              s_bi = to_BigInterval(cur_expr.step_expr, step_env)
              unroll_loss += 1
          else:
            unroll_loss = 2
          in_x_min = (
            BigInterval(min_thresh) if s_bi.lower < Knuth10(min_thresh) else BigInterval(s_bi.lower, s_bi.lower)
          )
          stack.append((cur_expr, cur_var, cur_k, cur_x_min, True, (g_in, in_x_min, unroll_loss)))
          if make_key(cur_expr.step_expr, cur_expr.var, k_in, in_x_min) not in _memo:
            stack.append((cur_expr.step_expr, cur_expr.var, k_in, in_x_min, False, None))
        else:
          stack.append((cur_expr, cur_var, cur_k, cur_x_min, True, (g_in, None, 0)))
        if make_key(cur_expr.num_reps, cur_var, cur_k, cur_x_min) not in _memo:
          stack.append((cur_expr.num_reps, cur_var, cur_k, cur_x_min, False, None))
      else:
        raise NotImplementedError(f"_tower_lower unsupported for {type(cur_expr)}: {cur_expr}")
    else:
      if isinstance(cur_expr, Expression):
        best = (0, Fraction(0), Fraction(0))
        lin_m = Fraction(0)
        c_int = _int_val(cur_expr.const)
        lin_a = Fraction(c_int) if c_int is not None and c_int > 0 else Fraction(0)
        neg_exprs = []
        for term in cur_expr.terms:
          t_c = _int_val(term.coef)
          if t_c is not None and t_c < 0:
            neg_exprs.append(Expression(terms=(term.__class__(term.vars, -t_c),), constant=0))
            continue
          cur = (0, Fraction(0), Fraction(1))
          for vp in term.vars:
            tl = _memo[make_key(vp.var, cur_var, cur_k, cur_x_min)]
            if tl[0] > cur[0] or (tl[0] == 0 and tl[1] > cur[1]):
              cur = tl
          if cur[0] == 0:
            c_val = t_c if t_c is not None else 1
            lin_m += c_val * cur[1]
            lin_a += c_val * (cur[2] if isinstance(cur[2], Fraction) else 0)
          else:
            best = pick_better(best, cur)
        best = pick_better(best, (0, lin_m, lin_a))
        neg_c = -c_int if c_int is not None and c_int < 0 else 0
        _memo[key] = (
          best
          if (not neg_exprs and neg_c == 0)
          else apply_sub_and_div(best, neg_exprs, neg_c, 1, cur_var, cur_k, cur_x_min)
        )
      elif isinstance(cur_expr, ExpInt):
        best = (0, Fraction(0), Fraction(0))
        neg_exprs = []
        for term in cur_expr.terms:
          t_c = _int_val(term.coef)
          if t_c is not None and t_c < 0:
            neg_exprs.append(ExpInt([ExpTerm(term.base, term.exponent, -t_c)], 0, 1))
            continue
          if cur_var in variables(term.exponent):
            h_e, m_e, a_e = _memo[make_key(term.exponent, cur_var, cur_k, cur_x_min)]
            best = pick_better(best, (h_e + 1 if cur_k == 1 else h_e, m_e, a_e))
          else:
            c_bi = BigInterval(max(1, t_c)) if t_c is not None else BigInterval(1)
            term_bi = c_bi * (to_BigInterval(term.base, env) ** to_BigInterval(term.exponent, env))
            v = term_bi.lower.try_eval()
            best = pick_better(best, (0, Fraction(0), Fraction(v) if v is not None else BigInterval(term_bi.lower)))
        c_int = _int_val(cur_expr.const)
        if best[0] == 0 and c_int is not None and c_int > 0 and isinstance(best[2], Fraction):
          best = (0, best[1], best[2] + c_int)
        neg_c = -c_int if c_int is not None and c_int < 0 else 0
        _memo[key] = apply_sub_and_div(best, neg_exprs, neg_c, cur_expr.denom, cur_var, cur_k, cur_x_min)
      elif isinstance(cur_expr, Iterated_Math):
        best = (0, Fraction(0), Fraction(0))
        neg_exprs = []
        for t in cur_expr.terms:
          t_c = _int_val(t.coef)
          if t_c is not None and t_c < 0:
            neg_exprs.append(Iterated_Math([Iterated_Term(t.it_expr, -t_c)], 0))
            continue
          best = pick_better(best, _memo[make_key(t.it_expr, cur_var, cur_k, cur_x_min)])
        c_int = _int_val(cur_expr.const)
        neg_c = -c_int if c_int is not None and c_int < 0 else 0
        _memo[key] = apply_sub_and_div(best, neg_exprs, neg_c, 1, cur_var, cur_k, cur_x_min)
      else:  # Iterated_Expression
        g_in, in_x_min, unroll_loss = payload
        r_l = _memo[make_key(cur_expr.num_reps, cur_var, cur_k, cur_x_min)]
        if g_in is None or g_in == (1, 0) or in_x_min is None:
          _memo[key] = r_l
        else:
          k_in, m_in = g_in
          in_l = _memo[make_key(cur_expr.step_expr, cur_expr.var, k_in, in_x_min)]
          in_min_v = in_x_min.lower.try_eval()
          ge_x = in_l[1] >= 1 and (
            isinstance(in_l[2], BigInterval)
            or in_l[2] >= 0
            or (in_min_v is not None and in_l[1] * in_min_v + int(math.floor(in_l[2])) >= in_min_v)
            or (
              in_min_v is None
              and in_l[1] > 1
              and in_x_min.lower >= BigInterval(int(math.ceil(-in_l[2] / (in_l[1] - 1))) + 1).lower
            )
          )
          if in_l[0] == m_in and ge_x:
            h_r, m_r, a_r = r_l
            _memo[key] = (
              (1, m_in * m_r, m_in * a_r - m_in * unroll_loss) if h_r == 0 else (h_r + 1, m_r, a_r - unroll_loss - 1)
            )
          else:
            _memo[key] = r_l

  return _memo[root_key]


def _iterated_to_big_interval(it_expr: Iterated_Expression, env=None):
  start_bi = to_BigInterval(it_expr.start_val, env)
  reps_bi = to_BigInterval(it_expr.num_reps, env)
  return _iterated_to_big_interval_from_bounds(it_expr, start_bi, reps_bi, env)


def _iterated_to_big_interval_from_bounds(it_expr: Iterated_Expression, start_bi, reps_bi, env=None):
  global _ACTIVE_TU_MEMO, _ACTIVE_TL_MEMO, _ACTIVE_SG_MEMO
  owns_memos = _ACTIVE_TU_MEMO is None
  if owns_memos:
    _ACTIVE_TU_MEMO = {}
    _ACTIVE_TL_MEMO = {}
    _ACTIVE_SG_MEMO = {}
  try:
    return _iterated_to_big_interval_from_bounds_impl(it_expr, start_bi, reps_bi, env)
  finally:
    if owns_memos:
      _ACTIVE_TU_MEMO = None
      _ACTIVE_TL_MEMO = None
      _ACTIVE_SG_MEMO = None


def _iterated_to_big_interval_from_bounds_impl(it_expr: Iterated_Expression, start_bi, reps_bi, env=None):
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
  tu_memo = _ACTIVE_TU_MEMO
  tl_memo = _ACTIVE_TL_MEMO
  h_u, m_u, a_u = _tower_upper(it_expr.step_expr, it_expr.var, step_arrows, x_min_bi, env, tu_memo)
  h_l, m_l, a_l = _tower_lower(it_expr.step_expr, it_expr.var, step_arrows, x_min_bi, env, tl_memo, tu_memo)

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
      if struct_eq(c.it_expr, term.it_expr):
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

  def try_eval(self):
    return None

  def _min_children(self):
    for term in self.terms:
      yield term.it_expr
      yield term.coef
    yield self.const

  def _min_combine(self, resolve):
    res = resolve(self.const)
    for term in self.terms:
      res = res + resolve(term.coef) * resolve(term.it_expr)
    return res

  def min_val(self):
    return min_val(self)

  def _var_children(self):
    for term in self.terms:
      yield term.it_expr
      yield term.coef
    yield self.const

  def _var_combine(self, resolve):
    vars_set = set()
    for term in self.terms:
      vars_set.update(resolve(term.it_expr))
      vars_set.update(resolve(term.coef))
    vars_set.update(resolve(self.const))
    return frozenset(vars_set)

  def variables(self):
    return variables(self)

  def _sub_children(self):
    for term in self.terms:
      yield term.it_expr
      yield term.coef
    yield self.const

  def _sub_combine(self, resolve, assignment):
    new_terms = [Iterated_Term(resolve(t.it_expr), resolve(t.coef)) for t in self.terms]
    return Iterated_Math(new_terms, resolve(self.const))

  def substitute(self, assignment):
    return substitute(self, assignment)

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
    if is_simple(other) or isinstance(other, (ExpInt, Expression)):
      new_terms = [Iterated_Term(t.it_expr, t.coef * other) for t in self.terms]
      return Iterated_Math(new_terms, self.const * other)
    return NotImplemented

  def __rmul__(self, other):
    return self.__mul__(other)

  def __truediv__(self, other):
    other = int(other) if isinstance(other, NatExpr) else other
    assert isinstance(other, int), (self, other, type(other))
    if other == 0:
      raise ZeroDivisionError("Cannot divide Iterated_Math by 0")
    if other == 1:
      return self
    new_terms = [Iterated_Term(t.it_expr, div(t.coef, other)) for t in self.terms]
    return Iterated_Math(new_terms, div(self.const, other))

  def __mod__(self, other):
    if other == 1:
      return 0
    other = int(other)
    terms_rem = sum((t.coef % other) * (t.it_expr % other) for t in self.terms if t.coef % other != 0)
    return (terms_rem + (self.const % other)) % other

  def __divmod__(self, other):
    if other == 1:
      return (self, 0)
    other = int(other)
    if all(t.coef % other == 0 for t in self.terms):
      q, r = divmod(self.const, other)
      new_terms = [Iterated_Term(t.it_expr, t.coef // other) for t in self.terms]
      return (Iterated_Math(new_terms, q), r)
    # TODO: Support general case when coef % other != 0.
    raise IteratedExprGaveUp(f"Cannot divmod Iterated_Math by {other}: {self}")

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
    return cmp_expr(self, other) < 0

  def __gt__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return False
    return cmp_expr(self, other) > 0

  def __le__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return True
    return cmp_expr(self, other) <= 0

  def __ge__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return False
    return cmp_expr(self, other) >= 0
