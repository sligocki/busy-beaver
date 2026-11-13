from __future__ import annotations

import abc
import fractions
import math

from Big_Interval import BigInterval


def is_scalar(value) -> bool:
  return isinstance(value, (int, float, fractions.Fraction))


def is_const(value) -> bool:
  if is_scalar(value):
    return True
  return value.is_const


def to_BigInterval(value, env=None):
  """Convert a BigInterval, NatExpr, Variable, or int into a BigInterval iteratively."""

  def resolve_leaf(v):
    if isinstance(v, BigInterval):
      return v
    if isinstance(v, ConstInt):
      return BigInterval(v.val)
    if is_scalar(v):
      return BigInterval(v)
    return None

  def unwrap_var(v):
    while type(v).__name__ == "Variable":
      assert env is not None and v in env, f"Unbound variable {v}"
      v = env[v]
    return v

  def get_cached(v):
    if getattr(v, "is_const", False):
      return getattr(v, "__dict__", {}).get("_cached_big_interval")
    return None

  root = unwrap_var(value)
  leaf = resolve_leaf(root)
  if leaf is not None:
    return leaf
  cached = get_cached(root)
  if cached is not None:
    return cached

  memo: dict[int, BigInterval] = {}
  stack: list[tuple[object, bool]] = [(root, False)]

  def resolve(x):
    x = unwrap_var(x)
    res = resolve_leaf(x)
    if res is not None:
      return res
    return memo[id(x)]

  while stack:
    node, visited = stack.pop()
    nid = id(node)
    if nid in memo:
      continue
    cached = get_cached(node)
    if cached is not None:
      memo[nid] = cached
      continue
    if visited:
      res = node._bi_combine(resolve, env)
      memo[nid] = res
      if getattr(node, "is_const", False) and hasattr(node, "__dict__"):
        node._cached_big_interval = res
    else:
      if not hasattr(node, "_bi_children"):
        if isinstance(node, NatExpr):
          raise NotImplementedError(f"to_BigInterval not implemented for {type(node)}")
        memo[nid] = BigInterval(node)
        continue
      stack.append((node, True))
      for child in node._bi_children(env):
        c = unwrap_var(child)
        if resolve_leaf(c) is not None:
          continue
        cid = id(c)
        if cid in memo:
          continue
        cached = get_cached(c)
        if cached is not None:
          memo[cid] = cached
          continue
        stack.append((c, False))

  return memo[id(root)]


def _str_or_len(value, compute_len: bool):
  """Iteratively compute str(value) or len(str(value)) over expression DAGs."""

  def cached_or_leaf(v):
    d = getattr(v, "__dict__", None)
    if d is not None and "formula_str" in d:
      s = d["formula_str"]
      return len(s) if compute_len else s
    if not hasattr(v, "_str_tokens"):
      s = str(v)
      return len(s) if compute_len else s
    return None

  leaf = cached_or_leaf(value)
  if leaf is not None:
    return leaf

  memo = {}
  stack = [(value, False, None)]
  while stack:
    node, visited, tokens = stack.pop()
    nid = id(node)
    if nid in memo:
      continue
    leaf = cached_or_leaf(node)
    if leaf is not None:
      memo[nid] = leaf
      continue
    if visited:
      if compute_len:
        memo[nid] = sum(len(part) if isinstance(part, str) else memo[id(part)] for part in tokens)
      else:
        memo[nid] = "".join(part if isinstance(part, str) else memo[id(part)] for part in tokens)
    else:
      tokens = node._str_tokens()
      stack.append((node, True, tokens))
      for part in tokens:
        if isinstance(part, str):
          continue
        pid = id(part)
        if pid in memo:
          continue
        p_leaf = cached_or_leaf(part)
        if p_leaf is not None:
          memo[pid] = p_leaf
        else:
          stack.append((part, False, None))

  return memo[id(value)]


def expr_str(value) -> str:
  return _str_or_len(value, compute_len=False)


def expr_str_len(value) -> int:
  return _str_or_len(value, compute_len=True)


