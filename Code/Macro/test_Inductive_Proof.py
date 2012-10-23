#! /usr/bin/env python
"""
Unit test for "Inductive_Proof.py"
"""

import Inductive_Proof

from optparse import OptionParser
import sys
import unittest

import Macro_Simulator
import Proof_System
import Tape
import Turing_Machine

parent_dir = sys.path[0][:sys.path[0].rfind("/")] # pwd path with last directory removed
sys.path.insert(1, parent_dir)
import IO
from Numbers import Algebraic_Expression

class InductiveProofTest(unittest.TestCase):
  """Test that some manually discovered rules work."""

  def setUp(self):
    # Setup default options.
    parser = OptionParser()
    Macro_Simulator.add_option_group(parser)
    self.options, args = parser.parse_args([])

  def test_June_2_2011(self):
    ttable = IO.parse_ttable("1RB 0RB  1LC 1RB  --- 0LD  1RA 1LD")
    machine = Turing_Machine.Simple_Machine(ttable)

    # Construct rule
    a = Algebraic_Expression.Variable()
    a_expr = Algebraic_Expression.VariableToExpression(a)
    b = Algebraic_Expression.Variable()
    b_expr = Algebraic_Expression.VariableToExpression(b)
    c = Algebraic_Expression.Variable()
    c_expr = Algebraic_Expression.VariableToExpression(c)
    var_list = [a, b, c]
    min_list = [1, 3, 1]
    result_tape = Tape.Chain_Tape()
    result_tape.init(machine.init_symbol, machine.init_dir)
    result_tape.tape[0] = []
    result_tape.tape[1] = []
    result_tape.tape[0].append(Tape.Repeated_Symbol(0, a_expr - 1))
    result_tape.tape[0].append(Tape.Repeated_Symbol(1, b_expr + 2))
    result_tape.tape[1].append(Tape.Repeated_Symbol(0, c_expr - 1))
    rule = Proof_System.General_Rule(var_list, min_list, result_tape,
                                     None, None, None)

    self.assertEqual(True, Inductive_Proof.Inductive_Proof(
        machine, self.options, rule))


if __name__ == "__main__":
  unittest.main()
