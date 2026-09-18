import unittest
from Big_Interval import Knuth10, BigInterval


class TestKnuth10(unittest.TestCase):
  def test_canonicalize(self):
    self.assertEqual(Knuth10(10).args, (10,))
    self.assertEqual(Knuth10(1000).args, (3, 1))
    self.assertEqual(Knuth10(10**10).args, (10, 1))
    self.assertEqual(Knuth10(10**10, 1).args, (10, 2))
    self.assertEqual(Knuth10(1001).args, (1001,))

  def test_compare(self):
    self.assertTrue(Knuth10(3, 2) < Knuth10(1001, 1))
    self.assertTrue(Knuth10(2, 0, 1) < Knuth10(10**10, 1))
    self.assertEqual(Knuth10(10, 0, 1), Knuth10(1, 10))
    self.assertEqual(Knuth10(3, 0, 1), Knuth10(10**10, 1))


class TestBigInterval(unittest.TestCase):
  def test_small_add(self):
    # [10, 10] + [20, 20] = [30, 30]
    A = BigInterval(10, 10)
    B = BigInterval(20, 20)
    C = A + B
    self.assertEqual(C.lower.args, (30,))
    self.assertEqual(C.upper.args, (30,))


if __name__ == "__main__":
  unittest.main()
