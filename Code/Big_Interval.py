# See @big_interval.md for mathematical background.


class Knuth10:
  """
  Represents an exact number of the form:
  g_k^{a_k} ... g_1^{a_1} (a_0)
  where g_1(x) = 10^x, g_2(x) = 10 ^^ x, etc.
  Stored internally as a tuple: (a_0, a_1, ..., a_k).
  """

  def __init__(self, *args):
    self.args = tuple(self._canonicalize(list(args)))

  @staticmethod
  def _canonicalize(A):
    while True:
      A.append(0)
      changed = False
      # Rule 1: g_k(0) = 1
      if A[0] == 0:
        for k in range(1, len(A)):
          if A[k] > 0:
            A[k] -= 1
            A[0] = 1
            changed = True
            break
        if changed:
          continue

      # Rule 2: g_k(1) = 10
      if A[0] == 1:
        for k in range(1, len(A)):
          if A[k] > 0:
            if A[k] == 1:
              A[k] = 0
              A[0] = 10
            else:
              A[0] = A[k]
              A[k] = 0
              A[k + 1] += 1
            changed = True
            break
        if changed:
          continue

      # power of 10
      if A[0] > 10:
        s = str(A[0])
        if s.startswith("1") and all(c == "0" for c in s[1:]):
          A[0] = len(s) - 1
          A[1] += 1
          changed = True
          continue

      break

    while len(A) > 1 and A[-1] == 0:
      A.pop()
    return A

  @staticmethod
  def _eval_bounded(A, limit):
    val = A[0]
    for k in range(1, len(A)):
      for _ in range(A[k]):
        if val > limit:
          return limit + 1
        if k == 1:
          if val > 1000 and limit < 10**1000:
            return limit + 1
          val = 10**val
        elif k == 2:
          if val == 0:
            val = 1
          elif val == 1:
            val = 10
          elif val == 2:
            val = 10**10
          elif val == 3:
            if limit < 10**1000:
              return limit + 1
            val = 10 ** (10**10)
          else:
            return limit + 1
        else:
          if val == 0:
            val = 1
          elif val == 1:
            val = 10
          else:
            return limit + 1
    return min(val, limit + 1)

  @staticmethod
  def _compare_lists(A, B):
    A = A.copy()
    B = B.copy()
    while len(A) > 1 and A[-1] == 0:
      A.pop()
    while len(B) > 1 and B[-1] == 0:
      B.pop()
    while len(A) < len(B):
      A.append(0)
    while len(B) < len(A):
      B.append(0)

    if A == B:
      return 0

    K = len(A) - 1
    while K >= 0 and A[K] == B[K]:
      K -= 1

    if K == 0:
      return 1 if A[0] > B[0] else -1

    swapped = False
    if A[K] < B[K]:
      A, B = B, A
      swapped = True

    # A[K] > B[K]. Cancel min(A[K], B[K]) operations
    m = B[K]
    A[K] -= m
    B[K] -= m

    A_dec = A.copy()
    A_dec[K] -= 1

    if K == 1:
      # Now B[1] is 0! So B is just B[0]
      # A is 10^X
      limit = B[0] + 1
      X = Knuth10._eval_bounded(A_dec[:2], limit)

      import math

      log_B = math.log10(max(1, B[0]))
      if X > log_B:
        res = 1
      elif X < log_B:
        res = -1
      else:
        # rare exact equality? 10^X == B[0]
        val_A = 10**X if X < 1000 else float("inf")
        res = 1 if val_A > B[0] else (-1 if val_A < B[0] else 0)
    else:
      limit = B[K - 1] + 1
      X = Knuth10._eval_bounded(A_dec[: K + 1], limit)
      A_new = [1] + [0] * (K - 2) + [X] + A_dec[K:]
      res = Knuth10._compare_lists(A_new, B)

    return -res if swapped else res

  def __lt__(self, other):
    if not isinstance(other, Knuth10):
      return NotImplemented
    return self._compare_lists(list(self.args), list(other.args)) < 0

  def __eq__(self, other):
    if not isinstance(other, Knuth10):
      return NotImplemented
    return self._compare_lists(list(self.args), list(other.args)) == 0

  def __le__(self, other):
    if not isinstance(other, Knuth10):
      return NotImplemented
    return self < other or self == other

  def __gt__(self, other):
    if not isinstance(other, Knuth10):
      return NotImplemented
    return not (self <= other)

  def __ge__(self, other):
    if not isinstance(other, Knuth10):
      return NotImplemented
    return not (self < other)

  def __repr__(self):
    return f"Knuth10{self.args}"

  def try_eval(self, limit=10**100):
    v = self._eval_bounded(list(self.args), limit)
    if v > limit:
      return None
    return v

  def inc_a0(self):
    """Returns a strict upper bound by incrementing a_0."""
    new_args = list(self.args)
    new_args[0] += 1
    return Knuth10(*new_args)

  def inc_a1(self):
    """Returns a strict upper bound by incrementing a_1 (equivalent to 10^self)."""
    new_args = list(self.args)
    if len(new_args) < 2:
      new_args.append(1)
    else:
      new_args[1] += 1
    return Knuth10(*new_args)


class BigInterval:
  """
  Guaranteed interval arithmetic using Knuth10 boundaries.
  Can also use ints or float('inf').
  """

  def __init__(self, lower, upper):
    if isinstance(lower, int):
      lower = Knuth10(lower)
    if isinstance(upper, int):
      upper = Knuth10(upper)
    self.lower: Knuth10 = lower
    self.upper: Knuth10 = upper

  def __repr__(self):
    return f"BigInterval({self.lower}, {self.upper})"

  def __add__(self, other):
    if not isinstance(other, BigInterval):
      other = BigInterval(other, other)

    v_self_l = self.lower.try_eval()
    v_other_l = other.lower.try_eval()
    if v_self_l is not None and v_other_l is not None:
      new_lower = Knuth10(v_self_l + v_other_l)
    else:
      # All Knuth10 are ≥ 0, so a+b ≥ max(a,b)
      new_lower = max(self.lower, other.lower)

    v_self_u = self.upper.try_eval()
    v_other_u = other.upper.try_eval()
    if v_self_u is not None and v_other_u is not None:
      new_upper = Knuth10(v_self_u + v_other_u)
    else:
      max_upper = max(self.upper, other.upper)
      # TODO: Make less hacky. Guarantee bound!
      new_upper = max_upper.inc_a0()

    return BigInterval(new_lower, new_upper)

  def __mul__(self, other):
    if not isinstance(other, BigInterval):
      other = BigInterval(other, other)

    v_self_l = self.lower.try_eval()
    v_other_l = other.lower.try_eval()
    if v_self_l is not None and v_other_l is not None:
      new_lower = Knuth10(v_self_l * v_other_l)
    else:
      # All Knuth10 are ≥ 1, so a * b ≥ max(a,b)
      new_lower = max(self.lower, other.lower)

    v_self_u = self.upper.try_eval()
    v_other_u = other.upper.try_eval()
    if v_self_u is not None and v_other_u is not None:
      new_upper = Knuth10(v_self_u * v_other_u)
    else:
      max_upper = max(self.upper, other.upper)
      # TODO: Make less hacky. Guarantee bound!
      new_upper = max_upper.inc_a1()

    return BigInterval(new_lower, new_upper)

  def __lt__(self, other):
    if not isinstance(other, BigInterval):
      other = BigInterval(other, other)
    return self.upper < other.lower

  def __gt__(self, other):
    if not isinstance(other, BigInterval):
      other = BigInterval(other, other)
    return self.lower > other.upper
