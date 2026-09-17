from __future__ import annotations

import abc
import fractions
import math


def is_scalar(value) -> bool:
  return isinstance(value, (int, float, fractions.Fraction))


def is_const(value) -> bool:
  if is_scalar(value):
    return True
  return value.is_const


class NatExpr(abc.ABC):
  """Abstract base class for all symbolic counts and expressions."""

  @classmethod
  def wrap(cls, val):
    if isinstance(val, NatExpr):
      return val
    if isinstance(val, int):
      return ConstInt(val)
    if math.isinf(val):
      return InfNat()
    raise TypeError(f"Cannot wrap {type(val)} as NatExpr")

  @abc.abstractmethod
  def try_eval(self) -> int | None:
    pass

  def try_simplify(self) -> NatExpr:
    val = self.try_eval()
    if val is not None:
      return ConstInt(val)
    return self

  @property
  def is_inf(self) -> bool:
    return False


class ConstInt(NatExpr):
  """Wraps a standard Python integer."""

  __slots__ = ["val"]

  def __init__(self, val: int):
    self.val = val

  def try_eval(self) -> int:
    return self.val

  @property
  def is_const(self) -> bool:
    return True

  def min_val(self):
    return self

  def variables(self) -> set:
    return set()

  def substitute(self, assignment: dict):
    return self

  @property
  def uparrow_size_approx(self) -> tuple:
    return (2, 0, abs(self.val))

  # Standard Magic Methods
  def __add__(self, other):
    if type(other) is ConstInt:
      return ConstInt(self.val + other.val)
    if type(other) is int:
      return ConstInt(self.val + other)
    # Note: NatExpr subtypes handle reverse ops
    return NotImplemented

  def __radd__(self, other):
    if type(other) is int:
      return ConstInt(other + self.val)
    return NotImplemented

  def __sub__(self, other):
    if type(other) is ConstInt:
      return ConstInt(self.val - other.val)
    if type(other) is int:
      return ConstInt(self.val - other)
    return NotImplemented

  def __rsub__(self, other):
    if type(other) is int:
      return ConstInt(other - self.val)
    return NotImplemented

  def __mul__(self, other):
    if type(other) is ConstInt:
      return ConstInt(self.val * other.val)
    if type(other) is int:
      return ConstInt(self.val * other)
    return NotImplemented

  def __rmul__(self, other):
    if type(other) is int:
      return ConstInt(other * self.val)
    return NotImplemented

  def __floordiv__(self, other):
    if type(other) is ConstInt:
      return ConstInt(self.val // other.val)
    if type(other) is int:
      return ConstInt(self.val // other)
    return NotImplemented

  def __mod__(self, other):
    if type(other) is ConstInt:
      return ConstInt(self.val % other.val)
    if type(other) is int:
      return ConstInt(self.val % other)
    return NotImplemented

  def __eq__(self, other):
    if type(other) is ConstInt:
      return self.val == other.val
    if type(other) in (int, float):
      return self.val == other
    return NotImplemented

  def __lt__(self, other):
    if type(other) is ConstInt:
      return self.val < other.val
    if type(other) is int:
      return self.val < other
    return NotImplemented

  def __le__(self, other):
    if type(other) is ConstInt:
      return self.val <= other.val
    if type(other) is int:
      return self.val <= other
    return NotImplemented

  def __gt__(self, other):
    if type(other) is ConstInt:
      return self.val > other.val
    if type(other) is int:
      return self.val > other
    return NotImplemented

  def __ge__(self, other):
    if type(other) is ConstInt:
      return self.val >= other.val
    if type(other) is int:
      return self.val >= other
    return NotImplemented

  def __hash__(self):
    return hash(self.val)

  def __int__(self):
    return self.val

  def __index__(self):
    return self.val

  def __abs__(self):
    return ConstInt(abs(self.val))

  def __neg__(self):
    return ConstInt(-self.val)

  def __divmod__(self, other):
    if type(other) is ConstInt:
      d, m = divmod(self.val, other.val)
      return ConstInt(d), ConstInt(m)
    if type(other) is int:
      d, m = divmod(self.val, other)
      return ConstInt(d), ConstInt(m)
    return NotImplemented

  def __rdivmod__(self, other):
    if type(other) is int:
      d, m = divmod(other, self.val)
      return ConstInt(d), ConstInt(m)
    return NotImplemented

  def __truediv__(self, other):
    if type(other) is ConstInt:
      return self.val / other.val
    if type(other) is int:
      return self.val / other
    return NotImplemented

  def __pow__(self, other):
    if type(other) is ConstInt:
      return ConstInt(self.val**other.val)
    if type(other) is int:
      return ConstInt(self.val**other)
    return NotImplemented

  def __rtruediv__(self, other):
    if type(other) is int:
      return other / self.val
    return NotImplemented

  def __repr__(self):
    return repr(self.val)

  def __str__(self):
    return str(self.val)

  def __bool__(self):
    return bool(self.val)


class InfNat(NatExpr):
  """Represents positive infinity."""

  __slots__ = []

  def try_eval(self):
    return None

  @property
  def is_inf(self) -> bool:
    return True

  @property
  def is_const(self) -> bool:
    return True

  def min_val(self):
    return self

  def variables(self):
    return set()

  def substitute(self, assignment: dict):
    return self

  @property
  def uparrow_size_approx(self) -> tuple:
    return (math.inf, math.inf, math.inf)

  def _is_valid_type(self, other):
    return isinstance(other, (NatExpr, int))

  def __add__(self, other: NatExpr):
    if not self._is_valid_type(other):
      return NotImplemented
    return self

  def __radd__(self, other: NatExpr):
    return self.__add__(other)

  def __sub__(self, other: NatExpr):
    if not self._is_valid_type(other):
      return NotImplemented
    if isinstance(other, InfNat):
      raise ValueError("inf - inf is undefined")
    return self

  def __eq__(self, other):
    if isinstance(other, InfNat):
      return True
    return False

  def __lt__(self, other):
    return False

  def __le__(self, other):
    return self.__eq__(other)

  def __gt__(self, other):
    return not self.__le__(other)

  def __ge__(self, other):
    return True

  def __hash__(self):
    return hash(math.inf)

  def __repr__(self):
    return "inf"

  def __str__(self):
    return "inf"
