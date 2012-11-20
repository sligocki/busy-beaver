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

  def test_2x2(self):
    self.assertEqual(self.read("Backtracking.2x2.gold"), self.backtrack("2x2"))

  def test_2x3(self):
    self.assertEqual(self.read("Backtracking.2x3.gold"), self.backtrack("2x3"))

  def test_2x4(self):
    self.assertEqual(self.read("Backtracking.2x4.gold"),
                     self.backtrack("2x4.sample"))

  def test_3x2(self):
    self.assertEqual(self.read("Backtracking.3x2.gold"), self.backtrack("3x2"))

  def test_4x2(self):
    self.assertEqual(self.read("Backtracking.4x2.gold"),
                     self.backtrack("4x2.sample"))

if __name__ == "__main__":
  unittest.main()
