"""
Classes to do various algebraic operations on different abstract expression
which contain number and variables.
"""

from fractions import Fraction
from functools import reduce
import operator
import string


class BadOperation(Exception):
  """This operation cannot be performed on this Expression."""

def is_scalar(value):
  return isinstance(value, (int, Fraction))

class Variable:
  """A distinct variable in an algebraic expression"""
  num_vars = 0

  def __init__(self, id = None):
    if id == None:
      self.id = Variable.num_vars
      Variable.num_vars += 1
    else:
      self.id = id

  def __repr__(self):
    # Variables are initially printed as letters and thereafter as <x#>
    if self.id <= 25:
      return "%c" % (self.id + ord('a'))
    else:
      return "<x%d>" % self.id

  def __eq__(self, other):
    return self.id == other.id

  def __hash__(self):
    return hash(self.id)

def Variable_from_string(input):
  if input[0] == '<' and input[1] == 'x':
    return Variable(int(input[2:-1]))
  elif len(input) == 1 and input[0] in string.ascii_lowercase:
    return Variable(ord(input[0]) - ord('a'))
  else:
    raise ValueError("Unable to interpret '%s' as a Term" % (input,))

class Var_Power:
  """A variable raised to some power (eg: a^3)"""
  def __init__(self, variable, power):
    self.var = variable
    self.pow = power

  def __repr__(self):
    if self.pow == 1:
      return repr(self.var)
    else:
      return "%s^%s" % (repr(self.var), repr(self.pow))

  def substitute(self, subs):
    """Substitute values from dict 'subs' to get an int."""
    if self.var in subs:
      return subs[self.var]**self.pow
    else:
      return VariableToExpression(self.var)**self.pow

def Var_Power_from_string(input):
  input = input.split('^')

  vari = Variable_from_string(input[0])

  if len(input) == 2:
    power = int(input[1])
  else:
    power = 1

  return Var_Power(vari,power)

class Term:
  """A term in a (multi-variable) polynomial (eg: 4 x^3 y^2)"""
  def __init__(self, var_powers, coefficient):
    self.vars = var_powers # Always assumed to be a non-empty tuple
    self.coef = coefficient

  def __repr__(self):
    r = " ".join([repr(v) for v in self.vars])
    if self.coef == 1:
      return r
    elif self.coef == -1:
      return "-"+r
    else:
      return repr(self.coef)+" "+r

  def substitute(self, subs):
    """Substitute values from dict 'subs' to get an int."""
    return reduce(operator.mul, [vp.substitute(subs) for vp in self.vars]) * self.coef

def Term_from_string(input):
  input_split = input.split()

  try:
    coef = int(input_split[0])
    var_powers = input_split[1:]
  except ValueError:
    if input_split[0][0] == "-":
      coef = -1
      input_split[0] = input_split[0][1:]
    else:
      coef = 1
    var_powers = input_split

  var_powers = tuple([Var_Power_from_string(var_power) for var_power in var_powers])

  return Term(var_powers,coef)

