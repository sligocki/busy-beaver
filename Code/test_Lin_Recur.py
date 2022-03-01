#! /usr/bin/env python3

import Lin_Recur_Detect

import unittest

import IO


class SystemTest(unittest.TestCase):
  def test_simple(self):
    ttable = IO.parse_ttable("1RB 1LA  0LA 1RA")
    lr_result, quasihalt_info = Lin_Recur_Detect.lin_detect(
      ttable, max_steps=100, find_min_start_step=True)
    self.assertEqual(lr_result.max_steps, 100)
    self.assertTrue(lr_result.is_start_step_min)
    self.assertTrue(lr_result.success)
    self.assertEqual(lr_result.start_step, 7)
    self.assertEqual(lr_result.period, 5)
    self.assertEqual(lr_result.offset, -1)

    self.assertFalse(quasihalt_info.quasihalts)

  def test_in_place(self):
    ttable = IO.parse_ttable("1RB ---  0LB 1RB")
    lr_result, quasihalt_info = Lin_Recur_Detect.lin_detect(
      ttable, max_steps=100, find_min_start_step=True)
    self.assertEqual(lr_result.max_steps, 100)
    self.assertTrue(lr_result.is_start_step_min)
    self.assertTrue(lr_result.success)
    self.assertEqual(lr_result.start_step, 1)
    self.assertEqual(lr_result.period, 2)
    self.assertEqual(lr_result.offset, 0)

    self.assertTrue(quasihalt_info.quasihalts)
    self.assertEqual(quasihalt_info.quasihalt_steps, 1)
    self.assertEqual(quasihalt_info.quasihalt_state, 0)  # A

  def test_complex(self):
    # Super-long period and recurrence start. One of Boyd's machines.
    ttable = IO.parse_ttable("1RB 0RA  1RC 0RB  1LD 1LC  1RA 0LC")
    lr_result, quasihalt_info = Lin_Recur_Detect.lin_detect(
      ttable, max_steps=1_000_000, find_min_start_step=True)
    self.assertEqual(lr_result.max_steps, 1_000_000)
    self.assertTrue(lr_result.is_start_step_min)
    self.assertTrue(lr_result.success)
    self.assertEqual(lr_result.start_step, 7_170)
    self.assertEqual(lr_result.period,    29_117)
    self.assertEqual(lr_result.offset,      +525)

    self.assertFalse(quasihalt_info.quasihalts)

  def test_complex_no_min_start(self):
    # Make sure that find_min_start_step=False is still finding all correct
    # values (except for start_step which might be big).
    ttable = IO.parse_ttable("1RB 0RA  1RC 0RB  1LD 1LC  1RA 0LC")
    lr_result, quasihalt_info = Lin_Recur_Detect.lin_detect(
      ttable, max_steps=1_000_000, find_min_start_step=False)
    # Updates vs. test_complex()
    self.assertFalse(lr_result.is_start_step_min)
    self.assertGreaterEqual(lr_result.start_step, 7_170)

    # Same as expected via test_complex()
    self.assertEqual(lr_result.max_steps, 1_000_000)
    self.assertTrue(lr_result.success)
    self.assertEqual(lr_result.period,    29_117)
    self.assertEqual(lr_result.offset,      +525)

    self.assertFalse(quasihalt_info.quasihalts)

  def test_quasihalt(self):
    # Test a non-trivial quasihalting machine.
    ttable = IO.parse_ttable("1RB 1LC  1RC 0RC  0LD 0LA  0RA 0LA")
    _, quasihalt_info = Lin_Recur_Detect.lin_detect(
      ttable, max_steps=100, find_min_start_step=False)
    self.assertTrue(quasihalt_info.quasihalts)
    self.assertEqual(quasihalt_info.quasihalt_steps, 61)
    self.assertEqual(quasihalt_info.quasihalt_state, 3)  # D


if __name__ == "__main__":
  unittest.main()
