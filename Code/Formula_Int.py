# Classes designed to represent large integers using formulas (symbolically).

from __future__ import annotations

from dataclasses import dataclass

from Math import carmichael


type GenInt = FormulaInt | int

def try_as_basic_int(n: GenInt) -> int | None:
  if isinstance(n, (int, Int)):
    return int(n)
  return None

class FormulaInt:
  """Abstract Base Class for Formula Integers."""
  def __add__(self, other: GenInt) -> FormulaInt:
    return Sum.new([self, other])
  def __radd__(self, other: GenInt) -> FormulaInt:
    return self + other

  def __sub__(self, other: GenInt) -> FormulaInt:
    return self + (-other)
  def __rsub__(self, other: GenInt) -> FormulaInt:
    return (-self) + other

  def __mul__(self, other: GenInt) -> FormulaInt:
    return Mul(self, other)
  def __rmul__(self, other: GenInt) -> FormulaInt:
    return self * other
  
  def __neg__(self) -> FormulaInt:
    return -1 * self

  def __truediv__(self, denom: int) -> FormulaInt:
    return Div(self, denom)

  def __rpow__(self, base: int) -> FormulaInt:
    return Pow(base, self)
  
  def __mod__(self, modulus: int) -> int:
    raise NotImplementedError(self)
  
  def __divmod__(self, other: int) -> tuple[FormulaInt, int]:
    m = self % other
    return (self - m)/other, m


@dataclass(frozen=True)
class Int(FormulaInt):
  val: int

  def __int__(self) -> int:
    return self.val

  def __mod__(self, modulus: int) -> int:
    return self.val % modulus

@dataclass(frozen=True)
class Sum(FormulaInt):
  terms: list[FormulaInt]
  const: int

  @staticmethod
  def new(vals: list[GenInt]) -> Sum:
    terms: list[FormulaInt] = []
    const = 0
    for val in vals:
      if (ival := try_as_basic_int(val)) != None:
        const += ival
      else:
        terms.append(val)
    return Sum(terms, const)
  
  def __add__(self, other: GenInt) -> FormulaInt:
    terms = self.terms + [self.const]
    if isinstance(other, Sum):
      terms += other.terms + [other.const]
    else:
      terms.append(other)
    return Sum.new(terms)

  def __mod__(self, modulus: int) -> int:
    return (sum(term % modulus for term in self.terms) + self.const) % modulus

@dataclass(frozen=True)
class Mul(FormulaInt):
  left: GenInt
  right: GenInt

  def __mod__(self, modulus: int) -> int:
    return ((self.left % modulus) * (self.right % modulus)) % modulus

@dataclass(frozen=True)
class Div(FormulaInt):
  numer: GenInt
  denom: int

  def __mod__(self, modulus: int) -> int:
    # numer/denom = k modulus + r
    # numer = k (modulus denom) + (r denom)
    num_mod = self.numer % (modulus * self.denom)
    k, r = divmod(num_mod, self.denom)
    assert r == 0, (self, modulus, (modulus * self.denom), num_mod, k, r)
    return k % modulus


def exp_mod(b: int, k, m: int) -> int:
  """Evaluate b^k % m efficiently for huge k."""
  kp, k0 = carmichael(m)
  # for all kn >= k0: b^kn = b^{kp+kn} (mod m)
  #   See: https://en.wikipedia.org/wiki/Carmichael_function#Exponential_cycle_length
  kn = (k - k0) % kp + k0
  # b^k = b^kn (mod m)
  return pow(b, kn, m)

@dataclass(frozen=True)
class Pow(FormulaInt):
  base: int
  exp: GenInt

  def __mod__(self, modulus: int) -> int:
    return exp_mod(self.base, self.exp, modulus)