"""
Library for representing very large integers (ExpInt) of the form:
  (a b^n + c)/d
where a,b,c,d are normal int and n is either an int or ExpInt.
"""

from __future__ import annotations

import math
from fractions import Fraction
from functools import cached_property, cmp_to_key

from Algebraic_Expression import Expression, div, min_val, substitute, variables
from Big_Interval import BigInterval, Knuth10
from Math import exp_mod, gcd, int_pow, lcm, prec_add, prec_mult
from NatExpr import ConstInt, NatExpr, cmp_expr, expr_str, is_const, to_BigInterval

# If x < 10^EXP_THRESHOLD, evaluate it as an int
# if x > 10^EXP_THRESHOLD, only consider as formula
EXP_THRESHOLD = 1000
# Fail if we have too many layers of ExpInt
MAX_DEPTH = 500
# Maximum (recursive) number of ExpTerms in a single ExpInt
MAX_TERMS = 1_000_000
# Experimental gates for adding/subtracting or multiplying two ExpInts
# (controlled by --no-expint-add and --no-expint-mul).
ALLOW_ADD = True
ALLOW_MUL = True


# Standard way to create an ExpInt
def exp_int(base: int, exponent: int | ExpInt | Expression) -> ExpInt:
  """Returns either int or ExpInt based on size of exponent."""
  base = int(base)
  assert isinstance(base, int), base
  assert isinstance(exponent, (int, NatExpr)), exponent

  if exponent == 0:
    return 1

  return ExpInt([ExpTerm(base=base, coef=1, exponent=exponent)], const=0, denom=1)


class ExpIntException(Exception):
  pass


class ExpIntGaveUp(ExpIntException):
  pass


def tex_formula(root: ExpInt | ExpTerm | int) -> str:
  root_res = []
  stack = [(root, False, root_res, [])]
  while stack:
    node, visited, parent_res, my_res = stack.pop()
    if visited:
      if isinstance(node, ExpInt):
        s = " + ".join(my_res)
        if node.const != 0:
          s = rf"{node.const} + {s}"
        if node.denom != 1:
          s = rf"\frac{{ {s} }}{{ {node.denom} }}"
        parent_res.append(s)
      elif isinstance(node, ExpTerm):
        res = rf"{node.base}^{{ {my_res[0]} }}"
        if node.coef != 1:
          res = rf"{node.coef} \cdot {res}"
        parent_res.append(res)
      else:
        parent_res.append(str(node))
    else:
      stack.append((node, True, parent_res, my_res))
      if isinstance(node, ExpInt):
        for term in reversed(node.terms):
          stack.append((term, False, my_res, []))
      elif isinstance(node, ExpTerm):
        stack.append((node.exponent, False, my_res, []))
  return root_res[0] if root_res else str(root)


def is_simple(value) -> bool:
  """Is `value` a "simple" numeric type (integer or Fraction)."""
  return isinstance(value, (int, Fraction, ConstInt))


def try_eval(x: int | NatExpr) -> int | None:
  """Return integer value (if it's small enough) or None (if too big)."""
  if hasattr(x, "try_eval"):
    return x.try_eval()
  elif isinstance(x, int):
    return x
  else:
    return None


def try_simplify(x):
  """Return integer value (if it's small enough) or ExpInt (if too big)."""
  if hasattr(x, "try_simplify"):
    return x.try_simplify()
  y = try_eval(x)
  if y is not None:
    return ConstInt(y) if "ConstInt" in globals() else y
  else:
    return x


def struct_eq(a, b) -> bool:
  """Test for structural equality (not math equality)."""
  stack = [(a, b)]
  while stack:
    x, y = stack.pop()
    if x is y:
      continue
    if is_simple(x) and is_simple(y):
      if x != y:
        return False
    elif isinstance(x, ExpTerm) and isinstance(y, ExpTerm):
      if x.base != y.base or x.coef != y.coef:
        return False
      stack.append((x.exponent, y.exponent))
    elif isinstance(x, ExpInt) and isinstance(y, ExpInt):
      if x.const != y.const or x.denom != y.denom or len(x.terms) != len(y.terms):
        return False
      for tx, ty in zip(x.terms, y.terms):
        stack.append((tx, ty))
    elif isinstance(x, Expression) and isinstance(y, Expression):
      if x != y:
        return False
    elif type(x).__name__ == type(y).__name__:
      tname = type(x).__name__
      if tname == "Iterated_Expression":
        if x.var != y.var or x.step_expr != y.step_expr:
          return False
        stack.append((x.start_val, y.start_val))
        stack.append((x.num_reps, y.num_reps))
      elif tname == "Iterated_Term":
        stack.append((x.coef, y.coef))
        stack.append((x.it_expr, y.it_expr))
      elif tname == "Iterated_Math":
        if len(x.terms) != len(y.terms):
          return False
        stack.append((x.const, y.const))
        for tx, ty in zip(x.terms, y.terms):
          stack.append((tx, ty))
      else:
        return False
    else:
      return False
  return True