class Expression:
  """An algebraic expression, i.e. a multi-variable polynomial."""
  def __init__(self, terms, constant):
    self.terms = terms
    self.const = constant

  def __repr__(self):
    if len(self.terms) == 0:
      return repr(self.const)
    r = " + ".join([repr(t) for t in self.terms])
    if self.const == 0:
      return "("+r+")"
    elif self.const < 0:
      return "("+r+" - "+repr(-self.const)+")"
    else:
      return "("+r+" + "+repr(self.const)+")"

  def __add__(self, other):
    if is_scalar(other):
      return Expression(self.terms, self.const + other)
    else:
      assert isinstance(other, Expression), other
      return Expression(term_sum(self.terms, other.terms), self.const + other.const)


  def __mul__(self, other):
    if is_scalar(other):
      if other == 0:
        return Expression([], 0)
      else:
        new_terms = tuple([Term(t.vars, t.coef*other) for t in self.terms])
        return Expression(new_terms, self.const*other)
    else:
      assert isinstance(other, Expression), other
      return expr_prod(self, other)

  def __pow__(self, power):
    """x^n == x * x^(n-1)"""
    assert isinstance(power, int), (self, power)
    prod = 1
    for _ in range(power):
      prod *= self
    return prod

  def __neg__(self):
    """-x == -1*x"""
    return self.__mul__(-1)
  def __sub__(self, other):
    """x - y == x + -y"""
    return self.__add__(other.__neg__())
  def __radd__(self, other):
    """x+y == y+x"""
    return self.__add__(other)
  def __rmul__(self, other):
    """x*y == y*x"""
    return self.__mul__(other)
  def __rsub__(self, other):
    """x - y == -y + x"""
    return (self.__neg__()).__add__(other)

  def __truediv__(self, other):
    """Divide the expression by a scalar."""
    assert isinstance(other, int), (self, other)
    # We just force consts and coefs to be Fractions for simplicity.
    return Expression(
      terms = tuple(Term(var_powers = term.vars,
                         coefficient = Fraction(term.coef, other))
                    for term in self.terms),
      constant = Fraction(self.const, other))
  __floordiv__ = __truediv__

  def substitute(self, subs):
    """Substitute values from dict 'subs' to get an int."""
    val = sum([t.substitute(subs) for t in self.terms]) + self.const
    if isinstance(val, Fraction) and val.denominator == 1:
      return int(val)
    else:
      return val


  def always_greater_than(self, other):
    """True if self > other for any non-negative variable assignment."""
    diff = self - other
    if not diff.const > 0:
      return False
    for term in diff.terms:
      if not term.coef >= 0:
        return False
    return True

  def __eq__(self, other):
    if isinstance(other, Expression):
      # Is this a hack?
      return repr(self) == repr(other)
    else:
      return len(self.terms) == 0 and self.const == other

  def __ne__(self, other):
    return not self == other

  def __lt__(self, other):
    return self.__cmp__(other) < 0

  def __gt__(self, other):
    return self.__cmp__(other) > 0

  def __cmp__(self, other):
    # See if we are guaranteed (for all var values > 0) how self compares to other.
    # Ex:  x + 10 == x + 10
    #      x + 10 < 2x + 10
    #      x + 10 > 10
    #      x + 10 ? 2x + 9  (These are incomparable)
    diff = self - other
    has_pos = has_neg = False
    for term in diff.terms:
      if term.coef > 0:
        has_pos = True
      elif term.coef < 0:
        has_neg = True
    if diff.const > 0:
      has_pos = True
    elif diff.const < 0:
      has_neg = True

    if has_pos:
      if has_neg:
        # The two expressions are not comparable.
        raise BadOperation
      else:
        # There are some positive coefs and no negative ones -> self > other.
        return +1
    else:  # has_pos == False
      if has_neg:
        # There are some negative coefs and no positive ones -> self < other.
        return -1
      else:
        # There are no positive nor negative components -> self = other.
        return 0

  def is_const(self):
    """Returns true if this expression has not variables."""
    return (len(self.terms) == 0)

  def is_var_plus_const(self):
    """Is this expression of the form x + 5 (var + const)."""
    return (len(self.terms) == 1 and self.terms[0].coef == 1 and
            len(self.terms[0].vars) == 1 and self.terms[0].vars[0].pow == 1)

  def is_linear(self):
    """Is this expression linear, say 3x + 5 (coef * variable + const)."""
    return (len(self.terms) == 1 and len(self.terms[0].vars) == 1 and
            self.terms[0].vars[0].pow == 1)

  def variable_restricted(self):
    """Returns the single variable in this expression of form x + 12."""
    if self.is_var_plus_const():
      return self.terms[0].vars[0].var
    else:
      raise BadOperation("Expression %s is not of correct form" % self)

  def variable(self):
    """Returns the single variable in this expression if it exists."""
    if len(self.terms) == 1 and len(self.terms[0].vars) == 1:
      return self.terms[0].vars[0].var
    else:
      raise BadOperation("Expression %s is not of correct form" % self)

  def get_coef(self):
    """If expression is linear, say m*x + k, returns coefficient m.
    Otherwise returns None."""
    if self.is_linear():
      return self.terms[0].coef
    else:
      return None

