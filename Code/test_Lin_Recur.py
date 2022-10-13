#! /usr/bin/env python3

import Lin_Recur_Detect

import unittest

import Halting_Lib
import IO

import io_pb2


class SystemTest(unittest.TestCase):
  def test_simple(self):
    tm = IO.parse_tm("1RB1LA_0LA1RA")

    lr_info = io_pb2.LinRecurFilterInfo()
    lr_info.parameters.max_steps = 100
    lr_info.parameters.find_min_start_step = True
    bb_status = io_pb2.BBStatus()
    Lin_Recur_Detect.filter(tm, lr_info, bb_status)

    self.assertTrue(lr_info.result.success)
    self.assertEqual(lr_info.result.start_step, 7)
    self.assertEqual(lr_info.result.period, 5)
    self.assertEqual(lr_info.result.offset, -1)

    self.assertTrue(bb_status.halt_status.is_decided)
    self.assertFalse(bb_status.halt_status.is_halting)
    self.assertTrue(bb_status.quasihalt_status.is_decided)
    self.assertFalse(bb_status.quasihalt_status.is_quasihalting)

  def test_in_place(self):
    tm = IO.parse_tm("1RB---_0LB1RB")

    lr_info = io_pb2.LinRecurFilterInfo()
    lr_info.parameters.max_steps = 100
    lr_info.parameters.find_min_start_step = True
    bb_status = io_pb2.BBStatus()
    Lin_Recur_Detect.filter(tm, lr_info, bb_status)

    self.assertTrue(lr_info.result.success)
    self.assertEqual(lr_info.result.start_step, 1)
    self.assertEqual(lr_info.result.period, 2)
    self.assertEqual(lr_info.result.offset, 0)

    self.assertTrue(bb_status.halt_status.is_decided)
    self.assertFalse(bb_status.halt_status.is_halting)
    self.assertTrue(bb_status.quasihalt_status.is_decided)
    self.assertTrue(bb_status.quasihalt_status.is_quasihalting)
    self.assertEqual(Halting_Lib.get_big_int(bb_status.quasihalt_status.quasihalt_steps),
                     1)
    self.assertEqual(bb_status.quasihalt_status.quasihalt_state, 0)  # A

  def test_complex(self):
    # Super-long period and recurrence start. One of Boyd's machines.
    tm = IO.parse_tm("1RB0RA_1RC0RB_1LD1LC_1RA0LC")

    lr_info = io_pb2.LinRecurFilterInfo()
    lr_info.parameters.max_steps = 1_000_000
    lr_info.parameters.find_min_start_step = True
    bb_status = io_pb2.BBStatus()
    Lin_Recur_Detect.filter(tm, lr_info, bb_status)

    self.assertTrue(lr_info.result.success)
    self.assertEqual(lr_info.result.start_step, 7_170)
    self.assertEqual(lr_info.result.period,    29_117)
    self.assertEqual(lr_info.result.offset,      +525)

    self.assertTrue(bb_status.halt_status.is_decided)
    self.assertFalse(bb_status.halt_status.is_halting)
    self.assertTrue(bb_status.quasihalt_status.is_decided)
    self.assertFalse(bb_status.quasihalt_status.is_quasihalting)

  def test_complex_no_min_start(self):
    # Make sure that find_min_start_step=False is still finding all correct
    # values (except for start_step which might be big).
    tm = IO.parse_tm("1RB0RA_1RC0RB_1LD1LC_1RA0LC")

    lr_info = io_pb2.LinRecurFilterInfo()
    lr_info.parameters.max_steps = 1_000_000
    lr_info.parameters.find_min_start_step = False
    bb_status = io_pb2.BBStatus()
    Lin_Recur_Detect.filter(tm, lr_info, bb_status)

    self.assertTrue(lr_info.result.success)
    self.assertGreaterEqual(lr_info.result.start_step, 7_170)
    self.assertEqual(lr_info.result.period,    29_117)
    self.assertEqual(lr_info.result.offset,      +525)

    self.assertTrue(bb_status.halt_status.is_decided)
    self.assertFalse(bb_status.halt_status.is_halting)
    self.assertTrue(bb_status.quasihalt_status.is_decided)
    self.assertFalse(bb_status.quasihalt_status.is_quasihalting)

  def test_quasihalt(self):
    # Test a non-trivial quasihalting machine.
    tm = IO.parse_tm("1RB1LC_1RC0RC_0LD0LA_0RA0LA")

    lr_info = io_pb2.LinRecurFilterInfo()
    lr_info.parameters.max_steps = 100
    lr_info.parameters.find_min_start_step = False
    bb_status = io_pb2.BBStatus()
    Lin_Recur_Detect.filter(tm, lr_info, bb_status)

    self.assertTrue(bb_status.halt_status.is_decided)
    self.assertFalse(bb_status.halt_status.is_halting)

    self.assertTrue(bb_status.quasihalt_status.is_decided)
    self.assertTrue(bb_status.quasihalt_status.is_quasihalting)
    self.assertEqual(Halting_Lib.get_big_int(bb_status.quasihalt_status.quasihalt_steps),
                     61)
    self.assertEqual(bb_status.quasihalt_status.quasihalt_state, 3)  # D

  def test_halt(self):
    # Test a non-trivial halting machine.
    tm = IO.parse_tm("1RB1LB_1LA0LC_1RZ1LD_1RD0RA")

    lr_info = io_pb2.LinRecurFilterInfo()
    lr_info.parameters.max_steps = 200
    lr_info.parameters.find_min_start_step = False
    bb_status = io_pb2.BBStatus()
    Lin_Recur_Detect.filter(tm, lr_info, bb_status)

    self.assertTrue(bb_status.halt_status.is_decided)
    self.assertTrue(bb_status.halt_status.is_halting)
    self.assertEqual(Halting_Lib.get_big_int(bb_status.halt_status.halt_steps),
                     107)
    # We do not currently calculate halting score in LR. But if we do in the
    # future, this will automatically test it.
    if bb_status.halt_status.HasField("halt_score"):
      self.assertEqual(Halting_Lib.get_big_int(bb_status.halt_status.halt_score),
                       13)

    self.assertTrue(bb_status.quasihalt_status.is_decided)
    self.assertFalse(bb_status.quasihalt_status.is_quasihalting)


if __name__ == "__main__":
  unittest.main()