def fractional_height(x) -> float:
  val = uparrow_size_approx(x)
  assert val[0] == 2, val
  height, top = val[1], val[2]
  assert top > 0, x
  # Invariant: x ≈ 10^^height[^top]
  while top >= 1:
    top = math.log10(top)
    height += 1
  assert 0 <= top < 1, top
  #  10^^2.5 = 10^^2[^10^0.5] = 10^^3[^0.5]
  return height - 1 + top


def uparrow_size_approx(x):
  """
  Return y such that x ≈ 10^^y. Uses definition for fractional tetration
  as described in https://www.sligocki.com/2022/06/25/ext-up-notation.html
  """
  if hasattr(x, "uparrow_size_approx"):
    return x.uparrow_size_approx
  else:
    return (2, 0, abs(x))


def sign(x) -> int:
  if isinstance(x, ExpInt):
    return x.sign
  else:
    return (x > 0) - (x < 0)


def exp_int_depth(x) -> int:
  if isinstance(x, ExpInt):
    return x.depth
  elif isinstance(x, Expression):
    return max((exp_int_depth(y) for y in x.scalars()), default=0)
  else:
    return 0


class ExpTerm:
  """An integer represented by a formula: `a b^n`"""

  def __setstate__(self, state):
    self.__dict__.update(state)
    self.eval()

  @property
  def uparrow_size_approx(self) -> tuple:
    if "_uparrow_size_approx" not in self.__dict__:
      self.eval()
    return self._uparrow_size_approx

  def try_eval(self) -> int | None:
    if not self.is_const:
      return None
    val = uparrow_size_approx(self)
    top = val[-1]
    # Check isinstance(val[1], int) because val[1] can be a symbolic ExpInt height
    # (from Iterated_Expression); calling val[1] == 0 on an ExpInt would recurse
    # back into ExpInt.__eq__ -> try_eval().
    if val[0] == 2 and isinstance(val[1], int) and val[1] == 0:
      return self.sign * top
    return None

  def _bi_children(self, env):
    return (self.base, self.exponent, self.coef)

  def _bi_combine(self, resolve, env):
    return (resolve(self.base) ** resolve(self.exponent)) * resolve(self.coef)

  def to_BigInterval(self, env=None):
    return to_BigInterval(self, env)

  def __init__(self, base: int, coef: int, exponent):
    assert isinstance(base, int), base
    assert isinstance(coef, int), coef
    assert isinstance(exponent, (int, NatExpr)), exponent
    assert coef != 0

    self.base = base
    self.coef = coef
    self.exponent = exponent
    self.normalize()
    self.sign = sign(self.coef)
    self.eval()
    self.depth = exp_int_depth(self.exponent) + 1

  def normalize(self):
    """Normalize representation"""
    (n, k) = int_pow(self.base)
    if k > 1:
      self.base = n
      self.exponent *= k
    while self.coef % self.base == 0:
      self.coef //= self.base
      self.exponent += 1

  def eval(self):
    self.is_const = is_const(self.exponent)
    # Is this a constant? Or an expression?
    if self.is_const:
      self.vars = frozenset()
      exp_as_int = try_eval(self.exponent)

      if exp_as_int is None:
        assert hasattr(self.exponent, "uparrow_size_approx"), self.exponent
        # For large enough exponent, the coefficient and even base don't have much effect.
        val = self.exponent.uparrow_size_approx
        top = val[-1]
        assert top >= 0, top
        if val[0] == 2:
          # self = b^(10^^height[^top]) ~= 10^^(height+1)[^top]
          self._uparrow_size_approx = (2, val[1] + 1, val[2])
        else:
          # For pentation or higher, adding 1 to the base of the tower is negligible
          self._uparrow_size_approx = val

      else:
        assert isinstance(exp_as_int, int)
        if exp_as_int < EXP_THRESHOLD:
          # self = value = 10^^0[^value]
          self._uparrow_size_approx = uparrow_size_approx(self.coef * self.base**exp_as_int)

        else:
          top = prec_mult(exp_as_int, math.log10(self.base))
          top = prec_add(top, math.log10(abs(self.coef)))
          # self = 10^top = 10^^1[^top]
          self._uparrow_size_approx = (2, 1, abs(top))

    else:  # not self.is_const
      min_coef = min_val(self.coef)
      if min_coef < 0:
        # Not guaranteed ... but not sure it's worth tracking max_val ...
        self.min_value = -math.inf
      else:
        min_exp = min_val(self.exponent)
        min_exp = max(0, min_exp)
        self.min_value = min_coef * exp_int(self.base, min_exp)
      assert is_const(self.min_value), self
      self.vars = variables(self.coef) | variables(self.exponent)

  def min_val(self):
    if self.is_const:
      val = try_eval(self)
      return val if val is not None else ExpInt([self], const=0, denom=1)
    return self.min_value

  def variables(self):
    return self.vars

  def substitute(self, assignment):
    if self.is_const:
      return self
    new_coef = substitute(self.coef, assignment)
    new_exp = substitute(self.exponent, assignment)
    return new_coef * exp_int(self.base, new_exp)

  def mod(self, m: int) -> int:
    return (exp_mod(self.base, self.exponent, m) * self.coef) % m

  def mul_int(self, n: int):
    n = int(n)
    assert isinstance(n, int), n
    assert n != 0
    return ExpTerm(self.base, self.coef * n, self.exponent)

  def div_int(self, n: int):
    assert isinstance(n, int), n
    assert n != 0
    (new_coef, r) = divmod(self.coef, n)
    assert r == 0, (self.coef, n, r)
    return ExpTerm(self.base, new_coef, self.exponent)

  def mul_term(self, other):
    assert isinstance(other, ExpTerm), other
    assert self.base == other.base
    return ExpTerm(self.base, self.coef * other.coef, self.exponent + other.exponent)

  def _str_tokens(self):
    if self.coef != 1:
      return (f"{self.coef} * {self.base}^", self.exponent)
    return (f"{self.base}^", self.exponent)

  @cached_property
  def formula_str(self) -> str:
    return expr_str(self)

  def __repr__(self):
    return self.formula_str

  def __str__(self):
    return self.formula_str


