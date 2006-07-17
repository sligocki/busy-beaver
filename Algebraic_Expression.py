from __future__ import division

import copy

class Unknown:
  """An algebraic unknown (e.g. x or n)"""
  num_unknowns = 0
  def __init__(self):
    """Creates a new unknown w/ unique ID number."""
    self.id = Unknown.num_unknowns
    Unknown.num_unknowns += 1
  def __repr__(self):
    if self.id <= 25:
      return "%c" % (self.id + 97)
    else:
      return "<x%d>" % self.id
  def __eq__(self, other):
    return self.id == other.id
  def __hash__(self):
    return hash(self.id)

class Term:
  """An algebraic term (product of a scalar and unknown - e.g. 3x or -n)"""
  def __init__(self, coef=1, unknown=None):
    self.coef = coef
    if unknown is not None:
      self.unknown = unknown
    else:
      self.unknown = Unknown()
  def __repr__(self):
    if self.coef == 1:
      return `self.unknown`
    elif self.coef == -1:
      return "-"+`self.unknown`
    else:
      return `self.coef`+`self.unknown`
  def imul(self, scalar):
    self.coef *= scalar
  def itruediv(self, scalar):
    if not isinstance(self.coef, Algebraic_Expression) and \
       self.coef % scalar == 0:
      self.coef //= scalar
    else:
      self.coef /= scalar
  def copy(self):
    return copy.copy(self)

class Expression:
  """An algebraic expression (sum of terms and a single constant - e.g. 3n + x - 2)"""
  def __init__(self, const=0, terms=None):
    self.const = const
    if terms is not None:
      self.terms = terms
    else:
      self.terms = []
  def __repr__(self):
    r = ""
    for t in self.terms:
      r += `t`+" + "
    # If we have a nonzero constant or no terms, print sum(terms) + const
    if self.const or not r:
      return r+`self.const`
    # Otherwise, omit the " + 0"
    else:
      return r[:-3]
  def imul(self, scalar):
    """Multiply expression by scalar"""
    # expr * 0 -> 0
    if scalar == 0:
      self.const = 0
      self.terms = []
    # (5x + 3n - 2) * -4 -> -20x - 12n + 8
    else:
      self.const *= scalar
      for t in self.terms:
        t.imul(scalar)
  def itruediv(self, scalar):
    """Divides expression be scalar"""
    if scalar == 0:
      raise ZeroDivisionError, "Algebraic_Expression division by zero"
    while isinstance(self.const, Algebraic_Expression):
      temp, self.const = self.const, 0
      self.iadd(temp.expr)
    self.const /= scalar
    for term in self.terms:
      term.itruediv(scalar)
  def iadd(self, expr):
    """Add another expression to this one"""
    self.const += expr.const
    self.append_terms(expr.terms)
    self.terms.sort(key=(lambda x: x.unknown.id))
  def append_terms(self, new_terms):
    """
    i = j = 0
    while i < len(self.terms) and j < len(new_terms):
      if self.terms[i].unknown.id == new_terms[j].unknown.id:
        self.terms[i].coef += new_terms[j].coef
        if self.terms[i].coef == 0:
          del self.terms[i]
        i += 1; j += 1
      elif self.terms[i].unknown.id < new_terms[j].unknown.id:
        i += 1
      else:
        self.terms.insert(i, new_terms[j].copy())
        i += 1; j += 1
    if j < len(new_terms):
      for t in new_terms[j:]:
        self.terms.append(t.copy())
    """
    for t_new in new_terms:
      # If t_new has the same unknown as a term already in self.terms, combine them.
      for t_old, i in zip(self.terms, xrange(len(self.terms))):
        if t_new.unknown == t_old.unknown:
          t_old.coef += t_new.coef
          if t_old.coef == 0:
            del self.terms[i] # del t_old if it is 0
          break
      # If t_new has an unknown not in self.terms, append a copy of it.
      else:
        self.terms.append(t_new.copy())
  def copy(self):
    new = Expression(self.const, [])
    for t in self.terms:
      new.terms.append(t.copy())
    return new

