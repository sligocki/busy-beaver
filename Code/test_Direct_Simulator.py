#! /usr/bin/env python3

import Direct_Simulator

import unittest

import IO


class SystemTest(unittest.TestCase):
  def test_simple(self):
    tm = IO.parse_tm("1RB1LA_0LA1RA")
    sim = Direct_Simulator.DirectSimulator(tm)
    sim.seek(100)
    self.assertFalse(sim.halted)
    self.assertEqual(sim.state, 0)
    self.assertEqual(sim.tape.read(), 0)
    self.assertEqual(list(sim.tape.tape), [0] + [1]*21 + [0])

  def test_halt(self):
    # BB4 champion
    tm = IO.parse_tm("1RB1LB_1LA0LC_1RZ1LD_1RD0RA")
    sim = Direct_Simulator.DirectSimulator(tm)
    sim.seek(1000)
    self.assertTrue(sim.halted)
    self.assertEqual(sim.step_num, 107)
    self.assertEqual(sim.tape.read(), 0)
    self.assertEqual(list(sim.tape.tape), [1, 0] + [1]*12)

  def test_example(self):
    # This is testing a speicific TM that was broken by a change I was working on.
    tm = IO.parse_tm("1RB3LA1RB2LA1RA_1LB2LA3RA4RB---")
    sim = Direct_Simulator.DirectSimulator(tm)
    sim.seek(1000)
    self.assertFalse(sim.halted)
    self.assertEqual(sim.state, 0)
    self.assertEqual(sim.tape.read(), 2)
    self.assertEqual(list(sim.tape.tape), [1, 4, 1, 2, 2, 2, 3, 3, 2, 3, 2, 3, 3, 3] + [2]*9 + [3, 3, 2, 3, 2, 2, 3, 3, 3, 2, 3, 3, 3, 2, 2, 3, 3, 3, 2, 3])

  # TODO: Add some better tests that aren't just "golden" tests.


if __name__ == "__main__":
  unittest.main()