def big_interval_str(value) -> str:
  if value is None:
    return "N/A"
  if type(value).__name__ == "Variable":
    return str(value)
  expr = NatExpr.wrap(value)
  if expr.is_inf or not expr.is_const:
    return expr.approx_str()
  val_int = expr.try_eval()
  if val_int is not None and abs(val_int) < 10**10:
    return f"{val_int:_}"
  try:
    bi = expr.to_BigInterval()
  except (NotImplementedError, AssertionError, ValueError):
    return expr.approx_str()
  s = str(bi)
  if len(s) <= 80:
    return s
  return bi.approx_str()


def approx_str(value) -> str:
  if value is None:
    return "N/A"
  if type(value).__name__ == "Variable":
    return str(value)
  return NatExpr.wrap(value).approx_str()


def approx_and_full_str(value, max_chars: int = 100, use_big_interval: bool = True) -> str:
  if value is None:
    return "N/A"
  if type(value).__name__ == "Variable":
    return str(value)
  approx = big_interval_str(value) if use_big_interval else approx_str(value)
  full_len = expr_str_len(value)
  if max_chars and full_len > max_chars:
    return f"{approx} (_{full_len} chars_)"
  full = expr_str(value)
  if approx == full:
    return approx
  return f"{approx} ({full})"


def approx_or_full_str(value, max_chars: int = 100, use_big_interval: bool = True) -> str:
  if value is None:
    return "N/A"
  if type(value).__name__ == "Variable":
    return str(value)
  if max_chars and expr_str_len(value) > max_chars:
    return big_interval_str(value) if use_big_interval else approx_str(value)
  return expr_str(value)


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

  @property
  def is_inf(self) -> bool:
    return False

  is_const: bool = False

  @property
  @abc.abstractmethod
  def uparrow_size_approx(self) -> tuple:
    pass

  @abc.abstractmethod
  def try_eval(self) -> int | None:
    pass

  def try_simplify(self) -> NatExpr:
    val = self.try_eval()
    if val is not None:
      return ConstInt(val)
    return self

  def approx_str(self) -> str:
    if not self.is_const:
      return str(self)

    val = self.uparrow_size_approx
    if val[0] >= 4:
      return f"~ 10 ↑^{val[0]} {approx_str(val[1])}"
    elif val[0] > 2:
      arrows = "↑" * val[0]
      return f"~ 10 {arrows} {approx_str(val[1])}"

    assert val[0] == 2, val
    height, top = val[1], val[2]

    if not isinstance(height, (int, float)):
      if height == 0:
        return f"{top}"
      elif height == 1:
        return f"~ 10^{top}"
      else:
        height = approx_str(height)
        return f"~ 10^^{height}"

    # Compute "fractional heights"
    assert top > 0, val
    if height == 0 and top < 10**10:
      val_int = self.try_eval()
      return f"{val_int:_}" if val_int is not None else str(self)
    while top >= 10**10:
      top = math.log10(top)
      height += 1
    if height <= 1:
      exp = math.log10(top) if height == 0 else top
      return f"~ 10^{exp:_.1f}"

    while top >= 1:
      top = math.log10(top)
      height += 1
    height = height - 1 + top
    return f"~ 10^^{height:_.1f}"

  def to_BigInterval(self, env=None):
    raise NotImplementedError(f"to_BigInterval not implemented for {type(self)}")


class ConstInt(NatExpr):
  """Wraps a standard Python integer."""

  __slots__ = ["val"]

  def __init__(self, val: int):
    self.val = val

  def try_eval(self) -> int:
    return self.val

  is_const: bool = True

  @property
  def uparrow_size_approx(self) -> tuple:
    return (2, 0, abs(self.val))

  def min_val(self):
    return self

  def variables(self) -> set:
    return set()

  def substitute(self, assignment: dict):
    return self

  def approx_str(self) -> str:
    if self.val < 10**10:
      return f"{self.val:_}"
    return super().approx_str()

  def to_BigInterval(self, env=None):
    return BigInterval(self.val)

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

  is_const: bool = True

  def min_val(self):
    return self

  def variables(self):
    return set()

  def substitute(self, assignment: dict):
    return self

  @property
  def uparrow_size_approx(self) -> tuple:
    return (math.inf, math.inf, math.inf)

  def approx_str(self) -> str:
    return "inf"

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
