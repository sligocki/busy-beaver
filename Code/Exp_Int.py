"""Library for representing very large integers of the form: a b^n + c"""

from fractions import Fraction
import functools
import math

from Algebraic_Expression import Expression, min_val, variables, substitute
from Common import is_const
import io_pb2
from Math import gcd, lcm, int_pow, exp_mod, prec_mult, prec_add


# If x < 10^EXP_THRESHOLD, evaluate it as an int
# if x > 10^EXP_THRESHOLD, only consider as formula
EXP_THRESHOLD = 1000
# Fail if we have too many layers of ExpInt
MAX_DEPTH = 2_000


# Standard way to create an ExpInt
def exp_int(base, exponent):
  """Returns either int or ExpInt based on size of exponent."""
  assert isinstance(base, int)
  assert isinstance(exponent, (int, ExpInt, Expression))

  if exponent == 0:
    return 1

  return ExpInt([ExpTerm(base = base, coef = 1, exponent = exponent)],
                const = 0, denom = 1)


class ExpIntException(Exception):
  pass


def is_simple(value):
  """Is `value` a "simple" numeric type (integer or Fraction)."""
  return isinstance(value, (int, Fraction))

def try_eval(x):
  """Return integer value (if it's small enough) or None (if too big)."""
  if isinstance(x, (ExpInt, ExpTerm)):
    (height, top) = x.tower_value
    assert top >= 0, (top, x.formula_str)
    if height == 0:
      return x.sign * top
    else:
      # Too big to represent as `int`
      return None
  elif isinstance(x, int):
    return x
  else:
    return None

def try_simplify(x):
  """Return integer value (if it's small enough) or ExpInt (if too big)."""
  y = try_eval(x)
  if y is not None:
    return y
  else:
    return x

def struct_eq(a, b):
  """Test for structural equality (not math equality)."""
  if is_simple(a) and is_simple(b):
    return a == b
  elif isinstance(a, ExpTerm) and isinstance(b, ExpTerm):
    return (a.base == b.base and a.coef == b.coef and struct_eq(a.exponent, b.exponent))
  elif isinstance(a, ExpInt) and isinstance(b, ExpInt):
    return (a.const == b.const and a.denom == b.denom and len(a.terms) == len(b.terms)
            and all(struct_eq(ta, tb) for (ta, tb) in zip(a.terms, b.terms)))
  else:
    # Cannot compare
    return False

def fractional_height(x):
  (height, top) = tower_value(x)
  assert top > 0, x
  # Invariant: x ≈ 10^^height[^top]
  while top >= 1:
    top = math.log10(top)
    height += 1
  assert 0 <= top < 1, top
  #  10^^2.5 = 10^^2[^10^0.5] = 10^^3[^0.5]
  return height - 1 + top

def tower_value(x):
  """
  Return y such that x ≈ 10^^y. Uses definition for fractional tetration
  as described in https://www.sligocki.com/2022/06/25/ext-up-notation.html
  """
  if isinstance(x, ExpInt):
    return x.tower_value
  else:
    return (0, abs(x))

def sign(x):
  if isinstance(x, ExpInt):
    return x.sign
  else:
    return (x > 0) - (x < 0)

def exp_int_depth(x):
  if isinstance(x, ExpInt):
    return x.depth
  elif isinstance(x, Expression):
    return max((exp_int_depth(y) for y in x.scalars()), default=0)
  else:
    return 0