# Maximum bit length of a combined coefficient in normalize_terms (~10^1000).
MAX_COMBINE_BITS = int(EXP_THRESHOLD * math.log2(10))


def _const_exp_diff(e1, e2) -> int | None:
  """If e1 - e2 is an exact integer constant, return it; otherwise return None."""
  if e1 is e2:
    return 0
  v1 = try_eval(e1)
  v2 = try_eval(e2)
  if v1 is not None and v2 is not None:
    return v1 - v2
  if (v1 is None) != (v2 is None):
    return None
  if isinstance(e1, ExpInt) and isinstance(e2, ExpInt):
    if len(e1.terms) != len(e2.terms) or e1.bases != e2.bases:
      return None
    if e1.denom == e2.denom:
      if all(struct_eq(t1, t2) for t1, t2 in zip(e1.terms, e2.terms)):
        diff, rem = divmod(e1.const - e2.const, e1.denom)
        return diff if rem == 0 else None
    else:
      g = gcd(e1.denom, e2.denom)
      ns = e2.denom // g
      no = e1.denom // g
      if all(
        t1.base == t2.base and ns * t1.coef == no * t2.coef and struct_eq(t1.exponent, t2.exponent)
        for t1, t2 in zip(e1.terms, e2.terms)
      ):
        common_denom = e1.denom * ns
        diff, rem = divmod(ns * e1.const - no * e2.const, common_denom)
        return diff if rem == 0 else None
    return None
  if type(e1).__name__ == "Iterated_Math" and type(e2).__name__ == "Iterated_Math":
    if len(e1.terms) == len(e2.terms) and all(struct_eq(t1, t2) for t1, t2 in zip(e1.terms, e2.terms)):
      return _const_exp_diff(e1.const, e2.const)
    return None
  if struct_eq(e1, e2):
    return 0
  return None


