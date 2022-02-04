#! /usr/bin/env python
"""
Unit test for "Macro/Turing_Machine.py"
"""

from Macro import Turing_Machine

import os
import sys
import unittest

from Common import Exit_Condition
from Macro.Tape import INF
import IO


class SystemTest(unittest.TestCase):
  def setUp(self):
    # Get busy-beaver root directory.
    test_dir = os.path.dirname(sys.argv[0])
    self.root_dir = os.path.join(test_dir, os.pardir)
    self.root_dir = os.path.normpath(self.root_dir)

  def load_tm(self, name):
    filename = os.path.join(self.root_dir, "Machines", name)
    ttable = IO.load_TTable_filename(filename)
    return Turing_Machine.make_machine(ttable)

  def test_machine_ttable_to_str(self):
    self.assertEqual(Turing_Machine.machine_ttable_to_str(self.load_tm("2x2-6-4")),
                     """
Transition table:

       +-----+-----+
       |  0  |  1  |
   +---+-----+-----+
   | A | 1RB | 1LB |
   +---+-----+-----+
   | B | 1LA | 1RZ |
   +---+-----+-----+

""")
    
    # Test machine with >2 states and symbols
    self.assertEqual(Turing_Machine.machine_ttable_to_str(self.load_tm("3x3-e17")),
                     """
Transition table:

       +-----+-----+-----+
       |  0  |  1  |  2  |
   +---+-----+-----+-----+
   | A | 1RB | 2LA | 1LC |
   +---+-----+-----+-----+
   | B | 0LA | 2RB | 1LB |
   +---+-----+-----+-----+
   | C | 1RZ | 1RA | 1RC |
   +---+-----+-----+-----+

""")
    
    # Test machine with Unused transition (---)
    self.assertEqual(Turing_Machine.machine_ttable_to_str(self.load_tm("Lafitte.Papazian.complex")),
                     """
Transition table:

       +-----+-----+-----+-----+
       |  0  |  1  |  2  |  3  |
   +---+-----+-----+-----+-----+
   | A | 1RB | 2RA | 2LA | 1LA |
   +---+-----+-----+-----+-----+
   | B | 2LA | 3RB | --- | 0RA |
   +---+-----+-----+-----+-----+

""")

if __name__ == '__main__':
  unittest.main()
