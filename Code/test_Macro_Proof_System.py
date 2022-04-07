#! /usr/bin/env python3
#
# test_Macro_Proof_System.py
#
"""
Unit test for "Macro/Proof_System.py".
"""

from Macro import Proof_System, Turing_Machine, Tape

import Algebraic_Expression

from optparse import OptionParser
import os
import sys
import unittest

from Common import Exit_Condition
from Macro.Tape import INF
import IO


class SystemTest(unittest.TestCase):
  # Test the "apply_rule" method of "Proof_System" for the "Limited_Diff_Rule".
  #
  # This is a VERY limited test but I (TJL) needed it at figured it was a
  # start.

  def setUp(self):
    # Get busy-beaver root directory.
    test_dir = os.path.dirname(sys.argv[0])
    self.root_dir = os.path.join(test_dir, os.pardir)
    self.root_dir = os.path.normpath(self.root_dir)

    # Setup default options.
    parser = OptionParser()
    Proof_System.add_option_group(parser)
    self.options, args = parser.parse_args([])

    self.options.compute_steps = True
    self.options.verbose_prover = True
    self.options.html_format = False
    self.options.full_reps = False

  def test_apply_rule_limited_diff_rule(self):
    # To construct a "Proof_System", a TM is needed.  This will be a
    # "Simple_Machine" which needs a transition table ("2x5-e704" machine).
    ttable_filename = os.path.join(self.root_dir, "Machines/2x5-e704")
    ttable = IO.load_TTable_filename(ttable_filename)

    tm = Turing_Machine.Simple_Machine(ttable)

    proof = Proof_System.Proof_System(tm, self.options, "")

    # To call "apply_rule", a "rule" and a "start_config" are needed.

    # Build the "start_config".  It is a tuple contains a "state", "tape",
    # "step_num", and "loop_num".
    current_state = Turing_Machine.Simple_Machine_State(0)

    current_tape = Tape.Chain_Tape()
    current_tape.init(0,0,self.options)
    current_tape.tape[0] = [Tape.Repeated_Symbol(0,INF),
                            Tape.Repeated_Symbol(1,10),
                            Tape.Repeated_Symbol(2,10),
                            Tape.Repeated_Symbol(0,10),
                           ]
    current_tape.tape[1] = [Tape.Repeated_Symbol(0,INF),
                            Tape.Repeated_Symbol(2,10),
                            Tape.Repeated_Symbol(1,15),
                            Tape.Repeated_Symbol(0,15),
                           ]

    step_num = 10
    loop_num =  3

    current_config = (current_state, current_tape, step_num, loop_num)

    # Build the "Limited_Diff_Rule" which is constructed with an
    # "initial_tape", "left_dist", "right_dist", "diff_tape", "initial_state",
    # "num_steps", "num_loops", and "rule_num"
    expr_a = Algebraic_Expression.Expression_from_string("(a+3)")
    expr_b = Algebraic_Expression.Expression_from_string("(b+3)")
    expr_c = Algebraic_Expression.Expression_from_string("(c+2)")

    initial_tape = Tape.Chain_Tape()
    initial_tape.init(0,0,self.options)
    initial_tape.tape[0] = [Tape.Repeated_Symbol(0,expr_a),
                           ]
    initial_tape.tape[1] = [Tape.Repeated_Symbol(1,expr_c),
                            Tape.Repeated_Symbol(0,expr_b),
                           ]

    left_dist = 1
    right_dist = 2

    diff_tape = Tape.Chain_Tape()
    diff_tape.init(0,0,self.options)
    diff_tape.tape[0] = [Tape.Repeated_Symbol(0,-2),
                        ]
    diff_tape.tape[1] = [Tape.Repeated_Symbol(1,-1),
                         Tape.Repeated_Symbol(0,1),
                        ]

    initial_state = Turing_Machine.Simple_Machine_State(0)

    num_steps = Algebraic_Expression.Expression_from_string("(2 a + 3)")
    num_loops = 2

    rule_num = 1

    rule = Proof_System.Limited_Diff_Rule(initial_tape,left_dist,right_dist,diff_tape,initial_state,num_steps,num_loops,rule_num, states_last_seen={})

    success, (prover_result, large_delta) = proof.apply_rule(rule,current_config)

    expected_tape = Tape.Chain_Tape()
    expected_tape.init(0,0,self.options)
    expected_tape.tape[0] = [Tape.Repeated_Symbol(0,INF),
                             Tape.Repeated_Symbol(1,10),
                             Tape.Repeated_Symbol(2,10),
                             Tape.Repeated_Symbol(0, 2),
                            ]
    expected_tape.tape[1] = [Tape.Repeated_Symbol(0,INF),
                             Tape.Repeated_Symbol(2,10),
                             Tape.Repeated_Symbol(1,11),
                             Tape.Repeated_Symbol(0,19),
                            ]

    self.assertEqual(success, True)
    self.assertEqual(prover_result.condition, Proof_System.APPLY_RULE)
    self.assertEqual(prover_result.new_tape, expected_tape)
    self.assertEqual(prover_result.num_base_steps, 44)

if __name__ == '__main__':
  unittest.main()