Algebraic_Expression = Expression

def Expression_from_string(input):
  if input[0] == '(':
    input = input[1:-1]

  terms = input.split('+')
  terms = [term.strip() for term in terms]

  last_terms = terms[-1].split('-')
  last_terms = [last_term.strip() for last_term in last_terms]

  if len(last_terms) == 2:
    last_terms[1] = '-'+last_terms[1]

  if last_terms[0] == '':
    last_terms = last_terms[1:]

  terms[-1:] = last_terms

  try:
    coef = int(terms[-1])
    terms = terms[:-1]
  except ValueError:
    coef = 0

  terms = tuple([Term_from_string(term) for term in terms])

  return Expression(terms,coef)

def term_sum(terms1, terms2):
  """Add 2 lists of terms"""
  new_terms = []
  i = j = 0
  while i < len(terms1) and j < len(terms2):
    t1, t2 = terms1[i], terms2[j]
    c = compare_terms(t1, t2)
    if c == 0:  # if t1 == t2
      if t1.coef + t2.coef != 0:
        new_terms.append(Term(t1.vars, t1.coef + t2.coef))
      i += 1
      j += 1
    elif c < 0: # if t1 < t2
      new_terms.append(t1)
      i += 1
    else:       # if t1 > t2
      new_terms.append(t2)
      j += 1
  # Append the rest of the terms in the only remaining list
  new_terms.extend(terms1[i:])
  new_terms.extend(terms2[j:])
  return new_terms

def compare_terms(t1, t2):
  """Compare 2 Terms in an arbitrary, but consistent manner."""
  vars1 = t1.vars
  vars2 = t2.vars

  # Shorter terms preceed longer terms
  if len(vars1) < len(vars2):
    return -1
  elif len(vars1) > len(vars2):
    return +1

  # Same length
  for vp1, vp2 in zip(vars1, vars2):
    # Older variables preceed younger variables
    if vp1.var.id < vp2.var.id:
      return -1
    elif vp1.var.id > vp2.var.id:
      return +1

    # Variables to smaller exponents preceed those with larger exponents
    if vp1.pow < vp2.pow:
      return -1
    elif vp1.pow > vp2.pow:
      return +1

  # Otherwise the two terms are completely identical
  return 0

def expr_prod(e1 : Expression, e2 : Expression) -> Expression:
  assert isinstance(e1, Expression), e1
  assert isinstance(e2, Expression), e2
  new_expr = Expression([], 0)
  for t1 in e1.terms:
    for t2 in e2.terms:
      new_term = Term(vars_prod(t1.vars, t2.vars), t1.coef*t2.coef)
      new_expr += Expression([new_term], 0)
    new_expr += Expression([t1], 0)*e2.const
  new_expr += (e2*e1.const)
  return new_expr

def vars_prod(vars1, vars2):
  new_vars = []
  i = j = 0
  while i < len(vars1) and j < len(vars2):
    vp1, vp2 = vars1[i], vars2[j]
    if vp1.var.id < vp2.var.id:
      new_vars.append(vp1)
      i += 1
    elif vp1.var.id > vp2.var.id:
      new_vars.append(vp2)
      j += 1
    else:  # vp1.var.id == vp2.var.id
      new_vars.append(Var_Power(vp1.var, vp1.pow + vp2.pow))
      i += 1
      j += 1
  new_vars.extend(vars1[i:])
  new_vars.extend(vars2[j:])
  return new_vars

def NewVariableExpression():
  """Produce an expression containing only a new variable."""
  return VariableToExpression(Variable())

def VariableToExpression(var):
  """Produce Algebraic Expression from a lone variable."""
  vp = Var_Power(var, 1)
  term = Term([vp], 1)
  expr = Expression([term], 0)
  return expr

def ConstantToExpression(const):
  """Produce an Algebraic Expression from a lone constant."""
  return Expression([], const)