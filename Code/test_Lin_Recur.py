#! /usr/bin/env python

import Lin_Recur_Detect

import unittest

import IO


class SystemTest(unittest.TestCase):
  def test_simple(self):
    ttable = IO.parse_ttable("1RB 1LA  0LA 1RA")
    result = Lin_Recur_Detect.lin_search(ttable, max_steps=100)
    self.assertTrue(result.success)
    self.assertEqual(result.period, 5)
    self.assertEqual(result.offset, -1)
    self.assertEqual(result.states_used, {0, 1})

    recur_start = Lin_Recur_Detect.period_search(ttable,
                                                 result.init_step, result.period)
    self.assertEqual(recur_start, 7)
    
  def test_in_place(self):
    ttable = IO.parse_ttable("1RB ---  0LB 1RB")
    result = Lin_Recur_Detect.lin_search(ttable, max_steps=100)
    self.assertTrue(result.success)
    self.assertEqual(result.period, 2)
    self.assertEqual(result.offset, 0)
    self.assertEqual(result.states_used, {1})

    recur_start = Lin_Recur_Detect.period_search(ttable,
                                                 result.init_step, result.period)
    self.assertEqual(recur_start, 1)

  def test_complex(self):
    # Super-long period and recurrence start. One of Boyd's machines.
    ttable = IO.parse_ttable("1RB 0RA  1RC 0RB  1LD 1LC  1RA 0LC")
    result = Lin_Recur_Detect.lin_search(ttable, max_steps=1000000)
    self.assertTrue(result.success)
    self.assertEqual(result.period, 29117)
    self.assertEqual(result.offset, +525)
    self.assertEqual(result.states_used, {0, 1, 2, 3})

    recur_start = Lin_Recur_Detect.period_search(ttable,
                                                 result.init_step, result.period)
    self.assertEqual(recur_start, 7170)


if __name__ == "__main__":
  unittest.main()
