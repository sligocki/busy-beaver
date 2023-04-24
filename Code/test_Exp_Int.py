#! /usr/bin/env python3

import Exp_Int
from Exp_Int import *

import unittest

from Halting_Lib import set_big_int, get_big_int


class ExpIntTest(unittest.TestCase):

  def test_sign(self):
    self.assertEqual(sign(138), 1)
    self.assertEqual(sign(-127), -1)
    self.assertEqual(sign(0), 0)
    a = exp_int(7, exp_int(7, 7))
    b = exp_int(7, exp_int(7, 8))
    self.assertLess(a, b)
    self.assertEqual(sign(a - b), -1)
    self.assertEqual(sign(b - a), 1)
    self.assertEqual(sign(a - a), 0)

  def test_eval(self):
    self.assertEqual(try_eval(exp_int(2, 13)), 2**13)
    self.assertEqual(try_eval((47 * exp_int(3, 21) + 20 * exp_int(3, 11) - 5) / 2),
                     (47 * 3**21 + 20 * 3**11 - 5) / 2)
    self.assertEqual(try_eval(exp_int(2, exp_int(2, exp_int(2, 2)))),
                     2**(2**(2**2)))

  def test_formula_str(self):
    self.assertEqual(exp_int(2, exp_int(2, exp_int(2, 2))).formula_str,
                     "2^2^2^2")

  def test_compare_close_ratios(self):
    mid = exp_int(7, exp_int(7, 7))
    low = 4 * mid / 5
    high = 6 * mid / 5
    self.assertGreater(mid, low)
    self.assertLess(low, mid)
    self.assertEqual(sign(mid - low), 1)
    self.assertEqual(sign(low - mid), -1)

    self.assertLess(mid, high)
    self.assertGreater(high, mid)
    self.assertEqual(sign(high - mid), 1)
    self.assertEqual(sign(mid - high), -1)

    self.assertLess(low, high)
    self.assertGreater(high, low)
    self.assertEqual(sign(high - low), 1)
    self.assertEqual(sign(low - high), -1)

  def test_compare_close_powers(self):
    x = exp_int(7, 7)
    a = (7**10 + 1) * exp_int(7, x)
    b = exp_int(7, x+10)
    self.assertGreater(a, b)
    self.assertLess(-a, -b)
    self.assertEqual(sign(a - b), 1)
    self.assertEqual(sign(b - a), -1)

  def test_add(self):
    x = (11 * exp_int(3, 13875) - 3) / 2
    y = (4 * exp_int(3, x) + 6) / 4

    self.assertTrue(Exp_Int.struct_eq(y + 4, (4 * exp_int(3, x) + 22) / 4))
    self.assertTrue(Exp_Int.struct_eq(y - 4, (4 * exp_int(3, x) - 10) / 4))

    # Make sure we can simplify this expression
    self.assertEqual(y - (y - 4), 4)
    self.assertTrue(Exp_Int.struct_eq(y + y, 2 * y))
    # TODO: Fix this
    # self.assertTrue(Exp_Int.struct_eq((x+y)*(x+y), x*x + 2*x*y + y*y))

  def text_compare(self):
    x = (11 * exp_int(3, 13875) - 3) / 2
    y = (4 * exp_int(3, x) + 6) / 4
    self.assertGreater(y, x)
    self.assertLess(-y, -x)
    self.assertLess(x, y)
    self.assertGreater(-x, -y)

  def test_mod_6x2_t15(self):
    # From https://www.sligocki.com/2022/06/21/bb-6-2-t15.html
    k2 = 22143
    A3 = (exp_int(3, k2+3) - 11) / 2
    (k3, r3) = divmod(A3, 4)
    self.assertEqual(r3, 3)

    A4 = (exp_int(3, k3+3) + 1) / 2
    (k4, r4) = divmod(A4, 4)
    self.assertEqual(r4, 1)

    A5 = (exp_int(3, k4+3) - 11) / 2
    (k5, r5) = divmod(A5, 4)
    self.assertEqual(r5, 3)

    A6 = (exp_int(3, k5+3) + 1) / 2
    (k6, r6) = divmod(A6, 4)
    self.assertEqual(r6, 2)

  def test_protobuf(self):
    x = 138
    for n in range(50):
      x = 13 * exp_int(5, x) - 1

    x_proto = io_pb2.BigInt()
    set_big_int(x_proto, x)
    self.assertTrue(Exp_Int.struct_eq(get_big_int(x_proto), x))


if __name__ == '__main__':
  unittest.main()
