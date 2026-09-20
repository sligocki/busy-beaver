# See @big_interval.md for mathematical background.

from __future__ import annotations

import math
import sys

sys.set_int_max_str_digits(0)


# Raised if you try to compare two BigIntervals which overlap
class NotComparable(Exception):
  pass


class Knuth10:
  BASE = 10
  # a0 in [C, 10^C)
  C = 1000
  MAX_A0 = BASE**C
  # ai in [0, C-2)
  MAX_A = C - 2

  def __init__(self, *args):
    self.args = list(args)
    while len(self.args) > 1 and self.args[-1] == 0:
      self.args.pop()
    self.args = tuple(self.args)

  @classmethod
  def lower_bound_from_int(cls, x: float) -> Knuth10:
    """Return tight lower bound for x in canonical Knuth10 notation.
    Ex: 10^1000 + 1 -> 10^1000
    """
    if x < cls.C:
      return cls(int(math.floor(x)))
    a1 = 0
    while x >= cls.MAX_A0:
      x = math.floor(math.log10(x))
      a1 += 1
    return cls(int(x), a1)

  @classmethod
  def upper_bound_from_int(cls, x: float) -> Knuth10:
    """Return tight upper bound for x in canonical Knuth10 notation.
    Ex: 10^1000 + 1 -> 10^1001
    """
    if x < cls.C:
      return cls(int(math.ceil(x)))
    a1 = 0
    while x >= cls.MAX_A0:
      x = math.ceil(math.log10(x))
      a1 += 1
    return cls(int(x), a1)

  def safe_upper_bound(self):
    a = list(self.args)
    a[0] += 1
    for i in range(len(a)):
      if i == 0:
        if a[0] >= 10**self.C:
          a[0] = self.C
          if len(a) == 1:
            a.append(0)
          a[1] += 1
      else:
        if a[i] > self.MAX_A:
          a[i] = 0
          if len(a) == i + 1:
            a.append(0)
          a[i + 1] += 1
          a[0] = self.C
    return Knuth10(*a)

  def div10(self):
    a = list(self.args)
    if len(a) == 1:
      return Knuth10.lower_bound_from_int(max(0, a[0] // 10))
    if a[0] > self.C:
      a[0] -= 1
      return Knuth10(*a)
    else:
      a[0] = 10 ** (self.C - 1)
      for i in range(1, len(a)):
        if a[i] > 0:
          a[i] -= 1
          return Knuth10(*a)
      return Knuth10(0)

  def apply_g1(self):
    a = list(self.args)
    if len(a) == 1:
      if a[0] < self.C:
        return Knuth10.lower_bound_from_int(10 ** a[0])
      a.append(1)
      return Knuth10(*a)
    a[1] += 1
    if a[1] > self.MAX_A:
      a[1] = 0
      if len(a) == 2:
        a.append(0)
      a[2] += 1
      a[0] = self.C
    return Knuth10(*a)

  def apply_g1_upper(self):
    a = list(self.args)
    if len(a) == 1:
      if a[0] < self.C:
        return Knuth10.upper_bound_from_int(10 ** a[0])
      a.append(1)
      return Knuth10(*a)
    a[1] += 1
    for i in range(1, len(a)):
      if a[i] > self.MAX_A:
        a[i] = 0
        if len(a) == i + 1:
          a.append(0)
        a[i + 1] += 1
        a[0] = self.C + 1
    return Knuth10(*a)

  def __lt__(self, other):
    if not isinstance(other, Knuth10):
      return NotImplemented
    A = list(self.args)
    B = list(other.args)
    while len(A) < len(B):
      A.append(0)
    while len(B) < len(A):
      B.append(0)
    return tuple(reversed(A)) < tuple(reversed(B))

  def __eq__(self, other):
    if not isinstance(other, Knuth10):
      return NotImplemented
    return self.args == other.args

  def __le__(self, other):
    return self < other or self == other

  def __gt__(self, other):
    return not (self <= other)

  def __ge__(self, other):
    return not (self < other)

  def __repr__(self):
    return f"Knuth10{self.args}"

  def __str__(self):
    s = str(self.args[0])
    for i in range(1, len(self.args)):
      ak = self.args[i]
      if ak == 0:
        continue
      arrows = "↑" * i
      if ak == 1:
        s = f"10{arrows} {s}"
      else:
        s = f"(10{arrows})^{ak} {s}"
    return s

  def approx_str(self, is_lower=True):
    s = ""
    for i in range(len(self.args) - 1, 0, -1):
      ak = self.args[i]
      if ak == 0:
        continue
      arrows = "↑" * i
      if i == 1:
        # H is the additional height needed to be added to a1 based on a0 (which we will ignore)
        a0 = self.args[0]
        if a0 < 10:
          H = 0
        elif a0 < 10**10:
          H = 1
        else:
          assert self.C < 10**10, self.C
          H = 2
        if not is_lower:
          # For upper bounds, we must go one step higher to ensure it is an upper-bound
          H += 1
        height = ak + H
        s += f"10↑↑{height}"
        break
      else:
        if ak == 1:
          s += f"10{arrows} "
        elif ak == 2:
          s += f"10{arrows} 10{arrows} "
        else:
          s += f"(10{arrows})^{ak} "

    if s == "":
      a0 = self.args[0]
      if a0 < 10**6:
        s = str(a0)
      else:
        s = f"10^{len(str(a0)) - 1 if is_lower else len(str(a0))}"
    elif s.endswith(" ") or s.endswith("↑"):
      a0 = self.args[0]
      if a0 < 10**6:
        s += str(a0)
      else:
        s += f"10^{len(str(a0)) - 1 if is_lower else len(str(a0))}"

    return s.strip()

  def try_eval(self, limit=10**1000):
    if len(self.args) == 1:
      return self.args[0]
    return None


class BigInterval:
  def __init__(self, lower, upper=None):
    if upper is None:
      upper = lower
    if isinstance(lower, int):
      lower = Knuth10.lower_bound_from_int(lower)
    if isinstance(upper, int):
      upper = Knuth10.upper_bound_from_int(upper)

    self.lower: Knuth10 = lower
    self.upper: Knuth10 = upper

  def __repr__(self):
    if self.lower == self.upper:
      return f"BigInterval({self.lower})"
    return f"BigInterval({self.lower}, {self.upper})"

  def __str__(self):
    if self.lower == self.upper:
      return f"[{self.lower}]"
    return f"[{self.lower}, {self.upper}]"

  def approx_str(self):
    return f"[{self.lower.approx_str(is_lower=True)}, {self.upper.approx_str(is_lower=False)}]"

  def __add__(self, other):
    if not isinstance(other, BigInterval):
      other = BigInterval(other)

    v_self_l = self.lower.try_eval()
    v_other_l = other.lower.try_eval()
    if v_self_l is not None and v_other_l is not None:
      new_lower = Knuth10.lower_bound_from_int(v_self_l + v_other_l)
    else:
      new_lower = max(self.lower, other.lower)

    v_self_u = self.upper.try_eval()
    v_other_u = other.upper.try_eval()
    if v_self_u is not None and v_other_u is not None:
      new_upper = Knuth10.upper_bound_from_int(v_self_u + v_other_u)
    else:
      new_upper = max(self.upper, other.upper).safe_upper_bound()

    return BigInterval(new_lower, new_upper)

  def __mul__(self, other):
    if not isinstance(other, BigInterval):
      other = BigInterval(other)

    # Lower bound
    v_self_l = self.lower.try_eval()
    v_other_l = other.lower.try_eval()
    if v_self_l is not None and v_other_l is not None:
      # If they are both small enough, just multiply directly
      new_lower = Knuth10.lower_bound_from_int(v_self_l * v_other_l)
    else:
      # If they are bigger, just default to A*B ≥ max(A, B)
      new_lower = max(self.lower, other.lower)

    # Upper bound
    A = self.upper
    B = other.upper
    v_self_u = A.try_eval()
    v_other_u = B.try_eval()

    if v_self_u is not None and v_other_u is not None:
      # Case 1: Small enough to compute exactly
      new_upper = Knuth10.upper_bound_from_int(v_self_u * v_other_u)
    else:
      # Check if both have height <= 1 (represented as either (a0,) or (a0, 1))
      def is_height_0_or_1(K):
        return len(K.args) == 1 or (len(K.args) == 2 and K.args[1] == 1)

      if is_height_0_or_1(A) and is_height_0_or_1(B):
        # Case 2: AB <= 10^{exp_A + exp_B}
        def get_exp(K):
          if len(K.args) == 1:
            return len(str(K.args[0]))
          return K.args[0]

        power = get_exp(A) + get_exp(B)
        if power < 10**Knuth10.C:
          new_upper = Knuth10(power, 1)
        else:
          new_upper = Knuth10.lower_bound_from_int(power).safe_upper_bound()
      else:
        # Case 3: At least one has height >= 2
        # max(A, B)^2 is safely bounded by max(A, B).safe_upper_bound()
        U_max = max(A, B)
        new_upper = U_max.safe_upper_bound()

    return BigInterval(new_lower, new_upper)

  def __pow__(self, other):
    if not isinstance(other, BigInterval):
      other = BigInterval(other)

    def get_lower_power(b, n):
      try:
        log_b = math.nextafter(math.log10(b), -math.inf)
        return int(math.nextafter(n * log_b, -math.inf))
      except OverflowError:
        return (n * (b.bit_length() - 1) * 301029) // 1000000

    def get_upper_power(b, n):
      try:
        log_b = math.nextafter(math.log10(b), math.inf)
        return int(math.nextafter(n * log_b, math.inf)) + 1
      except OverflowError:
        return (n * b.bit_length() * 301030) // 1000000 + 1

    v_self_l = self.lower.try_eval()
    v_other_l = other.lower.try_eval()
    if v_self_l is not None and v_other_l is not None:
      power = get_lower_power(v_self_l, v_other_l)
      if power < Knuth10.C:
        new_lower = Knuth10.lower_bound_from_int(v_self_l**v_other_l)
      else:
        new_lower = Knuth10.lower_bound_from_int(power).apply_g1()
    else:
      if self.lower == Knuth10(1) or self.lower == Knuth10(0):
        new_lower = self.lower
      elif self.lower >= Knuth10(10):
        new_lower = other.lower.apply_g1()
      else:
        if len(other.lower.args) == 1 and len(self.lower.args) == 1:
          l_b = self.lower.args[0]
          l_n = other.lower.args[0]
          power = get_lower_power(l_b, l_n)
          new_lower = Knuth10.lower_bound_from_int(power).apply_g1()
        else:
          new_lower = other.lower.div10().apply_g1()

    v_self_u = self.upper.try_eval()
    v_other_u = other.upper.try_eval()
    if v_self_u is not None and v_other_u is not None:
      power = get_upper_power(v_self_u, v_other_u)
      if power < Knuth10.C:
        new_upper = Knuth10.upper_bound_from_int(v_self_u**v_other_u)
      else:
        new_upper = Knuth10.lower_bound_from_int(power).apply_g1_upper()
    else:
      if self.upper == Knuth10(1) or self.upper == Knuth10(0):
        new_upper = self.upper
      elif self.upper <= Knuth10(10):
        new_upper = other.upper.apply_g1_upper()
      else:
        if len(other.upper.args) == 1 and len(self.upper.args) == 1:
          u_b = self.upper.args[0]
          u_n = other.upper.args[0]
          power = get_upper_power(u_b, u_n)
          if power < Knuth10.C:
            new_upper = Knuth10.upper_bound_from_int(u_b**u_n)
          else:
            new_upper = Knuth10.lower_bound_from_int(power).apply_g1_upper()
        else:
          if len(self.upper.args) == 1 and self.upper.args[0] <= 10:
            new_upper = other.upper.apply_g1_upper()
          else:
            mul_upper = (BigInterval(self.upper) * BigInterval(other.upper)).upper
            new_upper = mul_upper.apply_g1_upper()

    return BigInterval(new_lower, new_upper)

  def __truediv__(self, other):
    if other == 0:
      raise ZeroDivisionError
    if not isinstance(other, BigInterval):
      other = BigInterval(other)

    v_self_l = self.lower.try_eval()
    v_other_u = other.upper.try_eval()
    if v_self_l is not None and v_other_u is not None:
      new_lower = Knuth10.lower_bound_from_int(v_self_l / v_other_u)
    else:
      if v_other_u is not None and v_other_u <= 10:
        new_lower = self.lower.div10()
      else:
        return NotImplemented

    v_self_u = self.upper.try_eval()
    v_other_l = other.lower.try_eval()
    if v_self_u is not None and v_other_l is not None:
      new_upper = Knuth10.upper_bound_from_int(v_self_u / v_other_l)
    else:
      new_upper = self.upper.safe_upper_bound()

    return BigInterval(new_lower, new_upper)

  def cmp(self, other):
    # Returns -1 if self < other, 1 if self > other, 0 if self = other (impossible for intervals).
    # Raises NotComparable if self and other are incomparable.
    if not isinstance(other, BigInterval):
      other = BigInterval(other)
    if self.upper < other.lower:
      # self < other
      return -1
    elif other.upper < self.lower:
      # other < self
      return 1
    else:
      raise NotComparable

  def __lt__(self, other):
    return self.cmp(other) < 0

  def __gt__(self, other):
    return self.cmp(other) > 0

  def __le__(self, other):
    return self.cmp(other) <= 0

  def __ge__(self, other):
    return self.cmp(other) >= 0
