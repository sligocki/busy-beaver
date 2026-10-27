from pathlib import Path
import subprocess
import tempfile
import unittest

import Diff
from IO import TM_Record
import TM_Enum


class DiffTest(unittest.TestCase):
  def test_identical_sets(self):
    set_a = {"1RB---_0LB0LC_------", "1RB0RA_0LB0LC_------"}
    set_b = {"1RB---_0LB0LC_------", "1RB0RA_0LB0LC_------"}
    diff_a, diff_b = Diff.diff_sets(set_a, set_b)
    self.assertEqual(diff_a, set())
    self.assertEqual(diff_b, set())

  def test_single_level_expansion(self):
    # 3-state TM with undefined transition at (0, 1) [A1]
    parent = "1RB---_0LB0LC_------"
    tm = TM_Record.parse_tm(parent)
    tme = TM_Enum.TM_Enum(tm, allow_no_halt=False)
    children = {ch.tm.ttable_str() for ch in tme.enum_children(0, 1)}
    self.assertEqual(len(children), 12)

    # Set A has the parent, Set B has all 12 children
    diff_a, diff_b = Diff.diff_sets({parent}, children)
    self.assertEqual(diff_a, set())
    self.assertEqual(diff_b, set())

    # Symmetric: Set A has children, Set B has parent
    diff_a, diff_b = Diff.diff_sets(children, {parent})
    self.assertEqual(diff_a, set())
    self.assertEqual(diff_b, set())

  def test_partial_expansion(self):
    parent = "1RB---_0LB0LC_------"
    tm = TM_Record.parse_tm(parent)
    tme = TM_Enum.TM_Enum(tm, allow_no_halt=False)
    children = sorted(list({ch.tm.ttable_str() for ch in tme.enum_children(0, 1)}))
    self.assertEqual(len(children), 12)

    # Remove 1 child from set B
    missing_child = children[0]
    set_b = set(children[1:])

    diff_a, diff_b = Diff.diff_sets({parent}, set_b)
    self.assertEqual(diff_a, {missing_child})
    self.assertEqual(diff_b, set())

  def test_disjoint_tms(self):
    tm_a = "1RB0LA_0LB0LC_------"
    tm_b = "1RB0RA_0LB0LC_------"
    diff_a, diff_b = Diff.diff_sets({tm_a}, {tm_b})
    self.assertEqual(diff_a, {tm_a})
    self.assertEqual(diff_b, {tm_b})

  def test_cli_integration(self):
    parent = "1RB---_0LB0LC_------"
    tm = TM_Record.parse_tm(parent)
    tme = TM_Enum.TM_Enum(tm, allow_no_halt=False)
    children = [ch.tm.ttable_str() for ch in tme.enum_children(0, 1)]

    with tempfile.TemporaryDirectory() as tmpdir:
      file_a = Path(tmpdir) / "parent.txt"
      file_b = Path(tmpdir) / "children.txt"
      file_c = Path(tmpdir) / "partial.txt"

      with open(file_a, "w") as f:
        f.write(f"{parent}\n")

      with open(file_b, "w") as f:
        for ch in children:
          f.write(f"{ch}\n")

      with open(file_c, "w") as f:
        for ch in children[1:]:
          f.write(f"{ch}\n")

      # file_a vs file_b should be identical modulo expansion (exit code 0)
      cmd_match = ["./Code/Count.py", str(file_a), "--diff", str(file_b), "--quiet"]
      res = subprocess.run(cmd_match, capture_output=True, text=True)
      self.assertEqual(res.returncode, 0)
      self.assertIn("In A but not B: 0", res.stdout)
      self.assertIn("In B but not A: 0", res.stdout)

      # file_a vs file_c has 1 difference (exit code 1)
      cmd_diff = ["./Code/Count.py", str(file_a), "--diff", str(file_c), "--quiet"]
      res = subprocess.run(cmd_diff, capture_output=True, text=True)
      self.assertEqual(res.returncode, 1)
      self.assertIn("In A but not B: 1", res.stdout)
      self.assertIn("In B but not A: 0", res.stdout)


if __name__ == "__main__":
  unittest.main()
