# See @big_interval.md for mathematical background.

import sys

sys.set_int_max_str_digits(0)


class Knuth10:
  C = 1000
  MAX_A = C - 2

  def __init__(self, *args):
    self.args = list(args)
    while len(self.args) > 1 and self.args[-1] == 0:
      self.args.pop()
    self.args = tuple(self.args)

  @classmethod
  def lower_bound_from_int(cls, x: int):
    if x < cls.C:
      return cls(x)
    a1 = 0
    while x >= 10**cls.C:
      x = len(str(x)) - 1
      a1 += 1
    return cls(x, a1)

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
        return Knuth10.lower_bound_from_int(10 ** a[0]).safe_upper_bound()
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
    if len(self.args) == 2 and self.args[1] == 1:
      if self.args[0] <= 1000:
        return 10 ** self.args[0]
    return None


class BigInterval:
  def __init__(self, lower, upper=None):
    if upper is None:
      upper = lower
    if isinstance(lower, int):
      lower = Knuth10.lower_bound_from_int(lower)
    if isinstance(upper, int):
      lb = Knuth10.lower_bound_from_int(upper)
      if lb.try_eval() == upper:
        upper = lb
      else:
        upper = lb.safe_upper_bound()

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
      new_upper = Knuth10.lower_bound_from_int(v_self_u + v_other_u)
      if new_upper.try_eval() != v_self_u + v_other_u:
        new_upper = new_upper.safe_upper_bound()
    else:
      new_upper = max(self.upper, other.upper).safe_upper_bound()

    return BigInterval(new_lower, new_upper)

  def __mul__(self, other):
    if not isinstance(other, BigInterval):
      other = BigInterval(other)

    v_self_l = self.lower.try_eval()
    v_other_l = other.lower.try_eval()
    if v_self_l is not None and v_other_l is not None:
      new_lower = Knuth10.lower_bound_from_int(v_self_l * v_other_l)
    else:
      new_lower = max(self.lower, other.lower)

    v_self_u = self.upper.try_eval()
    v_other_u = other.upper.try_eval()
    if v_self_u is not None and v_other_u is not None:
      new_upper = Knuth10.lower_bound_from_int(v_self_u * v_other_u)
      if new_upper.try_eval() != v_self_u * v_other_u:
        new_upper = new_upper.safe_upper_bound()
    else:
      U_max = max(self.upper, other.upper)
      if len(U_max.args) == 2 and U_max.args[1] == 1:
        power = 2 * U_max.args[0]
        if power < 10**Knuth10.C:
          new_upper = Knuth10(power, 1)
        else:
          new_upper = Knuth10.lower_bound_from_int(power).safe_upper_bound()
      else:
        new_upper = U_max.safe_upper_bound()

    return BigInterval(new_lower, new_upper)

  def __pow__(self, other):
    if not isinstance(other, BigInterval):
      other = BigInterval(other)

    # Lower bound
    if self.lower == Knuth10(1) or self.lower == Knuth10(0):
      new_lower = self.lower
    else:
      if self.lower >= Knuth10(10):
        new_lower = other.lower.apply_g1()
      else:
        new_lower = other.lower.div10().apply_g1()

    # Upper bound
    if self.upper == Knuth10(1) or self.upper == Knuth10(0):
      new_upper = self.upper
    elif self.upper <= Knuth10(10):
      new_upper = other.upper.apply_g1_upper()
    else:
      if len(other.upper.args) == 1 and len(self.upper.args) == 1:
        u_b = self.upper.args[0]
        u_n = other.upper.args[0]
        if u_n * len(str(u_b)) < Knuth10.C:
          new_upper = Knuth10.lower_bound_from_int(u_b**u_n).safe_upper_bound()
        else:
          power = u_n * len(str(u_b))
          new_upper = Knuth10.lower_bound_from_int(10**power).safe_upper_bound()
      else:
        mul_upper = (BigInterval(self.upper) * BigInterval(other.upper)).upper
        new_upper = mul_upper.apply_g1_upper()

    return BigInterval(new_lower, new_upper)

  def __truediv__(self, other):
    if not isinstance(other, BigInterval):
      other = BigInterval(other)

    v_self_l = self.lower.try_eval()
    v_other_u = other.upper.try_eval()
    if v_self_l is not None and v_other_u is not None:
      new_lower = Knuth10.lower_bound_from_int(v_self_l // max(1, v_other_u))
    else:
      if v_other_u is not None and v_other_u <= 10:
        new_lower = self.lower.div10()
      else:
        new_lower = Knuth10(1)

    v_self_u = self.upper.try_eval()
    v_other_l = other.lower.try_eval()
    if v_self_u is not None and v_other_l is not None:
      new_upper = Knuth10.lower_bound_from_int(v_self_u // max(1, v_other_l)).safe_upper_bound()
    else:
      new_upper = self.upper.safe_upper_bound()

    return BigInterval(new_lower, new_upper)

  def __floordiv__(self, other):
    return self.__truediv__(other)

  def __lt__(self, other):
    if not isinstance(other, BigInterval):
      other = BigInterval(other)
    return self.upper < other.lower

  def __gt__(self, other):
    if not isinstance(other, BigInterval):
      other = BigInterval(other)
    return self.lower > other.upper

  def __le__(self, other):
    if not isinstance(other, BigInterval):
      other = BigInterval(other)
    return self.upper <= other.lower

  def __ge__(self, other):
    if not isinstance(other, BigInterval):
      other = BigInterval(other)
    return self.lower >= other.upper
