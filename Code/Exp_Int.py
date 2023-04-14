"""Library for representing very large integers of the form: a b^n + c"""

# TODO: Add tests!

from fractions import Fraction
import functools
import math

import io_pb2
from Math import gcd, lcm, int_pow, prec_mult


# If x < 10^^MAX_INT_TOWER, store as int
# If x > 10^^MAX_INT_TOWER, store as ExpInt
MAX_INT_TOWER = 2.5


# Standard way to create an ExpInt
def exp_int(base, exponent):
  """Returns either int or ExpInt based on size of exponent."""
  assert isinstance(base, int)
  assert isinstance(exponent, (int, ExpInt))

  exponent = try_simplify(exponent)
  return try_simplify(
    ExpInt([ExpTerm(base = base, coef = 1, exponent = exponent)],
           const = 0, denom = 1))


def is_simple(value):
  """Is `value` a "simple" numeric type (integer or Fraction)."""
  return isinstance(value, (int, Fraction))

def struct_eq(a, b):
  """Test for structural equality (not math equality)."""
  if is_simple(a) and is_simple(b):
    return a == b
  elif isinstance(a, ExpTerm) and isinstance(b, ExpTerm):
    return (a.base == b.base and a.coef == b.coef and a.exponent == b.exponent)
  elif isinstance(a, ExpInt) and isinstance(b, ExpInt):
    return (a.const == b.const and a.denom == b.denom and len(a.terms) == len(b.terms)
            and all(struct_eq(ta, tb) for (ta, tb) in zip(a.terms, b.terms)))
  else:
    # Cannot compare
    return False

def signed_tower_approx(x):
  if x < 0:
    return -tower_approx(-x)
  else:
    return tower_approx(x)


def tower_approx(x):
  """
  Return y such that x ≈ 10^^y. Uses definition for fractional tetration
  as described in https://www.sligocki.com/2022/06/25/ext-up-notation.html
  """
  if isinstance(x, ExpInt):
    return x.tower_approx
  n = 0
  f = x
  # Invariant: x ≈ 10^^n[^f]
  while f >= 1:
    f = math.log10(f)
    n += 1
  assert 0 <= f < 1, f
  return n - 1 + f

def try_simplify(x):
  """Try to simplify x (turn it into an integer if it's small enough)"""
  if isinstance(x, ExpInt):
    try:
      return x.eval()
    except OverflowError:
      return x
  else:
    return x


@functools.cache
def cycle(b, m):
  """Smallest i >= 0, p > 0 such that b^i+p ≡ b^i (mod m)."""
  vals = {}
  n = 1
  k = 0
  # print(f"   DEBUG: cycle({b}, {m})")
  while n not in vals:
    vals[n] = k
    n = (n * b) % m
    k += 1
  i = vals[n]
  p = k - i
  # print(f"   DEBUG: cycle({b}, {m}) = ({i}, {p})")
  return (i, p)

# Modular arithmetic on ExpInt is actually reasonable once you know the trick.
#   See: https://www.sligocki.com/2022/06/21/bb-6-2-t15.html
#    and https://www.sligocki.com/2022/06/23/period-3.html
def exp_mod(b, k, m):
  """Evaluate b^k % m efficiently."""
  (i, p) = cycle(b, m)
  if k < i:
    return b**k % m
  else:
    kr = (k - i) % p
    return (b**(i+kr)) % m


class ExpTerm:
  """An integer represented by a formula: `a b^n`"""
  def __init__(self, base : int, coef : int, exponent):
    assert isinstance(base, int), base
    assert isinstance(coef, int), coef
    assert isinstance(exponent, (int, ExpInt)), exponent
    assert coef != 0

    self.base = base
    self.coef = coef
    self.exponent = exponent
    self.normalize()

    if isinstance(self.exponent, ExpInt):
      self.depth = self.exponent.depth + 1
      # For large enough exponent, the coeficient and even base don't have much effect.
      self.tower_approx = abs(self.exponent.tower_approx) + 1

    else:
      assert isinstance(self.exponent, int)
      self.depth = 1
      rest = prec_mult(self.exponent, math.log10(self.base))
      rest += int(math.log10(abs(self.coef)))
      # self ≈ 10^rest
      self.tower_approx = tower_approx(rest) + 1

  def normalize(self):
    """Normalize representation"""
    (n, k) = int_pow(self.base)
    if k > 1:
      self.base = n
      self.exponent *= k
    while self.coef % self.base == 0:
      self.coef //= self.base
      self.exponent += 1

  def formula_str(self):
    return f"{self.coef} * {self.base}^{repr(self.exponent)}"

  def eval(self) -> int:
    if self.tower_approx < MAX_INT_TOWER:
      return self.coef * self.base**self.exponent
    else:
      raise OverflowError((self.formula_str(), self.tower_approx))

  def mod(self, m : int) -> int:
    return (exp_mod(self.base, self.exponent, m) * self.coef) % m

  def mul_int(self, n : int):
    assert isinstance(n, int), n
    assert n != 0
    return ExpTerm(self.base, self.coef * n, self.exponent)

  def div_int(self, n : int):
    assert isinstance(n, int), n
    assert n != 0
    (new_coef, r) = divmod(self.coef, n)
    assert r == 0, (self.coef, n, r)
    return ExpTerm(self.base, new_coef, self.exponent)

  def mul_term(self, other):
    assert isinstance(other, ExpTerm), other
    assert self.base == other.base
    return ExpTerm(self.base, self.coef * other.coef,
                   self.exponent + other.exponent)

