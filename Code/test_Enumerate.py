#! /usr/bin/env python

import Enumerate

import subprocess
import unittest


class GoldTest(unittest.TestCase):
  # Test that Enumerator produces consistent results.
  # Note
  def setUp(self):
    pass

  def test_goldfiles(self):
    for states, symbols in [(2, 2), (2, 3), (3, 2)]:
      # TODO(shawn): Put this in a dir so we can just rm -rf it.
      outfile = "/tmp/Enum.%d.%d.out" % (states, symbols)
      # TODO(shawn): Make these path agnostic.
      goldfile = "Testdata/Enum.%d.%d.out.gold" % (states, symbols)
      Enumerate.main(["--states=%d" % states,
                      "--symbols=%d" % symbols,
                      "--outfile=%s" % outfile,
                      "--steps=10000",  # Makes tests deterministic.
                      ])
      retvalue = subprocess.call(["diff", outfile, goldfile])
      self.assertEqual(0, retvalue)
      # TODO(shawn): Clean up after ourselves
      


if __name__ == "__main__":
  unittest.main()
