#! /usr/bin/env python3
#
# test_Enumerate.py
#
"""
Unit test for "Enumerate.py".
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import Enumerate
import IO
import Macro_Simulator
import TM_Enum
import Work_Queue
from IO.TM_Record import TM_Record

regold = False


class GoldTest(unittest.TestCase):
  # Test that Enumerator produces consistent results.
  # Note
  def setUp(self):
    # Get busy-beaver root directory.
    test_dir = os.path.dirname(__file__)
    self.root_dir = os.path.join(test_dir, os.pardir)
    self.root_dir = os.path.normpath(self.root_dir)

  def test_goldfiles(self):
    # Clear out test directory to start fresh.
    test_dir = tempfile.mkdtemp()
    test_dir_source = os.path.dirname(__file__)
    for states, symbols in [(2, 2), (2, 3), (3, 2)]:
      outfile_pb = os.path.join(test_dir, "out.pb")
      outfile_txt = os.path.join(test_dir, "out.txt")
      goldfile = os.path.join(self.root_dir, "Testdata/Enum.%d.%d.out.gold" % (states, symbols))
      Enumerate.main(
        [
          "--states=%d" % states,
          "--symbols=%d" % symbols,
          "--outfile=%s" % outfile_pb,
          # Makes tests deterministic
          "--max-loops=10_000",
          "--time=0",
          "--force",
        ]
      )
      # For now, use old style text so that we have extra info.
      subprocess.call(
        [
          "python3",
          os.path.join(test_dir_source, "IO_Convert.py"),
          outfile_pb,
          outfile_txt,
          "--outformat=text_old",
        ]
      )
      if regold:
        subprocess.call(["mv", outfile_txt, goldfile])
      else:
        proc = subprocess.run(["diff", goldfile, outfile_txt])
        self.assertEqual(0, proc.returncode)
    # Clean up after ourselves.
    shutil.rmtree(test_dir)

  def test_exception_clears_status_and_preserves_ttable(self):
    ttable = "1RB1RG_1LC0LF_0RE1LD_0LB1LC_1RE1RA_0LE0LB_1RZ1LF"
    tm_record = TM_Record(tm_enum=TM_Enum.TM_Enum(IO.parse_tm(ttable), allow_no_halt=False))
    options = Enumerate.get_options_parser().parse_args(
      ["--states=7", "--symbols=2", "--outfile=/dev/null", "--force"]
    )[0]
    enumerator = Enumerate.Enumerator(
      options,
      writer=mock.MagicMock(),
      stack=mock.MagicMock(spec=Work_Queue.Work_Queue),
      pout=None,
    )

    def failing_run(record, _options, _time_limit):
      record.proto.status.halt_status.is_decided = True
      record.proto.status.halt_status.is_halting = True
      raise RuntimeError("boom")

    with mock.patch.object(Macro_Simulator, "run_options", side_effect=failing_run):
      enumerator.run(tm_record)

    self.assertTrue(tm_record.proto.filter.simulator.result.unknown_info.threw_exception)
    self.assertFalse(tm_record.proto.status.halt_status.is_decided)
    self.assertFalse(tm_record.proto.status.halt_status.is_halting)

    enumerator.add_result(tm_record)
    self.assertEqual(enumerator.num_unknown, 1)
    self.assertEqual(enumerator.num_halt, 0)
    self.assertEqual(tm_record.ttable_str(), ttable)


if __name__ == "__main__":
  if "--regold" in sys.argv:
    regold = True
    sys.argv.remove("--regold")
  unittest.main()
