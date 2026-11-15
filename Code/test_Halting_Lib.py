#! /usr/bin/env python3

import unittest

import Halting_Lib
import io_pb2
from Algebraic_Expression import ConstantToExpression, Variable, VariableToExpression
from Exp_Int import exp_int
from Iterated_Expression import Iterated_Expression


def set_get_big_int(value):
  big = io_pb2.BigInt()
  Halting_Lib.set_big_int(big, value)
  return Halting_Lib.get_big_int(big)


class SystemTest(unittest.TestCase):
  def test_big_int_success(self):
    self.assertEqual(set_get_big_int(0), 0)
    self.assertEqual(set_get_big_int(138), 138)
    self.assertEqual(set_get_big_int(1_000_000), 1_000_000)
    self.assertEqual(set_get_big_int(1_000_000_000_000), 1_000_000_000_000)
    self.assertEqual(
      set_get_big_int(1_000_000_000_000_000_000_000_000),
      1_000_000_000_000_000_000_000_000,
    )
    self.assertEqual(set_get_big_int(13**138), 13**138)

  def test_big_int_near_split(self):
    self.assertEqual(set_get_big_int(2**64 - 1), 2**64 - 1)
    self.assertEqual(set_get_big_int(2**64), 2**64)
    self.assertEqual(set_get_big_int(2**64 + 1), 2**64 + 1)

  def test_big_int_expr_types(self):
    x = Variable(10)
    step = exp_int(2, VariableToExpression(x)) + 1
    it_expr = Iterated_Expression(step, x, 10, exp_int(2, 200))
    it_math = it_expr + ConstantToExpression(7)

    for val in (step.substitute({x: 5}), it_expr, it_math):
      loaded = set_get_big_int(val)
      self.assertEqual(type(loaded), type(val))
      self.assertEqual(str(loaded), str(val))

  def test_set_halting_error_leaves_undecided(self):
    status = io_pb2.BBStatus()
    with self.assertRaises(TypeError):
      Halting_Lib.set_halting(status, halt_steps=10, halt_score=13.8, from_state=2, from_symbol=1)
    self.assertFalse(status.halt_status.is_decided)
    self.assertFalse(status.halt_status.is_halting)

  def test_big_int_error(self):
    # Error cases
    with self.assertRaises(ValueError):
      set_get_big_int(-1)
    with self.assertRaises(TypeError):
      set_get_big_int(13.8)


if __name__ == "__main__":
  unittest.main()
