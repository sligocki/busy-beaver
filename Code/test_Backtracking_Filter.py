#! /usr/bin/env python3

from Backtracking_Filter import backtrack

import unittest

from IO import parse_tm

class BacktrackingTest(unittest.TestCase):
  def test_1step(self):
    result = backtrack(parse_tm("1RB---_1LB1RB"), steps=5, max_width=10)
    self.assertTrue(result.success)
    self.assertFalse(result.halted)
    self.assertEqual(result.max_steps, 1)

  def test_3step(self):
    result = backtrack(parse_tm("1RB0LA_1LA---"), steps=5, max_width=10)
    self.assertTrue(result.success)
    self.assertFalse(result.halted)
    self.assertEqual(result.max_steps, 3)

  def test_5step(self):
    result = backtrack(parse_tm("1RB1LC_1LA1RC_0RD0LA_---1LB"), steps=5, max_width=10)
    self.assertTrue(result.success)
    self.assertFalse(result.halted)
    self.assertEqual(result.max_steps, 5)

  def test_mult_halts(self):
    result = backtrack(parse_tm("1RB---_1LC---_1LD0LC_1RD0LD"), steps=5, max_width=10)
    self.assertTrue(result.success)
    self.assertFalse(result.halted)
    self.assertEqual(result.max_steps, 2)

  def test_deep(self):
    result = backtrack(parse_tm("1RB0RC_1LC1RB_0LE0RD_---1LC_1RF1LE_1LE1RG_1RA0RB"), steps=100, max_width=100)
    self.assertTrue(result.success)
    self.assertFalse(result.halted)
    self.assertEqual(result.max_steps, 66)
    self.assertEqual(result.max_width, 25)
    self.assertEqual(result.num_nodes, 517)

    result = backtrack(parse_tm("1RB0RB_1RC1LE_1RD1LA_1LB---_0LE0RA"), steps=200, max_width=10)
    self.assertTrue(result.success)
    self.assertFalse(result.halted)
    self.assertEqual(result.max_steps, 115)
    self.assertEqual(result.max_width, 9)
    self.assertEqual(result.num_nodes, 402)

  def test_no_halt_trans(self):
    result = backtrack(parse_tm("1RB1LA_1LB1RB"), steps=5, max_width=10)
    self.assertFalse(result.success)
    self.assertFalse(result.halted)

  def test_not_provable(self):
    # One of TonyG's bbchallenge backtracking bug TMs
    #   https://discuss.bbchallenge.org/t/decider-backward-reasoning/35/11
    result = backtrack(parse_tm("1RB0RE_0RC---_1LC0LD_1RE1LA_0RC1LB"), steps=100, max_width=100)
    self.assertFalse(result.success)
    self.assertFalse(result.halted)

    # Nick Drozd's false positive
    result = backtrack(parse_tm("1RB2LA0RC_2LA---1RC_1LA0LB2RC"), steps=100, max_width=100)
    self.assertFalse(result.success)
    self.assertFalse(result.halted)

  def test_halt_trivial(self):
    result = backtrack(parse_tm("1RZ1RZ"), steps=5, max_width=10)
    self.assertFalse(result.success)
    self.assertTrue(result.halted)

  def test_halt_bb2(self):
    # BB(2) champion
    result = backtrack(parse_tm("1RB1LB_1LA1RZ"), steps=10, max_width=100)
    self.assertFalse(result.success)
    self.assertTrue(result.halted)

  def test_halt_bb3(self):
    # BB(3) champion
    result = backtrack(parse_tm("1RB1RZ_1LB0RC_1LC1LA"), steps=100, max_width=100)
    self.assertFalse(result.success)
    self.assertTrue(result.halted)

  def test_halt_bb4(self):
    # BB(4) champion
    result = backtrack(parse_tm("1RB1LB_1LA0LC_1RZ1LD_1RD0RA"), steps=1000, max_width=100)
    print(result)
    self.assertFalse(result.success)
    # We cannot go deep enough to prove halting b/c tree grows too big.
    # self.assertTrue(result.halted)

if __name__ == "__main__":
  unittest.main()