def _cmp_abs_exp_terms(t1: ExpTerm, t2: ExpTerm) -> int:
  """Compare |t1| vs |t2| for two constant ExpTerms with the same base."""
  u1 = t1.uparrow_size_approx
  u2 = t2.uparrow_size_approx
  # Use exact comparison when both terms are close enough in uparrow_size_approx
  # that float/truncation rounding could flip their order.
  need_exact = u1 == u2 or (u1[0] == 2 and u1[1] == 1 and u2[0] == 2 and u2[1] == 1 and abs(u1[2] - u2[2]) <= 4)
  if need_exact and t1.base == t2.base:
    d = _const_exp_diff(t1.exponent, t2.exponent)
    if d is None and isinstance(t1.exponent, ExpInt) and isinstance(t2.exponent, ExpInt):
      # Exponents can differ by a non-constant ExpInt (e.g. 5^(A) vs -5^(A - B) where
      # A >> B >> 1), giving identical uparrow_size_approx. Subtracting them cancels
      # matching leading terms at strictly lower depth to reveal the true sign.
      try:
        diff = t1.exponent - t2.exponent
      except ExpIntGaveUp:
        # ExpIntGaveUp signals a complexity/size limit (MAX_DEPTH / MAX_TERMS) and
        # must propagate so Simulator.step can cleanly stop with EXPRESSION_TOO_COMPLEX.
        raise
      except ExpIntException:
        # Other ExpIntExceptions (e.g. sign still undetermined) mean we couldn't
        # resolve the tie; fall back to uparrow_size_approx below.
        diff = None
      if diff is not None:
        if isinstance(diff, int):
          d = diff
        else:
          d_int = try_eval(diff)
          if d_int is not None:
            d = d_int
          else:
            # |e1 - e2| >= 2^EXP_THRESHOLD, so base^|e1 - e2| dwarfs any int coefficients.
            return diff.sign
    if d is not None:
      c1 = abs(t1.coef)
      c2 = abs(t2.coef)
      if d == 0:
        return (c1 > c2) - (c1 < c2)
      flip = False
      if d < 0:
        d = -d
        c1, c2 = c2, c1
        flip = True
      log2_b = math.log2(t1.base)
      # Compare c1 * base^d vs c2
      if (c1.bit_length() - 1) + d * log2_b > c2.bit_length() + 2:
        res = 1
      elif c1.bit_length() + d * log2_b < (c2.bit_length() - 1) - 2:
        res = -1
      else:
        lhs = c1 * (t1.base**d)
        res = (lhs > c2) - (lhs < c2)
      return -res if flip else res
  return (u1 > u2) - (u1 < u2)


def normalize_terms(terms):
  """Simplify sum of ExpTerms by combining ones that we can."""
  if not terms:
    return terms
  if not all(term.is_const for term in terms):
    # For expressions, don't attempt to normalize.
    return terms

  # Allow mixed-base sums (e.g. Tape.get_macro_size() summing blocks built by rules
  # with different bases) by normalizing each base group independently.
  bases = {term.base for term in terms}
  if len(bases) > 1:
    by_base: dict[int, list[ExpTerm]] = {}
    for term in terms:
      by_base.setdefault(term.base, []).append(term)
    combined = []
    for base_terms in by_base.values():
      combined.extend(normalize_terms(base_terms))
    combined.sort(key=lambda t: t.uparrow_size_approx, reverse=True)
    return combined

  # All terms have same base
  base = terms[0].base
  log2_base = math.log2(base)

  int_terms = []
  big_terms = []
  for term in terms:
    val = try_eval(term.exponent)
    if val is not None:
      int_terms.append((val, term))
    else:
      big_terms.append(term)

  new_terms = []

  # 1. Combine terms whose exponents are too large to evaluate as int.
  if big_terms:
    big_terms.sort(key=lambda t: uparrow_size_approx(t.exponent), reverse=True)
    bucket_key = None
    groups = []  # list of [exp, coef]

    def flush_groups():
      for g_exp, g_coef in groups:
        if g_coef:
          new_terms.append(ExpTerm(base, g_coef, g_exp))
      groups.clear()

    for term in big_terms:
      key = uparrow_size_approx(term.exponent)
      if key != bucket_key:
        flush_groups()
        bucket_key = key
      merged = False
      for idx, (g_exp, g_coef) in enumerate(groups):
        d = _const_exp_diff(term.exponent, g_exp)
        if d is None:
          continue
        if d == 0:
          g_coef += term.coef
          if g_coef == 0:
            groups.pop(idx)
          else:
            groups[idx][1] = g_coef
          merged = True
          break
        elif d > 0 and d <= EXP_THRESHOLD and abs(term.coef).bit_length() + d * log2_base <= MAX_COMBINE_BITS:
          g_coef = term.coef * (base**d) + g_coef
          if g_coef == 0:
            groups.pop(idx)
          else:
            groups[idx][1] = g_coef
          merged = True
          break
        elif d < 0 and -d <= EXP_THRESHOLD and abs(g_coef).bit_length() + (-d) * log2_base <= MAX_COMBINE_BITS:
          g_coef = g_coef * (base ** (-d)) + term.coef
          if g_coef == 0:
            groups.pop(idx)
          else:
            groups[idx][0] = term.exponent
            groups[idx][1] = g_coef
          merged = True
          break
      if not merged:
        groups.append([term.exponent, term.coef])
    flush_groups()

  # 2. Combine terms whose exponents evaluate to int.
  if int_terms:
    int_terms.sort(key=lambda pair: pair[0], reverse=True)
    prev_val = None
    prev_exp = None
    prev_coef = None
    for val, term in int_terms:
      if prev_coef is None:
        prev_val = val
        prev_exp = term.exponent
        prev_coef = term.coef
        continue
      d = prev_val - val
      if d == 0:
        prev_coef += term.coef
        if prev_coef == 0:
          prev_coef = None
      elif d <= EXP_THRESHOLD and abs(prev_coef).bit_length() + d * log2_base <= MAX_COMBINE_BITS:
        prev_coef = prev_coef * (base**d) + term.coef
        prev_val = val
        prev_exp = term.exponent
        if prev_coef == 0:
          prev_coef = None
      else:
        new_terms.append(ExpTerm(base, prev_coef, prev_exp))
        prev_val = val
        prev_exp = term.exponent
        prev_coef = term.coef
    if prev_coef:
      new_terms.append(ExpTerm(base, prev_coef, prev_exp))

  return new_terms


