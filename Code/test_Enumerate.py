#! /usr/bin/env python3
#
# test_Enumerate.py
#
"""
Unit test for "Enumerate.py".
"""

import Enumerate

import os
import subprocess
import sys
import unittest


regold = False

class GoldTest(unittest.TestCase):
  # Test that Enumerator produces consistent results.
  # Note
  def setUp(self):
    # Get busy-beaver root directory.
    test_dir = os.path.dirname(sys.argv[0])
    self.root_dir = os.path.join(test_dir, os.pardir)
    self.root_dir = os.path.normpath(self.root_dir)

  def test_goldfiles(self):
    # Clear out test directory to start fresh.
    test_dir = "/tmp/test_Enumerate/"
    subprocess.call(["rm", "-rf", test_dir])
    os.makedirs(test_dir)
    for states, symbols in [(2, 2), (2, 3), (3, 2)]:
      outfile_pb = os.path.join(test_dir, "out.pb")
      outfile_txt = os.path.join(test_dir, "out.txt")
      goldfile = os.path.join(
          self.root_dir, "Testdata/Enum.%d.%d.out.gold" % (states, symbols))
      Enumerate.main(["--states=%d" % states,
                      "--symbols=%d" % symbols,
                      "--outfile=%s" % outfile_pb,
                      # Makes tests deterministic
                      "--max-loops=10_000",
                      "--time=0",
                      "--force",
                      ])
      # For now, use old style text so that we have extra info.
      subprocess.call(["python3", "IO_Convert.py", outfile_pb, outfile_txt,
                       "--outformat=text_old"])
      if regold:
        subprocess.call(["mv", outfile_txt, goldfile])
      else:
        proc = subprocess.run(["diff", goldfile, outfile_txt])
        self.assertEqual(0, proc.returncode)
    # Clean up after ourselves.
    subprocess.call(["rm", "-rf", test_dir])


if __name__ == "__main__":
  if "--regold" in sys.argv:
    regold = True
    sys.argv.remove("--regold")
  unittest.main()
