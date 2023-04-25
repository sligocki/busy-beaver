#! /usr/bin/env python3
"""
Unit test for "Macro/Proof_System.py".
"""

from Macro import Proof_System

import math
from optparse import OptionParser
import os
import sys
import unittest

import Algebraic_Expression
import IO

from Macro import Tape
from Macro import Turing_Machine


def factor_expr(expr, var):
  """Helper method to simplify tests for factor_var()."""
  assert len(expr.terms) == 1, expr
  assert expr.const == 0, expr
  return Proof_System.factor_var(expr.terms[0], var)

class ProofSystemTest(unittest.TestCase):
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
    self.options.verbose_prover = False
    self.options.html_format = False
    self.options.full_reps = False

  def test_factor_var(self):
    k = Algebraic_Expression.Expression_from_string("k")
    k_var = k.variable()

    self.assertEqual(factor_expr(k, k_var), (1, 1))
    self.assertEqual(factor_expr(13 * k, k_var), (1, 13))
    self.assertEqual(factor_expr(k**2, k_var), (2, 1))
    self.assertEqual(factor_expr(-2 * k**2, k_var), (2, -2))
    self.assertEqual(factor_expr(81 * k**13, k_var), (13, 81))

    n = Algebraic_Expression.Expression_from_string("n")
    self.assertEqual(factor_expr(n, k_var), (0, n))
    self.assertEqual(factor_expr(13 * n, k_var), (0, 13 * n))
    self.assertEqual(factor_expr(-3 * n * k, k_var), (1, -3 * n))
    self.assertEqual(factor_expr(138 * k * n * k, k_var), (2, 138 * n))

  def test_series_sum(self):
    k = Algebraic_Expression.Expression_from_string("k")
    k_var = k.variable()

    # Constant
    self.assertEqual(Proof_System.series_sum(13, k_var, 10), 130)

    # Linear
    self.assertEqual(Proof_System.series_sum(k + 1, k_var, 10), 10 * 9 / 2 + 10)
    self.assertEqual(Proof_System.series_sum(2 * k + 3, k_var, 10), 10 * 9 + 30)

    # Quadratic
    self.assertEqual(Proof_System.series_sum(k**2 + 1, k_var, 10), 10 * 9 * 19 / 6 + 10)
    self.assertEqual(Proof_System.series_sum(5 * k**2 - 2 * k + 13, k_var, 10),
                     5 * 10 * 9 * 19 / 6 - 10 * 9 + 130)

    # With other variables
    n = Algebraic_Expression.Expression_from_string("n")
    self.assertEqual(Proof_System.series_sum(k * n, k_var, 10),
                     n * 10 * 9 / 2)
    self.assertEqual(Proof_System.series_sum(3 * k * n + 5 * k + 7 * n + 13, k_var, 10),
                     (3 * n + 5) * 10 * 9 / 2 + (7 * n + 13) * 10)


  def test_bug_limited_diff_rule(self):
    # See: https://github.com/sligocki/busy-beaver/issues/2
    tm = IO.parse_tm("1RB3RB3LB0RB0LA_2LB3RA3RB4RA2LA")
    self.options.recursive = True
    self.options.limited_rules = True
    prover = Proof_System.Proof_System(tm, self.options, "")

    # Rule should be:
    #   34 A> 2 -> 034 A>   or   0^m 3^1 4^1 A> 2^n+1 -> 0^m+1 3^1 4^1 A> 2^n
    # but the bug led to a rule:
    #   3^1 4^1 A> 2^b+2 -> 3^1 4^1 A> 2^b+1
    # which is clearly wrong since it is deleting a 2 without adding anything in exchange.
    tape = Tape.Chain_Tape()
    tape.init(0, 0, self.options)
    tape.dir = Turing_Machine.RIGHT
    tape.tape[0] = [
      Tape.Repeated_Symbol(0,math.inf),
      Tape.Repeated_Symbol(3, 1),
      Tape.Repeated_Symbol(4, 1),
    ]
    tape.tape[1] = [
      Tape.Repeated_Symbol(0,math.inf),
      Tape.Repeated_Symbol(2, 10),
    ]

    state_A = Turing_Machine.Simple_Machine_State(0)
    full_config = (state_A, tape, None, None)
    stripped_config = Proof_System.strip_config(
      state_A, Turing_Machine.RIGHT, tape.tape)

    rule = prover.prove_rule(stripped_config, full_config, delta_loop = 5)
    self.assertIsNotNone(rule)
    prover.add_rule(rule, stripped_config)
    self.assertGreaterEqual(len(prover.rules), 1)

    # Try to apply the rule to a situation it certainly should not apply in.
    bad_tape = Tape.Chain_Tape()
    bad_tape.init(0, 0, self.options)
    bad_tape.dir = Turing_Machine.RIGHT
    bad_tape.tape[0] = [
      Tape.Repeated_Symbol(0,math.inf),
      Tape.Repeated_Symbol(1, 10),  # Note: This 1 is the key to the bug.
      Tape.Repeated_Symbol(3, 1),
      Tape.Repeated_Symbol(4, 1),
    ]
    bad_tape.tape[1] = [
      Tape.Repeated_Symbol(0,math.inf),
      Tape.Repeated_Symbol(2, 10),
    ]
    bad_full_config = (state_A, bad_tape, None, None)
    bad_stripped_config = Proof_System.strip_config(
      state_A, Turing_Machine.RIGHT, bad_tape.tape)

    result = prover.try_apply_a_limited_rule(bad_stripped_config, bad_full_config)
    self.assertIsNone(result)


  def test_apply_rule_limited_diff_rule(self):
    tm_filename = os.path.join(self.root_dir, "Machines/2x5-e704")
    tm = IO.load_tm(tm_filename, 0)

    proof = Proof_System.Proof_System(tm, self.options, "")

    # To call "apply_rule", a "rule" and a "start_config" are needed.

    # Build the "start_config".  It is a tuple contains a "state", "tape",
    # "step_num", and "loop_num".
    current_state = Turing_Machine.Simple_Machine_State(0)

    current_tape = Tape.Chain_Tape()
    current_tape.init(0,0,self.options)
    current_tape.tape[0] = [Tape.Repeated_Symbol(0,math.inf),
                            Tape.Repeated_Symbol(1,10),
                            Tape.Repeated_Symbol(2,10),
                            Tape.Repeated_Symbol(0,10),
                           ]
    current_tape.tape[1] = [Tape.Repeated_Symbol(0,math.inf),
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
    expected_tape.tape[0] = [Tape.Repeated_Symbol(0,math.inf),
                             Tape.Repeated_Symbol(1,10),
                             Tape.Repeated_Symbol(2,10),
                             Tape.Repeated_Symbol(0, 2),
                            ]
    expected_tape.tape[1] = [Tape.Repeated_Symbol(0,math.inf),
                             Tape.Repeated_Symbol(2,10),
                             Tape.Repeated_Symbol(1,11),
                             Tape.Repeated_Symbol(0,19),
                            ]

    self.assertEqual(success, True)
    self.assertEqual(prover_result.condition, Proof_System.APPLY_RULE)
    self.assertEqual(prover_result.new_tape, expected_tape)
    self.assertEqual(prover_result.num_base_steps, 44)


  def test_complex_meta(self):
    """
    Test evaluation for a complex meta diff rule where # steps is non-linear.
    """
    # Hand-built TM to demonstrate this situation simply.
    tm = IO.parse_tm("1RB------_"
                     "0RB0LC1LD_"
                     "0LC1RA---_"
                     "1LD0LE---_"
                     "1RA0LE---")
    self.options.recursive = True
    prover = Proof_System.Proof_System(tm, self.options, "")


    # Base rule:
    #   1^a A> 0^b 1^c -> 1^a+1 A> 0^b 1^c-1   in 2b + 1 steps
    tape = Tape.Chain_Tape()
    tape.init(0, 0, self.options)
    tape.dir = Turing_Machine.RIGHT
    tape.tape[0] = [Tape.Repeated_Symbol(0, math.inf),
                    Tape.Repeated_Symbol(1, 10),
                   ]
    tape.tape[1] = [Tape.Repeated_Symbol(0, math.inf),
                    Tape.Repeated_Symbol(2, 40),
                    Tape.Repeated_Symbol(1, 30),
                    Tape.Repeated_Symbol(0, 20),
                   ]

    state_A = Turing_Machine.Simple_Machine_State(0)
    full_config = (state_A, tape, None, None)
    stripped_config = Proof_System.strip_config(
      state_A, Turing_Machine.RIGHT, tape.tape)
    base_rule = prover.prove_rule(stripped_config, full_config, delta_loop = 5)
    self.assertIsNotNone(base_rule)
    prover.add_rule(base_rule, stripped_config)
    self.assertGreaterEqual(len(prover.rules), 1)

    # Test rule on an example
    #   1^10 A> 0^20 1^30 -> 1^39 A> 0^20 1^1
    success, rest = prover.apply_rule(base_rule, full_config)
    self.assertTrue(success)
    result, _ = rest
    self.assertEqual(result.condition, Proof_System.APPLY_RULE)
    self.assertEqual(str(result.new_tape), "0^inf 1^39 -> 0^20 1^1 2^40 0^inf")
    # Each application should take 2b+1 (2 * 20 + 1) steps and we apply 29 times.
    self.assertEqual(result.num_base_steps, 29 * (2 * 20 + 1))


    # Second-level (meta) rule:
    #   0^inf 1^a A> 0^b 2^d
    #     -> 0^inf 1^1 A> 0^a+1 1^b 2^d-1  (Steps: 2b+a+2)
    #     -> 0^inf 1^b+1 A> 0^a+1 2^d-1    (Steps: b * (2(a+1) + 1) / Cumulative: 2ab + 5b + a + 2
    #     -> 0^inf 1^a+2 A> 0^b+2 2^d-2    (Steps: 2(b+1)(a+1) + 5(a+1) + (b+1) + 2)
    #   Total steps: 4ab + 8a + 8b + 12
    tape = Tape.Chain_Tape()
    tape.init(0, 0, self.options)
    tape.dir = Turing_Machine.RIGHT
    tape.tape[0] = [Tape.Repeated_Symbol(0, math.inf),
                    Tape.Repeated_Symbol(1, 10),
                   ]
    tape.tape[1] = [Tape.Repeated_Symbol(0, math.inf),
                    Tape.Repeated_Symbol(2, 4),
                    Tape.Repeated_Symbol(0, 20),
                   ]

    state_A = Turing_Machine.Simple_Machine_State(0)
    full_config = (state_A, tape, None, None)
    stripped_config = Proof_System.strip_config(
      state_A, Turing_Machine.RIGHT, tape.tape)
    meta_rule = prover.prove_rule(stripped_config, full_config, delta_loop = 36)

    # Check that rule was proven successfully
    self.assertTrue(meta_rule)
    self.assertTrue(meta_rule.is_meta_rule)

    # Test rule on an example:
    #   1^10 A> 0^20 2^40 -> 1^48 A> 0^58 2^2
    tape = Tape.Chain_Tape()
    tape.init(0, 0, self.options)
    tape.dir = Turing_Machine.RIGHT
    tape.tape[0] = [Tape.Repeated_Symbol(0, math.inf),
                    Tape.Repeated_Symbol(1, 10),
                   ]
    tape.tape[1] = [Tape.Repeated_Symbol(0, math.inf),
                    Tape.Repeated_Symbol(2, 40),
                    Tape.Repeated_Symbol(0, 20),
                   ]

    full_config = (state_A, tape, None, None)

    success, rest = prover.apply_rule(meta_rule, full_config)
    self.assertTrue(success)
    result, _ = rest
    self.assertEqual(result.condition, Proof_System.APPLY_RULE)
    self.assertEqual(str(result.new_tape), "0^inf 1^48 -> 0^58 2^2 0^inf")
    # a = 10 + 2k ; b = 20 + 2k
    # Total steps = sum_{k=0}^{N-1} (4ab + 8a + 8b + 12)
    #   = sum_k (4 (10+2k) (20+2k) + 8 (10+2k + 20+2k) + 12)
    #   = 16 sum_k k^2  +  (240+32) sum_k k  +  (800+240+12) sum_k 1
    #   = 8/3 N(N-1)(2N-1) + 136 N(N-1) + 1052 N
    N = 19
    self.assertEqual(result.num_base_steps,
                     N * (N-1) * (2*N-1) * 8 / 3 +
                     136 * N * (N-1) + 1052 * N)


if __name__ == '__main__':
  unittest.main()
