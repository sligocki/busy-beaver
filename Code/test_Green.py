#!/usr/bin/env python3
"""Unit tests for Green Turing Machine generator."""

import glob
import os
import unittest

from Direct_Simulator import DirectSimulator
from Green import green_machine, green_machine_str


class TestGreen(unittest.TestCase):
  def setUp(self):
    test_dir = os.path.dirname(__file__)
    self.root_dir = os.path.normpath(os.path.join(test_dir, os.pardir))

  def test_10x2_green_explicit(self):
    expected = "1LB1RZ_0LC1LC_0LD0LC_1LE1RA_0LF0LE_1LG1RD_0LH0LG_1LI1RF_0LJ0LI_1RJ1RH"
    self.assertEqual(green_machine_str(10), expected)
    self.assertEqual(green_machine(10).ttable_str(), expected)

  def test_match_saved_machines(self):
    machine_files = glob.glob(os.path.join(self.root_dir, "Machines", "*x2-Green"))
    self.assertGreater(len(machine_files), 0)

    for filepath in machine_files:
      basename = os.path.basename(filepath)
      num_states = int(basename.split("x")[0])

      with open(filepath, "r") as f:
        expected_str = f.read().strip()

      actual_str = green_machine_str(num_states)
      self.assertEqual(actual_str, expected_str, f"Mismatch for {basename}")

      tm = green_machine(num_states)
      self.assertEqual(tm.ttable_str(), expected_str, f"Mismatch for {basename} Simple_Machine")

  def test_sim_6x2(self):
    tm = green_machine(6)
    sim = DirectSimulator(tm)
    sim.seek(1000)
    self.assertTrue(sim.halted)
    self.assertEqual(sim.step_num, 436)
    self.assertEqual(sim.tape.count_nonzero(), 35)

  def test_invalid_num_states(self):
    for n in (0, 1, 2, 3, 4, 5):
      with self.assertRaises(ValueError):
        green_machine_str(n)
      with self.assertRaises(ValueError):
        green_machine(n)

  def test_large_states(self):
    # Verify bijective base-26 naming past 26 states works without error
    s26 = green_machine_str(26)
    self.assertIn("ZZ", s26)  # halt state
    tm26 = green_machine(26)
    self.assertEqual(tm26.num_states, 26)

    s27 = green_machine_str(27)
    tm27 = green_machine(27)
    self.assertEqual(tm27.num_states, 27)
    self.assertEqual(tm27.ttable_str(), s27)


if __name__ == "__main__":
  unittest.main()
