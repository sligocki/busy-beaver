#! /usr/bin/env python3

import sys
import unittest

import Exp_Int
import io_pb2
from Exp_Int import exp_int, sign, try_eval
from Halting_Lib import get_big_int, set_big_int


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
    self.assertEqual(sign(-a), -1)
    self.assertEqual(sign(-exp_int(7, 7) + 3), -1)

  def test_eval(self):
    self.assertEqual(try_eval(exp_int(2, 13)), 2**13)
    self.assertEqual(
      try_eval((47 * exp_int(3, 21) + 20 * exp_int(3, 11) - 5) / 2),
      (47 * 3**21 + 20 * 3**11 - 5) / 2,
    )
    self.assertEqual(try_eval(exp_int(2, exp_int(2, exp_int(2, 2)))), 2 ** (2 ** (2**2)))
    self.assertEqual(try_eval(-exp_int(7, 7) + 3), 3 - 7**7)

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

  def test_compare_close(self):
    x = exp_int(7, 7)
    a = (7**10 + 1) * exp_int(7, x)
    b = exp_int(7, x + 10)
    self.assertGreater(a, b)
    self.assertLess(-a, -b)
    self.assertEqual(sign(a - b), 1)
    self.assertEqual(sign(b - a), -1)

  def todo_test_compare_closer(self):
    x = exp_int(7, exp_int(7, 7))
    a = (7**10 + 1) * exp_int(7, x)
    b = exp_int(7, x + 10)
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
    A3 = (exp_int(3, k2 + 3) - 11) / 2
    (k3, r3) = divmod(A3, 4)
    self.assertEqual(r3, 3)

    A4 = (exp_int(3, k3 + 3) + 1) / 2
    (k4, r4) = divmod(A4, 4)
    self.assertEqual(r4, 1)

    A5 = (exp_int(3, k4 + 3) - 11) / 2
    (k5, r5) = divmod(A5, 4)
    self.assertEqual(r5, 3)

    A6 = (exp_int(3, k5 + 3) + 1) / 2
    (k6, r6) = divmod(A6, 4)
    self.assertEqual(r6, 2)

  def test_protobuf(self):
    x = 138
    for n in range(100):
      x = 13 * exp_int(5, x) - 1

    x_proto = io_pb2.BigInt()
    set_big_int(x_proto, x)
    x_pb_bytes = x_proto.SerializeToString()
    x_pb_reparsed = io_pb2.BigInt()
    x_pb_reparsed.ParseFromString(x_pb_bytes)
    self.assertTrue(Exp_Int.struct_eq(get_big_int(x_pb_reparsed), x))

  def test_tex_formula(self):
    self.assertEqual(Exp_Int.tex_formula(42), "42")

    t1 = Exp_Int.ExpTerm(2, 1, 5)
    self.assertEqual(Exp_Int.tex_formula(t1), "2^{ 5 }")

    t2 = Exp_Int.ExpTerm(2, 3, 5)
    self.assertEqual(Exp_Int.tex_formula(t2), r"3 \cdot 2^{ 5 }")

    e1 = exp_int(2, 5)
    self.assertEqual(Exp_Int.tex_formula(e1), "2^{ 5 }")
    self.assertEqual(e1.tex_formula(), "2^{ 5 }")

    e2 = exp_int(2, 5) + 3
    self.assertEqual(Exp_Int.tex_formula(e2), "3 + 2^{ 5 }")

    e3 = (exp_int(2, 5) + 3) / 7
    self.assertEqual(Exp_Int.tex_formula(e3), r"\frac{ 3 + 2^{ 5 } }{ 7 }")

    e4 = Exp_Int.ExpInt([Exp_Int.ExpTerm(2, 3, 5), Exp_Int.ExpTerm(2, 1, 4)], const=1, denom=5)
    self.assertEqual(Exp_Int.tex_formula(e4), r"\frac{ 1 + 3 \cdot 2^{ 5 } + 2^{ 4 } }{ 5 }")

    e5 = exp_int(3, exp_int(2, 5))
    self.assertEqual(Exp_Int.tex_formula(e5), "3^{ 2^{ 5 } }")

  def test_deep_tower(self):
    # Tests that deep towers (depth > recursion limit) do not cause
    # RecursionError for is_const, struct_eq, and tex_formula.
    old_limit = sys.getrecursionlimit()
    try:
      sys.setrecursionlimit(200)
      x = 2
      for _ in range(300):
        x = exp_int(2, x)
      self.assertEqual(x.depth, 300)
      self.assertTrue(x.is_const)
      self.assertTrue(Exp_Int.struct_eq(x, x))
      latex = Exp_Int.tex_formula(x)
      self.assertTrue(len(latex) > 1000)
    finally:
      sys.setrecursionlimit(old_limit)

  def test_max_depth_exceeded(self):
    x = 2
    for _ in range(Exp_Int.MAX_DEPTH):
      x = exp_int(2, x)
    with self.assertRaises(Exp_Int.ExpIntGaveUp):
      exp_int(2, x)

  def test_lazy_formula_str(self):
    x = exp_int(2, 500)
    # formula_str should not be computed initially in __dict__
    self.assertNotIn("formula_str", x.__dict__)
    self.assertNotIn("formula_str", x.terms[0].__dict__)
    # Accessing formula_str computes and caches it
    expected = "(2^500)"
    self.assertEqual(x.formula_str, expected)
    self.assertEqual(str(x), expected)
    self.assertIn("formula_str", x.__dict__)

  def test_legacy_unpickle_eval(self):
    import pickle

    x = exp_int(2, 500)
    del x._uparrow_size_approx
    x.terms[0].__dict__.pop("_uparrow_size_approx", None)
    # Simulate legacy object having tower_value in __dict__ and no _uparrow_size_approx
    x.__dict__["tower_value"] = (1, 150.5)
    x.terms[0].__dict__["tower_value"] = (1, 150.5)

    data = pickle.dumps(x)
    loaded = pickle.loads(data)

    self.assertTrue(hasattr(loaded, "_uparrow_size_approx"))
    self.assertTrue(loaded > 100)

  def todo_test_bug_normalize(self):
    # Simplified version of issue
    x = exp_int(7, exp_int(7, exp_int(7, 7))) + exp_int(7, 1 + exp_int(7, exp_int(7, 7)))
    self.assertEqual(sign(x - x), 0)

    # Came up while simulating 1RB1LC_1LC1LB_0LE0LD_0LC1LB_1RF0RA_0RE---
    a = 5 * exp_int(2, 81 + 25 * exp_int(2, 5 * exp_int(2, 95)))
    b = exp_int(2, -12 + 25 * exp_int(2, 5 * exp_int(2, 95)))
    x = a + b
    self.assertEqual(sign(x + (-x)), 0)


if __name__ == "__main__":
  unittest.main()
