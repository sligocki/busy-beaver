#! /usr/bin/env python3

import Exp_Int
from Exp_Int import exp_int, ExpTerm, ExpInt, try_eval

import unittest


class ExpIntTest(unittest.TestCase):
  def test_eval(self):
    self.assertEqual(try_eval(exp_int(2, 13)), 2**13)
    self.assertEqual(try_eval((47 * exp_int(3, 21) + 20 * exp_int(3, 11) - 5) / 2),
                     (47 * 3**21 + 20 * 3**11 - 5) / 2)
    self.assertEqual(try_eval(exp_int(2, exp_int(2, exp_int(2, 2)))),
                     2**(2**(2**2)))

  def test_add(self):
    x = (11 * exp_int(3, 13875) - 3) / 2
    y = (4 * exp_int(3, x) + 6) / 4

    self.assertTrue(Exp_Int.struct_eq(y + 4, (4 * exp_int(3, x) + 22) / 4))
    self.assertTrue(Exp_Int.struct_eq(y - 4, (4 * exp_int(3, x) - 10) / 4))

    # Make sure we can simplify this expression
    self.assertEqual(y - (y - 4), 4)
    self.assertTrue(Exp_Int.struct_eq(y + y, 2 * y))
    # self.assertTrue(Exp_Int.struct_eq((x+y)*(x+y), x*x + 2*x*y + y*y))

  def text_compare(self):
    x = (11 * exp_int(3, 13875) - 3) / 2
    y = (4 * exp_int(3, x) + 6) / 4
    self.assertGreater(y, x)
    self.assertLess(-y, -x)

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


if __name__ == '__main__':
  unittest.main()