def is_scalar(value):
  return not isinstance(value, Algebraic_Expression)

class Algebraic_Expression:
  """Algebraic Expression type"""
  def __init__(self, convert):
    if isinstance(convert, Algebraic_Expression):
      self.expr = convert.expr.copy()
    else:
      self.expr = Expression(convert)
  def __repr__(self):
    rep = `self.expr`
    if "+" in rep:
      return "("+rep+")"
    else:
      return `self.expr`
  def copy(self):
    return Algebraic_Expression(self)
  def const(self):
    """Returns the constant value in this expression."""
    return self.expr.const
  def unknown(self):
    """Returns the single unknown in this expression if it exists."""
    if len(self.expr.terms) == 1:
      return self.expr.terms[0].unknown
    else:
      raise Exception, "This expression does not have exactly 1 unknown!"
  def terms(self):
    """Returns a list of all the (coeficient, unknown) pairs for terms."""
    return [(term.coef, term.unknown) for term in self.expr.terms]
  def substitute(self, subs):
    new = Algebraic_Expression(0)
    for t in self.expr.terms:
      for unknown, value in subs:
        if isinstance(unknown, Algebraic_Expression):
          unknown = unknown.unknown()
        if unknown == t.unknown:
          new += (t.coef * value)
          break
      else:
        new.expr.append_terms([t])
    new += self.expr.const
    return new
  def __cmp__(self, other):
    """All unknowns assumbed to be >= 0"""
    # Inhereted concept of all numbers < strings
    if isinstance(other, str):
      return -1
    diff = self - other
    # 'c' will store the sign of the difference 'diff'.
    # All coeficients and the const must have the same sign or be zero.
    c = cmp(diff.const(), 0)
    terms = diff.terms()
    if not c:
      # If the const is 0 and there are no terms -> diff == 0 -> self == other
      if len(terms) == 0:
        return 0
      else:
        c = cmp(terms[0][0], 0)
    for coef, unknown in terms:
      # Coeficients cannot be 0, so they must have same sign.
      # If not, it will be imposible to know which is bigger without valuation.
      if cmp(coef, 0) != c:
        return NotImplemented
    return c
  def __eq__(self, other):
    if is_scalar(other):
      return self.expr.const == other and self.expr.terms == []
    else:
      return self.expr.const == other.expr.const and self.expr.terms == other.expr.terms
  # Addition magic methods:
  def __iadd__(self, other):
    if is_scalar(other):
      self.expr.const += other
    else:
      self.expr.iadd(other.expr)
    return self
  def __add__(self, other):
    new = self.copy()
    new += other
    return new
  def __radd__(self, other):
    return (self + other)
  # Multiplication magic methods:
  def __imul__(self, other):
    self.expr.imul(other)
    return self
  def __mul__(self, other):
    new = self.copy()
    new *= other
    return new
  def __rmul__(self, other):
    return (self * other)
  # Subtraction magic methods:
  def __neg__(self):
    return self * -1
  def __isub__(self, other):
    self += (-other)
    return self
  def __sub__(self, other):
    new = self.copy()
    new -= other
    return new
  def __rsub__(self, other):
    return -(self - other)
  # TODO: Divission magic methods:
  def __floordiv__(self, other):
    if other == 1:
      return self
    else:
      return NotImplemented
  def __itruediv__(self, other):
    self.expr.itruediv(other)
    return self
  def __truediv__(self, other):
    new = self.copy()
    new /= other
    return new
  def __div__(self, other):
    return self / other
  def __idiv__(self, other):
    self /= other
    return self

class Algebraic_Unknown(Algebraic_Expression):
  """Constructor for Algebraic_Expression type.  Creates a new unknown."""
  def __init__(self, unknown=None):
    if not unknown:
      unknown = Unknown()
    term = Term(1, unknown)
    self.expr = Expression(0, [term])
