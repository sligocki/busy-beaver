import unittest

from Big_Interval import Knuth10, BigInterval


class TestKnuth10(unittest.TestCase):
  def test_lower_bound_from_int(self):
    # With C=10
    self.assertEqual(Knuth10.lower_bound_from_int(9).args, (9,))
    self.assertEqual(Knuth10.lower_bound_from_int(10).args, (10,))
    self.assertEqual(Knuth10.lower_bound_from_int(1000).args, (1000,))
    self.assertEqual(Knuth10.lower_bound_from_int(10**1000).args, (1000, 1))
    self.assertEqual(Knuth10.lower_bound_from_int(10**10000).args, (10000, 1))

  def test_safe_upper_bound(self):
    # Base increment
    # 10^1000 +1 ≤ 10^1001
    self.assertEqual(Knuth10(1000, 1).safe_upper_bound().args, (1001, 1))
    # Rollover to next operation
    # 10^{10^1000 - 1} +1 ≤ 10^10^1000
    self.assertEqual(Knuth10(10**1000 - 1, 1).safe_upper_bound().args, (1000, 2))
    # Rollover past max allowed a_i
    # (10^)^997 (10^1000 - 1) +1 ≤ 10^^1000
    self.assertEqual(Knuth10(10**1000 - 1, 997).safe_upper_bound().args, (1000, 0, 1))

  def test_compare(self):
    self.assertTrue(Knuth10(100) < Knuth10(10, 1))
    self.assertTrue(Knuth10(10, 1) < Knuth10(11, 1))
    self.assertTrue(Knuth10(10**10 - 1, 8) < Knuth10(10, 0, 1))
    self.assertTrue(Knuth10(10, 0, 1) == Knuth10(10, 0, 1))


class TestBigInterval(unittest.TestCase):
  def test_small_add(self):
    # [10, 10] + [20, 20] = [30, 30]
    A = BigInterval(10)
    B = BigInterval(20)
    C = A + B
    self.assertEqual(C.lower.args, (30,))
    self.assertEqual(C.upper.args, (30,))

  def test_huge_add(self):
    # 10^100 + 10^200 -> bounds around 10^200
    A = BigInterval(10**1000)
    B = BigInterval(10**2000)
    C = A + B
    self.assertEqual(C.lower.args, (2000, 1))
    self.assertEqual(C.upper.args, (2001, 1))

  def test_small_mul(self):
    # [10, 10] * [20, 20] = [200, 200]
    A = BigInterval(10)
    B = BigInterval(20)
    C = A * B
    self.assertEqual(C.lower.args, (200,))
    self.assertEqual(C.upper.args, (200,))

  def test_huge_mul(self):
    # 10^100 * 10^200 -> exact lower and upper bound 10^300
    A = BigInterval(10**1000)
    B = BigInterval(10**2000)
    C = A * B
    self.assertEqual(C.lower.args, (2000, 1))
    self.assertEqual(C.upper.args, (3000, 1))

  def test_mul_x_squared(self):
    # X = 10^100. X^2 = 10^200.
    A = BigInterval(10**1000)
    C = A * A
    self.assertEqual(C.lower.args, (1000, 1))
    self.assertEqual(C.upper.args, (2000, 1))

    # Test X^2 logic without exact eval (use 10^10000)
    A = BigInterval(Knuth10(10000, 1), Knuth10(10000, 1))
    C = A * A
    self.assertEqual(C.lower.args, (10000, 1))  # lower bound is max(A, B) when not eval'd
    self.assertEqual(C.upper.args, (20000, 1))  # upper bound uses X^2 special logic

  def test_pow(self):
    # 10 ** 100 -> (100, 1)
    A = BigInterval(10)
    B = BigInterval(1000)
    C = A**B
    self.assertEqual(C.lower.args, (1000, 1))
    self.assertEqual(C.upper.args, (1001, 1))

    # 2 ** 100
    A = BigInterval(2)
    B = BigInterval(10000)
    C = A**B
    self.assertEqual(C.lower.args, (3010, 1))
    self.assertEqual(C.upper.args, (3011, 1))

  def test_huge_pow(self):
    # 10 ** (10**100)
    A = BigInterval(10)
    B = BigInterval(10**1000)
    C = A**B
    self.assertEqual(C.lower.args, (1000, 2))
    self.assertEqual(C.upper.args, (1000, 2))

  def test_truediv(self):
    A = BigInterval(100)
    B = BigInterval(3)
    C = A / B
    self.assertEqual(C.lower.args, (33,))
    self.assertEqual(C.upper.args, (34,))


if __name__ == "__main__":
  unittest.main()
