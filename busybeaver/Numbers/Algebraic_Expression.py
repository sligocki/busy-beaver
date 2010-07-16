import string, operator
from Number import Number, Rational

def is_scalar(value):
  return isinstance(value, (int, long, Rational))

class Variable(object):
  """A distinct variable in an algebraic expression"""
  num_vars = 0
  def __init__(self):
    self.id = Variable.num_vars
    Variable.num_vars += 1
  def __repr__(self):
    # Variables are initially printed as letters and thereafter as <x#>
    if self.id <= 25:
      return "%c" % (self.id + 97)
    else:
      return "<x%d>" % self.id
  def __eq__(self, other):
    return self.id == other.id
  def __hash__(self):
    return hash(self.id)

class Var_Power(object):
  """A variable raised to some power (eg: a^3)"""
  def __init__(self, variable, power):
    self.var = variable
    self.pow = power
  def __repr__(self):
    if self.pow == 1:
      return repr(self.var)
    else:
      return "(%s^%s)" % (repr(self.var), repr(self.pow))
  def substitute(self, subs):
    """Substitute values from dict 'subs' to get an int."""
    # TODO: What should we do if it's not in dict?
    return subs[self.var]**self.pow

class Term(object):
  """A term in a (multi-variable) polynomial (eg: 4 x^3 * y^2)"""
  def __init__(self, var_powers, coeficient):
    self.vars = var_powers # Always assumed to be a non-empty tuple
    self.coef = coeficient
  def __repr__(self):
    r = string.join([repr(v) for v in self.vars], "")
    if self.coef == 1:
      return r
    elif self.coef == -1:
      return "-"+r
    else:
      return repr(self.coef)+r
  def substitute(self, subs):
    """Substitute values from dict 'subs' to get an int."""
    return reduce(operator.mul, [vp.substitute(subs) for vp in self.vars]) * self.coef

class Expression(Number):
  """An algebraic expression, i.e. a multi-variable polynomial."""
  def __init__(self, terms, constant):
    self.terms = terms
    self.const = constant
  def __repr__(self):
    if len(self.terms) == 0:
      return repr(self.const)
    r = string.join([repr(t) for t in self.terms], " + ")
    if self.const == 0:
      return "("+r+")"
    else:
      return "("+r+" + "+repr(self.const)+")"
  def __add__(self, other):
    if is_scalar(other):
      return Expression(self.terms, self.const + other)
    else:
      return Expression(term_sum(self.terms, other.terms), self.const + other.const)
  def __mul__(self, other):
    if is_scalar(other):
      if other == 0:
        return Expression([], 0)
      else:
        new_terms = tuple([Term(t.vars, t.coef*other) for t in self.terms])
        return Expression(new_terms, self.const*other)
    else:
      return expr_prod(self, other)
  def __div__(self, other):
    """Divide the expression by a scalar.
    
    If the scalar does not perfectly divide all the coeficients and constant,
    we return NotImplemented
    """
    # TODO: Implement some way of dealing with situations like (d + d^2) / 2
    if other == 1:
      return self
    elif is_scalar(other):
      new_const = self.const.__div__(other)
      if new_const * other != self.const:
        return NotImplemented
      new_terms = []
      for old_term in self.terms:
        new_coef = old_term.coef.__div__(other)
        if new_coef * other != old_term.coef:
          return NotImplemented
        new_terms.append(Term(old_term.vars, new_coef))
      return Expression(tuple(new_terms), new_const)
    else:
      ### TODO: We could (actually) devide, say (8x+8) / (x+1) = 8 !
      return NotImplemented
  def __truediv__(self, other):
    if other == 1:
      return self
    if is_scalar(other):
      new_terms = tuple([Term(t.vars, t.coef.__truediv__(other)) for t in self.terms])
      return Expression(new_terms, self.const.__truediv__(other))
    else:
      ### TODO: We could (actually) devide, say (8x+8) / (x+1) = 8 !
      return NotImplemented
  def __floordiv__(self, other):
    if other == 1:
      return self
    else:
      ### TODO: We could (actually) devide, say (8x+8) // 8 = (x+1) !
      return NotImplemented
  
  def substitute(self, subs):
    """Substitute values from dict 'subs' to get an int."""
    return sum([t.substitute(subs) for t in self.terms]) + self.const
  
  def always_greater_than(self, other):
    """True if self > other for any non-negative variable assignment."""
    diff = self - other
    if not diff.const > 0:
      return False
    for term in diff.terms:
      if not term.coef >= 0:
        return False
    return True
  
  # Temporary methods
  def __eq__(self, other):
    if is_scalar(other):
      return (len(self.terms) == 0 and self.const == other)
    else:
      return NotImplemented
  def __cmp__(self, other):
    return cmp(self.const, other)
  def unknown(self):
    """Returns the single variable in this expression if it exists."""
    if len(self.terms) == 1 and len(self.terms[0].vars) == 1:
      return self.terms[0].vars[0].var
    else:
      raise Exception, "This expression does not have exactly 1 variable!"

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
  c = cmp(len(vars1), len(vars2))
  if c != 0:
    return c
  for vp1, vp2 in zip(vars1, vars2):
    # Older variables preceed younger variables
    c = cmp(vp1.var.id, vp2.var.id)
    if c != 0:
      return c
    # Variables to smaller exponents preceed those with larger exponents
    c = cmp(vp1.pow, vp2.pow)
    if c != 0:
      return c
  # Otherwise the two terms are completely identical
  return 0

def expr_prod(e1, e2):
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
    c = cmp(vp1.var.id, vp2.var.id)
    if c == 0:
      new_vars.append(Var_Power(vp1.var, vp1.pow + vp2.pow))
      i += 1
      j += 1
    elif c < 0:
      new_vars.append(vp1)
      i += 1
    else:
      new_vars.append(vp2)
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

Algebraic_Expression = Expression