def normalize_terms(terms):
  """Simplify sum of ExpTerms by combining ones that we can."""
  new_terms = []
  prev_exponent = None
  prev_coef = None
  prev_base = None
  for term in sorted(terms, key=lambda t: tower_approx(t.exponent), reverse=True):
    if struct_eq(term.exponent, prev_exponent):
      assert term.base == prev_base
      prev_coef += term.coef
    else:
      if prev_coef:
        # Don't add term if coef == 0 (or None)
        new_terms.append(ExpTerm(prev_base, prev_coef, prev_exponent))
      prev_base = term.base
      prev_coef = term.coef
      prev_exponent = term.exponent
  if prev_coef:
    new_terms.append(ExpTerm(prev_base, prev_coef, prev_exponent))
  return new_terms


# TODO: Update ExpInt to allow it to be the sum of multiple exponential formula.
#   Supports ex: 1RB0LD_1RC1RF_1LA1RD_0LE1RC_1LC0RA_---0RB
class ExpInt:
  """An integer represented by a formula: `(a1 b^n1 + a2 b^n2 + ... + c) / d` """
  def __init__(self, terms, const : int, denom : int):
    assert terms
    assert isinstance(const, int), const
    assert isinstance(denom, int), denom

    self.terms = terms
    self.const = const
    self.denom = denom
    self.normalize()

    self.depth = max(term.depth for term in terms)

    bases = frozenset(term.base for term in terms)
    assert len(bases) == 1, bases
    self.base = list(bases)[0]

    # Compute approximate tower height.
    try:
      self.tower_approx = signed_tower_approx(self.eval())
    except OverflowError:
      max_pos_tower = max((term.tower_approx for term in self.terms
                           if term.coef > 0), default = 0)
      max_neg_tower = max((term.tower_approx for term in self.terms
                           if term.coef < 0), default = 0)
      assert abs(max_pos_tower - max_neg_tower) > 1, (max_pos_tower, max_neg_tower)
      self.tower_approx = max(max_pos_tower, max_neg_tower)

  def normalize(self):
    common = gcd(self.const, self.denom)
    if common > 1:
      for term in self.terms:
        common = gcd(common, term.coef)
    if common > 1:
      self.const //= common
      self.denom //= common
      self.terms = [term.div_int(common) for term in self.terms]

  def formula_str(self):
    terms_str = " + ".join(term.formula_str() for term in self.terms)
    return f"({terms_str} + {self.const})/{self.denom}"

  __repr__ = formula_str
  __str__ = formula_str

  def eval(self) -> int:
    return (sum(term.eval() for term in self.terms) + self.const) // self.denom

  def tower_approx_str(self):
    return f"10^^{self.tower_approx}"


  # The ability to implement mod on this data structure efficiently is the
  # reason that this class works!
  def __mod__(self, other):
    if other == 1:
      return 0

    if isinstance(other, int):
      # (sum(a_i b^k_i) + c) / d = n other + r
      # sum(a_i b^k_i) + c = n (d other) + rd
      # rd = (sum(a_i b^k_i) + c) % (d other)
      m = self.denom * other
      terms_rem = sum(term.mod(m) for term in self.terms) % m
      rd = (terms_rem + self.const) % m
      r, rdr = divmod(rd, self.denom)
      assert rdr == 0, f"ExpInt is not an integer: {self}"
      return r % other

    raise NotImplementedError(f"Cannot eval %: {self} % {repr(other)}")

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
      return ExpInt(terms = self.terms,
                    const = self.const + other*self.denom,
                    denom = self.denom)

    if isinstance(other, ExpInt):
      new_denom = lcm(self.denom, other.denom)
      ns = new_denom // self.denom
      no = new_denom // other.denom
      terms_s = [term.mul_int(ns) for term in self.terms]
      terms_o = [term.mul_int(no) for term in other.terms]
      terms = normalize_terms(terms_s + terms_o)
      if terms:
        return ExpInt(terms = terms,
                      const = ns * self.const + no * other.const,
                      denom = new_denom)
      else:
        # If all ExpTerms cancelled out, return int
        return (ns * self.const + no * other.const) // new_denom

    raise NotImplementedError(f"ExpInt add: unsupported type {type(other)}")

  def __mul__(self, other):
    if other == 0:
      return 0

    if is_simple(other):
      return ExpInt(terms = [term.mul_int(other) for term in self.terms],
                    const = self.const * other,
                    denom = self.denom)

    if isinstance(other, ExpInt):
      if self.base == other.base:
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
        raise NotImplementedError("ExpInt mul: base mismatch")

    raise NotImplementedError(f"ExpInt mul: unsupported type {type(other)}")

  def __truediv__(self, other):
    if is_simple(other):
      return ExpInt(self.terms, self.const, self.denom * other)
    raise NotImplementedError(f"ExpInt truediv: unsupported type {type(other)}")

  # Basic comparision using tower notation.
  # TODO: This is not 100% accurate b/c tower_approx is ... an approximation
  # but it should be (mostly) good enough.
  def __gt__(self, other):
    if other == math.inf:
      return False
    if other == -math.inf:
      return True

    return self.tower_approx > signed_tower_approx(other)

  def __ge__(self, other):
    if other == math.inf:
      return False
    if other == -math.inf:
      return True

    return self.tower_approx >= signed_tower_approx(other)

  # Boilerplate
  def __neg__(self):
    return self * -1
  def __sub__(self, other):
    return self + (-other)
  def __lt__(self, other):
    return not (self >= other)
  def __le__(self, other):
    return not (self > other)
  __radd__ = __add__
  __rmul__ = __mul__
