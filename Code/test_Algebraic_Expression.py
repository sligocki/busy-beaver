#! /usr/bin/env python3
"""
Unit test for "Numbers/Algebraic_Expression.py"
"""

import Algebraic_Expression

import os
import sys
import unittest


def expr(expr_str):
  return Algebraic_Expression.Expression_from_string(expr_str)


class SystemTest(unittest.TestCase):
  def test_parsing(self):
    self.assertEqual(str(expr("13")), "13")
    self.assertEqual(str(expr("x + 1")), "(x + 1)")
    self.assertEqual(str(expr("2 x - 5")), "(2 x + -5)")
    self.assertEqual(str(expr("2 x + -5")), "(2 x + -5)")
    self.assertEqual(str(expr("-5 x + 8")), "(-5 x + 8)")
    # Note: Perhaps this could be simplified ...
    self.assertEqual(str(expr("0 x + 8")), "(0 x + 8)")
    self.assertEqual(str(expr("2 x^2 y z^13 - 3")), "(2 x^2 y z^13 + -3)")
    self.assertEqual(str(expr("x + -1 y + 3")), "(x + -y + 3)")

  def test_equal(self):
    self.assertEqual(expr("x + 1"), expr("1 x + 1"))

  def test_always_cmp(self):
    # Always: 2x >= x
    self.assertTrue(Algebraic_Expression.always_ge(
      expr("2 x"), expr("x")))
    # Not always 2x > x  (could be == if x = 0)
    self.assertFalse(Algebraic_Expression.always_gt(
      expr("2 x"), expr("x")))

    self.assertTrue(Algebraic_Expression.always_ge(
      expr("x + 1"), expr("1")))
    self.assertTrue(Algebraic_Expression.always_ge(
      expr("x + 1"), expr("0 x + 1")))
    self.assertTrue(Algebraic_Expression.always_ge(
      expr("2 x + 1"), expr("x + 1")))
    self.assertTrue(Algebraic_Expression.always_gt(
      expr("x + 2"), expr("x + 1")))
    self.assertTrue(Algebraic_Expression.always_gt(
      expr("x + 2"), expr("1")))
    self.assertTrue(Algebraic_Expression.always_gt(
      expr("x + 1"), expr("x + 0")))
    self.assertTrue(Algebraic_Expression.always_ge(
      expr("x + 2 y + 1"), expr("x + y + 1")))
    self.assertTrue(Algebraic_Expression.always_ge(
      expr("2 x + 2 y + 1"), expr("x + 2 y + 1")))
    self.assertTrue(Algebraic_Expression.always_gt(
      expr("3 x + 2 y + 2"), expr("x + y + 1")))

  def test_divide(self):
    n = expr("n")
    sum_n = n * (n+1) / 2
    n_var = n.variable()

    self.assertEqual(sum_n.substitute({n_var : 10}), 55)
    self.assertEqual(sum_n.substitute({n_var : 13}), 91)

  def test_as_strictly_linear(self):
    n = expr("n")
    n_var = n.variable()

    # Positive cases
    self.assertEqual(n.as_strictly_linear(), (n_var, 1, 0))
    self.assertEqual((n + 8).as_strictly_linear(), (n_var, 1, 8))
    self.assertEqual((n - 13).as_strictly_linear(), (n_var, 1, -13))
    self.assertEqual((2 * n - 1).as_strictly_linear(), (n_var, 2, -1))
    self.assertEqual((3 - n).as_strictly_linear(), (n_var, -1, 3))

    # Negative cases
    # Constants don't count as "strictly" linear.
    self.assertEqual(expr("813").as_strictly_linear(), None)
    self.assertEqual((n*n).as_strictly_linear(), None)
    self.assertEqual((n*expr("m")).as_strictly_linear(), None)


if __name__ == '__main__':
  unittest.main()
