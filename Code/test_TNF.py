#! /usr/bin/env python3

import TNF

import unittest

import IO


class SystemTest(unittest.TestCase):
  def test_no_halt(self):
    old_tm = IO.parse_tm("1RB 1LC  0LD 0LB  0RE 0LA  0LE 1LD  1RE 1RA")
    new_tm = TNF.to_TNF(old_tm, max_steps = 100, skip_over_steps = True)
    self.assertEqual(new_tm.ttable_str(),
                     "1RB 1LE  0LC 0LB  0LD 1LC  1RD 1RA  0RD 0LA")

  def test_multi_symbol(self):
    # Symbols 1/2 and States B/C are swapped.
    old_tm = IO.parse_tm("2RC 2LB 1LA  1RZ 2RB 2RA  0LA 2LC 1RC")
    new_tm = TNF.to_TNF(old_tm, max_steps = 100, skip_over_steps = True)
    self.assertEqual(new_tm.ttable_str(),
                     "1RB 2LA 1LC  0LA 2RB 1LB  1RZ 1RA 1RC")

  def test_undefined(self):
    old_tm = IO.parse_tm("1RC ---  --- ---  1LB ---")
    new_tm = TNF.to_TNF(old_tm, max_steps = 100, skip_over_steps = True)
    self.assertEqual(new_tm.ttable_str(),
                     "1RB ---  1LC ---  --- ---")

  def test_standardize_halt_trans(self):
    old_tm = IO.parse_tm("1RB ---  0LZ ---")
    new_tm = TNF.to_TNF(old_tm, max_steps = 100, skip_over_steps = True)
    self.assertEqual(new_tm.ttable_str(),
                     "1RB ---  1RZ ---")


if __name__ == "__main__":
  unittest.main()