class ExpInt(NatExpr):
  """An integer represented by a formula: `(a1 b^n1 + a2 b^n2 + ... + c) / d`"""

  def try_eval(self) -> int | None:
    if not self.is_const:
      return None
    val = uparrow_size_approx(self)
    top = val[-1]
    # Check isinstance(val[1], int) because val[1] can be a symbolic ExpInt height
    # (from Iterated_Expression); calling val[1] == 0 on an ExpInt would recurse
    # back into ExpInt.__eq__ -> try_eval().
    if val[0] == 2 and isinstance(val[1], int) and val[1] == 0:
      return self.sign * top
    return None

  def to_BigInterval(self, env=None):
    return to_BigInterval(self, env)

  def _bi_children(self, env):
    for term in self.terms:
      yield term.base
      yield term.exponent
      if not (isinstance(term.coef, int) and term.coef < 0):
        yield term.coef
    if not (isinstance(self.const, int) and self.const < 0):
      yield self.const
    if self.denom != 1:
      yield self.denom

  def _bi_combine(self, resolve, env):
    pos_bi = BigInterval(0)
    neg_bi = BigInterval(0)
    pos_items = []
    neg_items = []
    for term in self.terms:
      pow_bi = resolve(term.base) ** resolve(term.exponent)
      if isinstance(term.coef, int) and term.coef < 0:
        t_bi = pow_bi * BigInterval(-term.coef)
        neg_bi = neg_bi + t_bi
        neg_items.append((term, t_bi))
      else:
        t_bi = pow_bi * resolve(term.coef)
        pos_bi = pos_bi + t_bi
        pos_items.append((term, t_bi))
    if isinstance(self.const, int) and self.const < 0:
      c_bi = BigInterval(-self.const)
      neg_bi = neg_bi + c_bi
      neg_items.append((None, c_bi))
    else:
      pos_bi = pos_bi + resolve(self.const)
    res = pos_bi - neg_bi
    if neg_items and pos_items and res.lower < pos_bi.lower.div10() and self.is_const and env is None:
      tight_lower = self._tighten_sub_lower(pos_items, neg_items)
      if tight_lower is not None and tight_lower > res.lower:
        res = BigInterval(tight_lower, res.upper)
    if self.denom != 1:
      res = res / resolve(self.denom)
    return res

  def _tighten_sub_lower(self, pos_items, neg_items):
    """Prove a tighter lower bound for pos_bi - neg_bi when interval subtraction loses precision.

    Finds the dominant positive term p* = a* * b^{e*} and verifies that every negative
    summand t_j satisfies |t_j| <= (1 / (2 * M)) * p*, where M = len(neg_items).
    If proven, sum(|t_j|) <= p* / 2, so pos_sum - neg_sum >= p* / 2.
    """
    p_star, p_star_bi = max(pos_items, key=lambda item: cmp_to_key(_cmp_abs_exp_terms)(item[0]))
    if not (isinstance(p_star.coef, int) and p_star.coef > 0 and p_star.base >= 2):
      return None

    m = len(neg_items)
    two_m_bi = BigInterval(2 * m)
    for neg_term, neg_t_bi in neg_items:
      # 1. Fast BigInterval dominance check: 2 * M * |t_j| <= p*
      if (neg_t_bi * two_m_bi).upper <= p_star_bi.lower:
        continue
      # 2. Same-base symbolic exponent difference check: b^{e* - f_j} >= ceil(2 * M * d_j / a*)
      if (
        neg_term is None
        or neg_term.base != p_star.base
        or not isinstance(p_star.exponent, (int, ConstInt, ExpInt))
        or not isinstance(neg_term.exponent, (int, ConstInt, ExpInt))
      ):
        return None
      d_j = -neg_term.coef
      need = (2 * m * d_j + p_star.coef - 1) // p_star.coef
      need_bits = need.bit_length()  # 2^need_bits > need, so b^d >= 2^d >= need for all d >= need_bits
      try:
        diff = p_star.exponent - neg_term.exponent
      except (ExpIntException, TypeError):
        return None
      diff_int = try_eval(diff)
      if diff_int is not None:
        if diff_int < 0:
          return None
        if diff_int < need_bits and p_star.coef * (p_star.base**diff_int) < 2 * m * d_j:
          return None
      else:
        if sign(diff) <= 0:
          return None
        try:
          diff_bi = to_BigInterval(diff)
        except Exception:
          return None
        if diff_bi.lower < Knuth10.upper_bound_from_int(need_bits):
          return None

    return (p_star_bi / BigInterval(2)).lower

  def __init__(self, terms: list[ExpTerm], const: int, denom: int):
    assert terms
    const = int(const)
    assert isinstance(const, int), const
    assert isinstance(denom, int), denom

    self.terms = terms
    self.const = const
    self.denom = denom

    self.normalize()
    self.depth = max(term.depth for term in terms)
    if self.depth > MAX_DEPTH:
      raise ExpIntGaveUp(f"Too many layers of ExpInt: {self.depth}")

    self.eval()

    bases = frozenset(term.base for term in terms)
    self.bases = bases
    self.base = next(iter(bases)) if len(bases) == 1 else None

    # Number of ExpTerms (recursively) inside this one.
    # Once it gets too large, we give up to avoid OOM.
    self.rec_num_terms = len(self.terms)
    for term in self.terms:
      self.rec_num_terms += getattr(term.exponent, "rec_num_terms", 0)
    if self.rec_num_terms > MAX_TERMS:
      raise ExpIntGaveUp(f"Too many subterms of ExpInt: {self.rec_num_terms}")

  def normalize(self):
    common = gcd(self.const, self.denom)
    # Force denominator to be positive
    common = abs(common) * sign(self.denom)
    assert isinstance(common, int), (common, repr(self.denom))
    if common != 1:
      for term in self.terms:
        common = gcd(common, term.coef)
        assert isinstance(common, int), (common, repr(term.coef))
    if common != 1:
      self.const //= common
      self.denom //= common
      self.terms = [term.div_int(common) for term in self.terms]
    assert self.denom > 0, self

  def __int__(self) -> int:
    val = try_eval(self)
    if val is None:
      raise ValueError("Attempt to convert large ExpInt -> int")
    return val

  def eval(self):
    self.is_const = all(term.is_const for term in self.terms)
    if self.is_const:
      term_values = [try_eval(term) for term in self.terms]
      if all(v is not None for v in term_values):
        # All terms are small enough to fit in `int`s. We can represent the sum
        # precisely here.
        value = (sum(term_values) + self.const) // self.denom
        self._uparrow_size_approx = uparrow_size_approx(value)
        self.sign = sign(value)

      else:
        # At least one term is too large to fit in an `int`.
        pos_terms = [term for term in self.terms if term.sign > 0]
        neg_terms = [term for term in self.terms if term.sign < 0]
        max_pos_term = max(pos_terms, key=cmp_to_key(_cmp_abs_exp_terms)) if pos_terms else None
        max_neg_term = max(neg_terms, key=cmp_to_key(_cmp_abs_exp_terms)) if neg_terms else None
        if max_pos_term is None:
          self._uparrow_size_approx = max_neg_term.uparrow_size_approx
          self.sign = -1
        elif max_neg_term is None:
          self._uparrow_size_approx = max_pos_term.uparrow_size_approx
          self.sign = 1
        else:
          cmp_res = _cmp_abs_exp_terms(max_pos_term, max_neg_term)
          if cmp_res == 0:
            raise ExpIntException(
              f"Cannot evaluate sign of ExpInt: {self}    "
              f"({max_pos_term.uparrow_size_approx} == {max_neg_term.uparrow_size_approx})"
            )
          elif cmp_res < 0:
            self._uparrow_size_approx = max_neg_term.uparrow_size_approx
            self.sign = -1
          else:
            self._uparrow_size_approx = max_pos_term.uparrow_size_approx
            self.sign = 1

        # Tweak tower value for denom
        if self.denom != 1:
          val = self.uparrow_size_approx
          if val[0] == 2:
            assert val[1] >= 1, self
            if val[1] == 1:
              top = prec_add(val[2], -math.log10(self.denom))
              self._uparrow_size_approx = (2, 1, top)

    else:  # not self.is_const
      assert is_const(self.denom), self
      min_terms = [term.min_val() for term in self.terms]
      if -math.inf in min_terms:
        self.min_value = -math.inf
      else:
        min_terms = sum(min_terms)
        a = min_terms + min_val(self.const)
        b = self.denom
        if isinstance(a, int):
          self.min_value = a // b
        else:
          self.min_value = a / b
        assert isinstance(self.min_value, (ExpInt, int)), self
      self.vars = set(variables(self.const) | variables(self.denom))
      for term in self.terms:
        self.vars.update(term.vars)
      self.vars = frozenset(self.vars)

  def min_val(self):
    return self.min_value

  def variables(self):
    return self.vars

  def _sub_children(self):
    for term in self.terms:
      if not term.is_const:
        yield term.exponent
    yield self.const
    yield self.denom

  def _sub_combine(self, resolve, assignment):
    numer = 0
    for term in self.terms:
      if term.is_const:
        numer = numer + term.coef * exp_int(term.base, term.exponent)
      else:
        numer = numer + term.coef * exp_int(term.base, resolve(term.exponent))
    numer = numer + resolve(self.const)
    denom = resolve(self.denom)
    if denom == 1:
      return numer
    if isinstance(numer, int) and isinstance(denom, int):
      return div(numer, denom)
    return numer / denom

  def substitute(self, assignment):
    return substitute(self, assignment)

  def tex_formula(self):
    return tex_formula(self)

  def _str_tokens(self):
    tokens = ["("]
    if self.denom != 1:
      tokens.append("(")
    if self.const != 0:
      tokens.append(f"{self.const} + ")
    for i, term in enumerate(self.terms):
      if i > 0:
        tokens.append(" + ")
      tokens.append(term)
    if self.denom != 1:
      tokens.append(f")/{self.denom}")
    tokens.append(")")
    return tokens

  @cached_property
  def formula_str(self) -> str:
    return expr_str(self)

  def __repr__(self):
    return self.formula_str

  def __str__(self):
    return self.formula_str

  # The ability to implement mod on this data structure efficiently is the
  # reason that this class works!

  def __setstate__(self, state):
    self.__dict__.update(state)
    self.eval()

  @property
  def uparrow_size_approx(self) -> tuple:
    if "_uparrow_size_approx" not in self.__dict__:
      self.eval()
    return self._uparrow_size_approx

  def __mod__(self, other):
    other_int = try_eval(other)
    if not other_int:
      raise ExpIntException(f"Cannot eval %: {self} % {other!r}")

    if other_int == 1:
      return 0

    assert isinstance(other_int, int), repr(other_int)
    # (sum(a_i b^k_i) + c) / d = n other + r
    # sum(a_i b^k_i) + c = n (d other) + rd
    # rd = (sum(a_i b^k_i) + c) % (d other)
    m = self.denom * other_int
    terms_rem = sum(term.mod(m) for term in self.terms) % m
    rd = (terms_rem + self.const) % m
    r, rdr = divmod(rd, self.denom)
    assert rdr == 0, f"ExpInt is not an integer: {self}"
    return r % other_int

  def __divmod__(self, other):
    # if other == 1:
    #   return (self, 0)

    r = self % other
    div = (self - r) / other
    return (div, r)

  def __floordiv__(self, other):
    (div, _) = divmod(self, other)
    return div

  def __add__(self, other):
    if is_simple(other):
      return ExpInt(
        terms=self.terms,
        const=self.const + other * self.denom,
        denom=self.denom,
      )

    if isinstance(other, ExpInt):
      other_int = try_eval(other)
      if other_int is not None:
        return self + other_int
      self_int = try_eval(self)
      if self_int is not None:
        return other + self_int
      if not ALLOW_ADD:
        raise ExpIntGaveUp("ExpInt add is disabled (remove --no-expint-add to enable)")
      new_denom = lcm(self.denom, other.denom)
      ns = new_denom // self.denom
      no = new_denom // other.denom
      terms_s = [term.mul_int(ns) for term in self.terms]
      terms_o = [term.mul_int(no) for term in other.terms]
      terms = normalize_terms(terms_s + terms_o)
      if terms:
        return ExpInt(
          terms=terms,
          const=ns * self.const + no * other.const,
          denom=new_denom,
        )
      else:
        # If all ExpTerms cancelled out, return int
        return (ns * self.const + no * other.const) // new_denom

    if isinstance(other, Expression):
      return other + self

    return NotImplemented

  def __mul__(self, other):
    other = try_simplify(other)

    if other == 0:
      return 0

    if is_simple(other):
      return ExpInt(
        terms=[term.mul_int(other) for term in self.terms],
        const=self.const * other,
        denom=self.denom,
      )

    if isinstance(other, ExpInt):
      self_int = try_eval(self)
      if self_int is not None:
        return other * self_int
      if not ALLOW_MUL:
        raise ExpIntGaveUp("ExpInt mul is disabled (remove --no-expint-mul to enable)")
      if self.base is not None and self.base == other.base:
        new_terms = []
        for term_s in self.terms:
          if other.const:
            new_terms.append(term_s.mul_int(other.const))
          for term_o in other.terms:
            new_terms.append(term_s.mul_term(term_o))
        if self.const:
          for term_o in other.terms:
            new_terms.append(term_o.mul_int(self.const))
        new_terms = normalize_terms(new_terms)
        if new_terms:
          return ExpInt(new_terms, self.const * other.const, self.denom * other.denom)
        else:
          return (self.const * other.const) // (self.denom * other.denom)
      else:
        # Raise ExpIntGaveUp (not generic ExpIntException) so Simulator.step cleanly
        # records EXPRESSION_TOO_COMPLEX when rules with different bases interact.
        raise ExpIntGaveUp("ExpInt mul: base mismatch")

    if isinstance(other, Expression):
      return other * self

    return NotImplemented

  def __truediv__(self, other):
    other_int = try_eval(other)
    if not other_int:
      return NotImplemented

    return ExpInt(self.terms, self.const, self.denom * other_int)

  # Basic comparison using tower notation, with exact fallback when towers tie.
  # Without the fallback, two unequal ExpInts with the same uparrow_size_approx
  # compare as neither < nor >, which can cause min(a, b) in rule application to
  # pick the larger value and produce negative block counts.
  def _cmp_other(self, other) -> int:
    c = cmp_expr(self, other)
    if c != 0:
      return c
    if isinstance(other, ExpInt):
      if struct_eq(self, other):
        return 0
      try:
        return sign(self - other)
      except ExpIntException:
        # If the difference's sign cannot be resolved (e.g. pentation/Iterated_Expression
        # exponents), fall back to treating the towers as tied.
        return 0
    return 0

  # Needed so small ExpInts that evaluate to 0 or 1 (e.g. (-5103 + 7 * 3^6)/2 == 0)
  # match int/ConstInt checks such as removing zero-count blocks in _normalize_half_tape.
  def __eq__(self, other):
    if self is other:
      return True
    if not self.is_const:
      return False
    if isinstance(other, (int, float, ConstInt)):
      val = try_eval(self)
      if val is None:
        return False
      return val == (other.val if isinstance(other, ConstInt) else other)
    if isinstance(other, ExpInt):
      if not other.is_const:
        return False
      return self._cmp_other(other) == 0
    return NotImplemented

  def __hash__(self):
    if not self.is_const:
      return id(self)
    val = try_eval(self)
    if val is not None:
      return hash(val)
    return hash(self.sign)

  def __gt__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return False
    return self._cmp_other(other) > 0

  def __ge__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return False
    return self._cmp_other(other) >= 0

  # Boilerplate
  def __neg__(self):
    return self * -1

  def __sub__(self, other):
    return self + (-other)

  def __rsub__(self, other):
    return (-self) + other

  def __lt__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return True
    return self._cmp_other(other) < 0

  def __le__(self, other):
    assert self.is_const, self
    other = NatExpr.wrap(other)
    if other.is_inf:
      return True
    return self._cmp_other(other) <= 0

  __radd__ = __add__
  __rmul__ = __mul__
