#! /usr/bin/env python
"""
Unit test for "Numbers/Algebraic_Expression.py"
"""

from Numbers import Algebraic_Expression

import os
import sys
import unittest


def expr(expr_str):
  return Algebraic_Expression.Expression_from_string(expr_str)


class SystemTest(unittest.TestCase):
  def test_parsing(self):
    self.assertEqual(str(expr("13")), "13")
    self.assertEqual(str(expr("x + 1")), "(x + 1)")
    self.assertEqual(str(expr("2 x - 5")), "(2 x - 5)")
    self.assertEqual(str(expr("2 x + -5")), "(2 x - 5)")
    self.assertEqual(str(expr("-5 x + 8")), "(-5 x + 8)")
    # Note: Perhaps this could be simplified ...
    self.assertEqual(str(expr("0 x + 8")), "(0 x + 8)")
    self.assertEqual(str(expr("2 x^2 y z^13 - 3")), "(2 x^2 y z^13 - 3)")
    self.assertEqual(str(expr("x + -1 y + 3")), "(x + -y + 3)")

  def test_expression_cmp(self):
    self.assertEqual(expr("x + 1"), expr("1 x + 1"))
    self.assertLess(expr("x + 1"), expr("x + 2"))
    self.assertLess(expr("x + 1"), expr("2 x + 1"))
    self.assertLess(expr("x + 2 y + 1"), expr("2 x + 2 y + 1"))
    self.assertGreater(expr("x + 1"), expr("1"))
    self.assertGreater(expr("x + 1"), expr("x + 0"))
    self.assertGreater(expr("x + 1"), expr("0 x + 1"))
    self.assertGreater(expr("x + 2 y + 1"), expr("x + y + 1"))
    
    with self.assertRaises(Algebraic_Expression.BadOperation):
      expr("x + 1") < expr("2 x + 0")
    
    with self.assertRaises(Algebraic_Expression.BadOperation):
      expr("x + 2 y") < expr("2 x + y")


if __name__ == '__main__':
  unittest.main()
