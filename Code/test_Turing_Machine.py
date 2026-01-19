#! /usr/bin/env python3
"""
Unit test for "Macro/Turing_Machine.py"
"""

from Macro import Turing_Machine

import os
import sys
import unittest
import globals

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
    return IO.load_tm(filename, 0)

  def test_block_repeat(self):
    """Test that Block_Macro_Machine can detect repeats efficiently even for giant block sizes."""
    tm = IO.parse_tm("0RA1LA")
    block_size = 100
    macro_machine = Turing_Machine.Block_Macro_Machine(tm, block_size)
    macro_symbol = Turing_Machine.Block_Symbol((0, 1) + (0,) * (block_size - 2))

    trans = macro_machine.get_trans_object(macro_symbol,
                                           macro_machine.init_state,
                                           Turing_Machine.RIGHT)

    self.assertEqual(trans.condition, Turing_Machine.INF_REPEAT)

  def test_backsymbol_repeat(self):
    """Test that Backsymbol_Macro_Machine can detect repeats efficiently even for giant block sizes."""
    tm = IO.parse_tm("0RA1LA")
    block_size = 100
    block_m = Turing_Machine.Block_Macro_Machine(tm, block_size)
    macro_machine = Turing_Machine.Backsymbol_Macro_Machine(block_m)

    back_symbol = Turing_Machine.Block_Symbol((0,) * block_size)
    front_symbol = Turing_Machine.Block_Symbol((1,) * block_size)
    state = Turing_Machine.Backsymbol_Macro_Machine_State(tm.init_state,
                                                          back_symbol)

    trans = macro_machine.get_trans_object(front_symbol, state, Turing_Machine.RIGHT)

    self.assertEqual(trans.condition, Turing_Machine.INF_REPEAT)

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
  globals.init()
  unittest.main()
