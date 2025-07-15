#! /usr/bin/env python3

from Formula_Int import *

import unittest


class FormulaIntTest(unittest.TestCase):
  def test_mod(self):
    x = Int(13)
    self.assertEqual(x % 10, 3)
    self.assertEqual((-x) % 10, 7)
    self.assertEqual((x + 8) % 10, 1)
    self.assertEqual((x - 8) % 10, 5)
    self.assertEqual((2*x) % 10, 6)

  def test_mod_div(self):
    x = Int(13)
    self.assertEqual((8*x + 1)/5 % 10, 1)

  def test_mod_pow(self):
    k = Int(1)
    self.assertEqual((3**(k+3) - 11)/2 % 4, 3)

  def test_6x2_t15(self):
    def t15_step(n: FormulaInt) -> tuple[FormulaInt, int]:
      k, r = divmod(n, 4)
      if r == 3:
        return (3**(k+3) + 1)/2, r
      else:
        return (3**(k+3) - 11)/2, r

    A = Int(5)
    A, r = t15_step(A)
    self.assertEqual(r, 1)
    A, r = t15_step(A)
    self.assertEqual(r, 3)
    A, r = t15_step(A)
    self.assertEqual(r, 2)
    A, r = t15_step(A)
    self.assertEqual(r, 3)
    A, r = t15_step(A)
    self.assertEqual(r, 1)
    A, r = t15_step(A)
    self.assertEqual(r, 3)
    A, r = t15_step(A)
    self.assertEqual(r, 2)
    A, r = t15_step(A)
    self.assertEqual(r, 3)
    A, r = t15_step(A)
    self.assertEqual(r, 1)
    A, r = t15_step(A)
    self.assertEqual(r, 3)
    A, r = t15_step(A)
    self.assertEqual(r, 1)
    A, r = t15_step(A)
    self.assertEqual(r, 3)
    A, r = t15_step(A)
    self.assertEqual(r, 2)
    A, r = t15_step(A)
    self.assertEqual(r, 3)
    A, r = t15_step(A)
    self.assertEqual(r, 1)
    A, r = t15_step(A)
    self.assertEqual(r, 0)


if __name__ == '__main__':
  unittest.main()
