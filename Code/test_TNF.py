#! /usr/bin/env python3

import TNF

import unittest

import IO


class SystemTest(unittest.TestCase):
  def test_no_halt(self):
    old_tm = IO.parse_tm("1RB1LC_0LD0LB_0RE0LA_0LE1LD_1RE1RA")
    new_tm = TNF.to_TNF(old_tm, skip_zeros=False, max_steps = 100)
    self.assertEqual(new_tm.ttable_str(),
                     "1RB1LE_0LC0LB_0LD1LC_1RD1RA_0RD0LA")

  def test_multi_symbol(self):
    # Symbols 1/2 and States B/C are swapped.
    old_tm = IO.parse_tm("2RC2LB1LA_1RZ2RB2RA_0LA2LC1RC")
    new_tm = TNF.to_TNF(old_tm, skip_zeros=False, max_steps = 100)
    self.assertEqual(new_tm.ttable_str(),
                     "1RB2LA1LC_0LA2RB1LB_1RZ1RA1RC")

  def test_undefined(self):
    old_tm = IO.parse_tm("1RC---_------_1LB---")
    new_tm = TNF.to_TNF(old_tm, skip_zeros=False, max_steps = 100)
    self.assertEqual(new_tm.ttable_str(),
                     "1RB---_1LC---_------")

  def test_standardize_halt_trans(self):
    old_tm = IO.parse_tm("1RB---_0LZ---")
    new_tm = TNF.to_TNF(old_tm, skip_zeros=False, max_steps = 100)
    self.assertEqual(new_tm.ttable_str(),
                     "1RB---_1RZ---")

  def test_skip_zeros(self):
    # BB(3,3) champion which runs 1 step longer than 1RB version.
    old_tm = IO.parse_tm("0RB2LA1RA_1LA2RB1RC_1RZ1LB1LC")
    new_tm = TNF.to_TNF(old_tm, skip_zeros=True, max_steps = 100)
    self.assertEqual(new_tm.ttable_str(),
                     "1RB2LA1LC_0LA2RB1LB_1RZ1RA1RC")

  def test_no_skip_zeros(self):
    old_tm = IO.parse_tm("0RB2LA1RA_1LA2RB1RC_1RZ1LB1LC")
    new_tm = TNF.to_TNF(old_tm, skip_zeros=False, max_steps = 100)
    self.assertEqual(new_tm.ttable_str(),
                     "0RB2LA1RA_1LA2RB1RC_1RZ1LB1LC")


if __name__ == "__main__":
  unittest.main()
