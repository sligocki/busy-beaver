#! /usr/bin/env python
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
      outfile = os.path.join(test_dir, "Enum.%d.%d.out" % (states, symbols))
      goldfile = os.path.join(
          self.root_dir, "Testdata/Enum.%d.%d.out.gold" % (states, symbols))
      Enumerate.main(["--states=%d" % states,
                      "--symbols=%d" % symbols,
                      "--outfile=%s" % outfile,
                      "--max-loops=1000",  # Makes tests deterministic.
                      ])
      if regold:
        subprocess.call(["mv", outfile, goldfile])
      else:
        retvalue = subprocess.call(["diff", outfile, goldfile])
        self.assertEqual(0, retvalue)
    # Clean up after ourselves.
    subprocess.call(["rm", "-rf", test_dir])


if __name__ == "__main__":
  if "--regold" in sys.argv:
    regold = True
    sys.argv.remove("--regold")
  unittest.main()