class ExpTerm:
  """An integer represented by a formula: `a b^n`"""
  def __init__(self, base : int, coef : int, exponent):
    assert isinstance(base, int), base
    assert isinstance(coef, int), coef
    assert isinstance(exponent, (int, ExpInt, Expression)), exponent
    assert coef != 0

    self.base = base
    self.coef = coef
    self.exponent = exponent
    self.normalize()
    self.sign = sign(self.coef)
    self.eval()
    self.formula_str = f"{self.base}^{self.exponent}"
    if self.coef != 1:
      self.formula_str = f"{self.coef} * {self.formula_str}"

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
    # Is this a constant? Or an expression?
    self.is_const = is_const(self.exponent)
    if self.is_const:
      exp_as_int = try_eval(self.exponent)

      if not exp_as_int:
        assert isinstance(self.exponent, ExpInt), self.exponent
        # For large enough exponent, the coeficient and even base don't have much effect.
        (height, top) = self.exponent.tower_value
        assert top >= 0, top
        # self = b^(10^^height[^top]) ~= 10^^(height+1)[^top]
        self.tower_value = (height + 1, top)

      else:
        assert isinstance(exp_as_int, int)
        if exp_as_int < EXP_THRESHOLD:
          # self = value = 10^^0[^value]
          self.tower_value = tower_value(self.coef * self.base**exp_as_int)

        else:
          top = prec_mult(exp_as_int, math.log10(self.base))
          top = prec_add(top, math.log10(abs(self.coef)))
          # self = 10^top = 10^^1[^top]
          self.tower_value = (1, abs(top))

    else:  # not self.is_const
      min_coef = min_val(self.coef)
      if min_coef < 0:
        # Not guaranteed ... but not sure it's worth tracking max_val ...
        self.min_value = -math.inf
      else:
        self.min_value = min_coef * exp_int(self.base, min_val(self.exponent))
      assert is_const(self.min_value), self
      self.vars = variables(self.coef) | variables(self.exponent)

  def min_val(self):
    return self.min_value
  def variables(self):
    return self.vars
  def substitute(self, assignment):
    if self.is_const:
      return self
    new_coef = substitute(self.coef, assignment)
    new_exp = substitute(self.exponent, assignment)
    return new_coef * exp_int(self.base, new_exp)

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
  assert len({term.base for term in terms}) == 1, terms
  if not all(term.is_const for term in terms):
    # For expressions, don't attempt to normalize.
    return terms

  new_terms = []
  prev_exponent = None
  prev_coef = None
  prev_base = None
  for term in sorted(terms, key=lambda t: tower_value(t.exponent), reverse=True):
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
    if self.depth > MAX_DEPTH:
      raise ExpIntException(f"Too many layers of ExpInt: {self.depth}")

    self.formula_str = " + ".join(term.formula_str for term in self.terms)
    if self.const != 0:
      self.formula_str = f"{self.const} + {self.formula_str}"
    if self.denom != 1:
      self.formula_str = f"({self.formula_str})/{self.denom}"
    self.formula_str = f"({self.formula_str})"
    self.eval()

    bases = frozenset(term.base for term in terms)
    assert len(bases) == 1, bases
    self.base = list(bases)[0]

  def normalize(self):
    common = gcd(self.const, self.denom)
    # Force denominator to be postitive
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

  def eval(self):
    self.is_const = all(term.is_const for term in self.terms)
    if self.is_const:
      term_values = [try_eval(term) for term in self.terms]
      if all(term_values):
        # All terms are small enough to fit in `int`s. We can represent the sum
        # percisely here.
        value = (sum(term_values) + self.const) // self.denom
        self.tower_value = tower_value(value)
        self.sign = sign(value)

      else:
        # At least one term is too large to fit in an `int`.
        max_pos_tower = max((term.tower_value for term in self.terms
                             if term.sign > 0), default = tower_value(0))
        max_neg_tower = max((term.tower_value for term in self.terms
                             if term.sign < 0), default = tower_value(0))
        if max_pos_tower == max_neg_tower:
          raise ExpIntException(f"Cannot evalulate sign of ExpInt: {self}    ({max_pos_tower} == {max_neg_tower})")
        self.tower_value = max(max_pos_tower, max_neg_tower)
        if max_neg_tower > max_pos_tower:
          self.sign = -1
        else:
          self.sign = 1

        # Tweak tower value for denom
        if self.denom != 1:
          (height, top) = self.tower_value
          assert height >= 1, self
          if height == 1:
            top = prec_add(top, -math.log10(self.denom))
            self.tower_value = (height, top)

    else:  # not self.is_const
      assert is_const(self.denom), self
      min_terms = [term.min_value for term in self.terms]
      if -math.inf in min_terms:
        self.min_value = -math.inf
      else:
        min_terms = sum(min_terms)
        self.min_value = (min_terms + min_val(self.const)) / self.denom
        assert isinstance(self.min_value, (ExpInt, int)), self
      self.vars = set(variables(self.const) | variables(self.denom))
      for term in self.terms:
        self.vars.update(term.vars)
      self.vars = frozenset(self.vars)

  def min_val(self):
    return self.min_value
  def variables(self):
    return self.vars
  def substitute(self, assignment):
    if self.is_const:
      return self
    numer = sum(term.substitute(assignment) for term in self.terms)
    numer += substitute(self.const, assignment)
    return numer / substitute(self.denom, assignment)

  def __repr__(self):
    return self.formula_str
  def __str__(self):
    return self.formula_str


  # The ability to implement mod on this data structure efficiently is the
  # reason that this class works!
  def __mod__(self, other):
    other_int = try_eval(other)
    if not other_int:
      raise ExpIntException(f"Cannot eval %: {self} % {repr(other)}")

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

    if isinstance(other, Expression):
      return other + self

    raise ExpIntException(f"ExpInt add: unsupported type {type(other)}")

  def __mul__(self, other):
    other = try_simplify(other)

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
        raise ExpIntException("ExpInt mul: base mismatch")

    if isinstance(other, Expression):
      return other * self

    raise ExpIntException(f"ExpInt mul: unsupported type {type(other)}")

  def __truediv__(self, other):
    other_int = try_eval(other)
    if not other_int:
      raise ExpIntException(f"ExpInt truediv: unsupported type {type(other)}")

    return ExpInt(self.terms, self.const, self.denom * other_int)


  # Basic comparision using tower notation.
  def __gt__(self, other):
    assert self.is_const, self
    if other == math.inf:
      return False
    if other == -math.inf:
      return True

    if self.sign < 0:
      return not (-self >= -other)
    if sign(other) < 0:
      # self > 0 > other
      return True

    return self.tower_value > tower_value(other)

  def __ge__(self, other):
    assert self.is_const, self
    if other == math.inf:
      return False
    if other == -math.inf:
      return True

    if self.sign < 0:
      return not (-self > -other)
    if sign(other) < 0:
      # self > 0 > other
      return True

    return self.tower_value >= tower_value(other)

  # Boilerplate
  def __neg__(self):
    return self * -1
  def __sub__(self, other):
    return self + (-other)
  def __rsub__(self, other):
    return (-self) + other
  def __lt__(self, other):
    return not (self >= other)
  def __le__(self, other):
    return not (self > other)
  __radd__ = __add__
  __rmul__ = __mul__
