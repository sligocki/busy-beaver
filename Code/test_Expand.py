from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import Count
import Expand
from IO import TM_Record


class ExpandTest(unittest.TestCase):
  def test_parse_and_expand_line_valid(self):
    line = "1RB---_0LB1RC_1RD0LC_1RE0RC_0RF1RA_1LG1LC_0LF--- 57807763 A 1"
    children = Expand.parse_and_expand_line(line)
    # 7 states, 2 symbols: 7 * 2 * 2 = 28 running children + 1 halting child (1RZ) = 29 children
    self.assertEqual(len(children), 29)
    parent_tm = TM_Record.parse_tm("1RB---_0LB1RC_1RD0LC_1RE0RC_0RF1RA_1LG1LC_0LF---")
    self.assertEqual(
      Count.count(parent_tm, allow_no_halt=False),
      sum(Count.count(ch.tm(), allow_no_halt=False) for ch in children),
    )
    # The last child is the halting child with status set
    halt_rec = children[-1]
    self.assertTrue(halt_rec.is_halting())

  def test_parse_and_expand_line_defined_transition_raises(self):
    # Transition (A, 0) is '1RB' (defined), so expanding it must raise ValueError
    line = "1RB---_0LB1RC_1RD0LC_1RE0RC_0RF1RA_1LG1LC_0LF--- 57807763 A 0"
    with self.assertRaises(ValueError):
      Expand.parse_and_expand_line(line)

  def test_parse_and_expand_line_last_undef_transition(self):
    # Only 1 undefined transition left (G, 1), so with allow_no_halt=False -> only the 1 halting child
    line = "1RB0LA_0LB1RC_1RD0LC_1RE0RC_0RF1RA_1LG1LC_0LF--- 57807763 G 1"
    children = Expand.parse_and_expand_line(line, allow_no_halt=False)
    self.assertEqual(len(children), 1)
    self.assertEqual(
      children[0].ttable_str(),
      "1RB0LA_0LB1RC_1RD0LC_1RE0RC_0RF1RA_1LG1LC_0LF1RZ",
    )

    children_no_halt = Expand.parse_and_expand_line(line, allow_no_halt=True)
    self.assertEqual(len(children_no_halt), 29)

  def test_expand_files_and_cli(self):
    line1 = "1RB---_0LB0LC_------ 100 A 1"
    line2 = "1RB0LA_0LB---_------ 200 B 1"

    with tempfile.TemporaryDirectory() as tmpdir:
      in1 = Path(tmpdir) / "in1.txt"
      in2 = Path(tmpdir) / "in2.txt"
      out = Path(tmpdir) / "out.txt"

      in1.write_text(f"# machine steps state symbol\n{line1}\n")
      in2.write_text(f"{line2}\n")

      expand_script = str(Path(__file__).resolve().parent / "Expand.py")
      cmd = [sys.executable, expand_script, str(in1), str(in2), "-o", str(out), "--quiet"]
      res = subprocess.run(cmd, capture_output=True, text=True)
      self.assertEqual(res.returncode, 0, res.stderr)

      out_lines = [line.strip() for line in out.read_text().splitlines() if line.strip()]
      # Both have 12 running TNF children + 1 halting child = 13 children each
      self.assertEqual(len(out_lines), 26)
      self.assertIn("1RB1RZ_0LB0LC_------ Halt 100 N/A", out_lines)
      self.assertIn("1RB0LA_0LB1RZ_------ Halt 200 N/A", out_lines)


if __name__ == "__main__":
  unittest.main()
