#! /usr/bin/env python3

import Lin_Recur_Detect

import unittest

import Halting_Lib
import IO

import io_pb2


class SystemTest(unittest.TestCase):
  def test_simple(self):
    ttable = IO.parse_ttable("1RB 1LA  0LA 1RA")
    params = io_pb2.LinRecurFilterParams()
    params.max_steps = 100
    params.find_min_start_step = True

    result = io_pb2.LinRecurFilterResult()
    Lin_Recur_Detect.filter(ttable, params, result)

    self.assertTrue(result.success)
    self.assertEqual(result.start_step, 7)
    self.assertEqual(result.period, 5)
    self.assertEqual(result.offset, -1)

    self.assertTrue(result.status.halt_status.is_decided)
    self.assertFalse(result.status.halt_status.is_halting)
    self.assertTrue(result.status.quasihalt_status.is_decided)
    self.assertFalse(result.status.quasihalt_status.is_quasihalting)

  def test_in_place(self):
    ttable = IO.parse_ttable("1RB ---  0LB 1RB")
    params = io_pb2.LinRecurFilterParams()
    params.max_steps = 100
    params.find_min_start_step = True

    result = io_pb2.LinRecurFilterResult()
    Lin_Recur_Detect.filter(ttable, params, result)

    self.assertTrue(result.success)
    self.assertEqual(result.start_step, 1)
    self.assertEqual(result.period, 2)
    self.assertEqual(result.offset, 0)

    self.assertTrue(result.status.halt_status.is_decided)
    self.assertFalse(result.status.halt_status.is_halting)
    self.assertTrue(result.status.quasihalt_status.is_decided)
    self.assertTrue(result.status.quasihalt_status.is_quasihalting)
    self.assertEqual(Halting_Lib.get_big_int(result.status.quasihalt_status.quasihalt_steps),
                     1)
    self.assertEqual(result.status.quasihalt_status.quasihalt_state, 0)  # A

  def test_complex(self):
    # Super-long period and recurrence start. One of Boyd's machines.
    ttable = IO.parse_ttable("1RB 0RA  1RC 0RB  1LD 1LC  1RA 0LC")
    params = io_pb2.LinRecurFilterParams()
    params.max_steps = 1_000_000
    params.find_min_start_step = True

    result = io_pb2.LinRecurFilterResult()
    Lin_Recur_Detect.filter(ttable, params, result)

    self.assertTrue(result.success)
    self.assertEqual(result.start_step, 7_170)
    self.assertEqual(result.period,    29_117)
    self.assertEqual(result.offset,      +525)

    self.assertTrue(result.status.halt_status.is_decided)
    self.assertFalse(result.status.halt_status.is_halting)
    self.assertTrue(result.status.quasihalt_status.is_decided)
    self.assertFalse(result.status.quasihalt_status.is_quasihalting)

  def test_complex_no_min_start(self):
    # Make sure that find_min_start_step=False is still finding all correct
    # values (except for start_step which might be big).
    ttable = IO.parse_ttable("1RB 0RA  1RC 0RB  1LD 1LC  1RA 0LC")
    params = io_pb2.LinRecurFilterParams()
    params.max_steps = 1_000_000
    params.find_min_start_step = False

    result = io_pb2.LinRecurFilterResult()
    Lin_Recur_Detect.filter(ttable, params, result)

    self.assertTrue(result.success)
    self.assertGreaterEqual(result.start_step, 7_170)
    self.assertEqual(result.period,    29_117)
    self.assertEqual(result.offset,      +525)

    self.assertTrue(result.status.halt_status.is_decided)
    self.assertFalse(result.status.halt_status.is_halting)
    self.assertTrue(result.status.quasihalt_status.is_decided)
    self.assertFalse(result.status.quasihalt_status.is_quasihalting)

  def test_quasihalt(self):
    # Test a non-trivial quasihalting machine.
    ttable = IO.parse_ttable("1RB 1LC  1RC 0RC  0LD 0LA  0RA 0LA")
    params = io_pb2.LinRecurFilterParams()
    params.max_steps = 100
    params.find_min_start_step = False

    result = io_pb2.LinRecurFilterResult()
    Lin_Recur_Detect.filter(ttable, params, result)

    self.assertTrue(result.status.halt_status.is_decided)
    self.assertFalse(result.status.halt_status.is_halting)

    self.assertTrue(result.status.quasihalt_status.is_decided)
    self.assertTrue(result.status.quasihalt_status.is_quasihalting)
    self.assertEqual(Halting_Lib.get_big_int(result.status.quasihalt_status.quasihalt_steps),
                     61)
    self.assertEqual(result.status.quasihalt_status.quasihalt_state, 3)  # D

  def test_halt(self):
    # Test a non-trivial halting machine.
    ttable = IO.parse_ttable("1RB 1LB  1LA 0LC  1RZ 1LD  1RD 0RA")
    params = io_pb2.LinRecurFilterParams()
    params.max_steps = 200
    params.find_min_start_step = False

    result = io_pb2.LinRecurFilterResult()
    Lin_Recur_Detect.filter(ttable, params, result)

    self.assertTrue(result.status.halt_status.is_decided)
    self.assertTrue(result.status.halt_status.is_halting)
    self.assertEqual(Halting_Lib.get_big_int(result.status.halt_status.halt_steps),
                     107)
    # We do not currently calculate halting score in LR. But if we do in the
    # future, this will automatically test it.
    if result.status.halt_status.HasField("halt_score"):
      self.assertEqual(Halting_Lib.get_big_int(result.status.halt_status.halt_score),
                       13)

    self.assertTrue(result.status.quasihalt_status.is_decided)
    self.assertFalse(result.status.quasihalt_status.is_quasihalting)


if __name__ == "__main__":
  unittest.main()
