#! /usr/bin/env python
#
# test_Backtracking_Filter.py
#
"""
Unit test for "Backtracking_Filter.py"
"""

import Backtracking_Filter

import os.path
import sys
import tempfile
import unittest

class SystemTest(unittest.TestCase):
  def setUp(self):
    # Get busy-beaver root direcory.
    test_dir = os.path.dirname(sys.argv[0])
    self.testdata_dir = os.path.join(test_dir, os.pardir, "Testdata")

  def read(self, filename):
    return open(os.path.join(self.testdata_dir, filename), "r").read()

  def backtrack(self, filename):
    filename = os.path.join(self.testdata_dir, filename)
    outfile = tempfile.NamedTemporaryFile()
    Backtracking_Filter.main([sys.argv[0],
                              "--infile=%s" % filename,
                              "--outfile=%s" % outfile.name,
                              "--force",
                              "--backsteps=10"])
    return self.read(outfile.name)

  def test_foo(self):
    self.assertEqual(self.read("Backtracking.2x2.gold"), self.backtrack("2x2"))

if __name__ == "__main__":
  unittest.main()
