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
import globals

import Algebraic_Expression
import IO

from Macro import Tape
from Macro import Turing_Machine
from Macro.Turing_Machine import Block_Symbol


def factor_expr(expr, var):
  """Helper method to simplify tests for factor_var()."""
  assert len(expr.terms) == 1, expr
  assert expr.const == 0, expr
  return Proof_System.factor_var(expr.terms[0], var)

class ProofSystemTest(unittest.TestCase):
  def setUp(self):
    globals.init()

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

    # Cubic: sum_{k=0}^{N-1}(k^3) = (N(N-1)/2)^2
    self.assertEqual(Proof_System.series_sum(k**3, k_var, 10), (10 * 9 // 2) ** 2)
    self.assertEqual(Proof_System.series_sum(2 * k**3, k_var, 5), 2 * (5 * 4 // 2) ** 2)

    # k^4 is not implemented
    with self.assertRaises(NotImplementedError):
      Proof_System.series_sum(k**4, k_var, 5)


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
    full_config = (state_A, tape, None)
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
    bad_full_config = (state_A, bad_tape, None)
    bad_stripped_config = Proof_System.strip_config(
      state_A, Turing_Machine.RIGHT, bad_tape.tape)

    result = prover.try_apply_a_limited_rule(bad_stripped_config, bad_full_config)
    self.assertIsNone(result)

    # Also test with the original (good) config — rule should apply.
    result_good = prover.try_apply_a_limited_rule(stripped_config, full_config)
    self.assertIsNotNone(result_good)
    self.assertEqual(result_good.condition, Proof_System.APPLY_RULE)


  def test_apply_rule_limited_diff_rule(self):
    tm_filename = os.path.join(self.root_dir, "Machines/2x5-e704")
    tm = IO.load_tm(tm_filename, 0)

    proof = Proof_System.Proof_System(tm, self.options, "")

    # To call "apply_rule", a "rule" and a "start_config" are needed.

    # Build the "start_config". It is a tuple containing a "state", "tape", and "loop_num".
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

    loop_num = 3

    current_config = (current_state, current_tape, loop_num)

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

    rule = Proof_System.Limited_Diff_Rule(initial_tape,left_dist,right_dist,diff_tape,initial_state,num_steps,num_loops,rule_num, states_last_seen={}, level=1)
    self.assertIn("Limited Diff Rule", repr(rule))
    self.assertIn("Level: 1", repr(rule))

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
    full_config = (state_A, tape, None)
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
    full_config = (state_A, tape, None)
    stripped_config = Proof_System.strip_config(
      state_A, Turing_Machine.RIGHT, tape.tape)
    meta_rule = prover.prove_rule(stripped_config, full_config, delta_loop = 36)

    # Check repr for base Diff_Rule
    r = repr(base_rule)
    self.assertIn("Diff Rule", r)
    self.assertIn("Level: 1", r)

    # Check that rule was proven successfully
    self.assertTrue(meta_rule)
    self.assertEqual(meta_rule.level, 2)

    # Check repr for level-2 Diff_Rule
    r = repr(meta_rule)
    self.assertIn("Diff Rule", r)
    self.assertIn("Level: 2", r)

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

    full_config = (state_A, tape, None)

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


  def test_meta_linear_rule(self):
    """
    Test evaluation for a meta linear rule where substitution must happen within an ExpInt.
    """
    # TM I found this bug in.
    tm = IO.parse_tm("1RB1RA_0LC1RF_1LE1LD_0LB1LC_0RA---_0RD0LF")
    tm = Turing_Machine.Block_Macro_Machine(tm, 2)
    self.options.recursive = True
    self.options.exp_linear_rules = True
    self.options.exp_meta_linear_rules = True
    self.options.compute_steps = False
    # Only allow General_Rules to be applied once so that we can see the result directly.
    self.options.max_num_reps = 1
    prover = Proof_System.Proof_System(tm, self.options, "")


    # Diff Rule 1:
    #   $ <E 11^a 10 00^b 10 $ -> $ <E 11^a+2 10 00^b-1 10 $
    tape = Tape.Chain_Tape()
    tape.init(0, 0, self.options)
    tape.dir = Turing_Machine.LEFT
    tape.tape[0] = [Tape.Repeated_Symbol(Block_Symbol((0, 0)), math.inf),
                   ]
    tape.tape[1] = [Tape.Repeated_Symbol(Block_Symbol((0, 0)), math.inf),
                    Tape.Repeated_Symbol(Block_Symbol((1, 0)), 1),
                    Tape.Repeated_Symbol(Block_Symbol((0, 0)), 30),
                    Tape.Repeated_Symbol(Block_Symbol((1, 0)), 1),
                    Tape.Repeated_Symbol(Block_Symbol((1, 1)), 20),
                   ]

    state_E = Turing_Machine.Simple_Machine_State(4)
    full_config = (state_E, tape, None)
    stripped_config = Proof_System.strip_config(
      state_E, Turing_Machine.LEFT, tape.tape)
    rule_d1 = prover.prove_rule(stripped_config, full_config, delta_loop = 10)
    self.assertIsNotNone(rule_d1)
    self.assertIn("Diff Rule", repr(rule_d1))
    prover.add_rule(rule_d1, stripped_config)
    self.assertEqual(len(prover.rules), 1)
    # Test rule on an example
    #   $ <E 11^20 10 00^32 10 $ -> $ <E 11^20+2*30 10 00^2 10 $
    success, rest = prover.apply_rule(rule_d1, full_config)
    self.assertTrue(success)
    result, _ = rest
    self.assertEqual(result.condition, Proof_System.APPLY_RULE)
    self.assertEqual(str(result.new_tape), "00^inf <- 11^78 10^1 00^1 10^1 00^inf")

    # Diff Rule 2:
    #   $ <E 11^a 10 00^b 11^c 10 $ -> $ <E 11^a+2 10 00^b-1 11^c 10 $
    tape = Tape.Chain_Tape()
    tape.init(0, 0, self.options)
    tape.dir = Turing_Machine.LEFT
    tape.tape[0] = [Tape.Repeated_Symbol(Block_Symbol((0, 0)), math.inf),
                   ]
    tape.tape[1] = [Tape.Repeated_Symbol(Block_Symbol((0, 0)), math.inf),
                    Tape.Repeated_Symbol(Block_Symbol((1, 0)), 1),
                    Tape.Repeated_Symbol(Block_Symbol((1, 1)), 40),
                    Tape.Repeated_Symbol(Block_Symbol((0, 0)), 30),
                    Tape.Repeated_Symbol(Block_Symbol((1, 0)), 1),
                    Tape.Repeated_Symbol(Block_Symbol((1, 1)), 20),
                   ]

    full_config = (state_E, tape, None)
    stripped_config = Proof_System.strip_config(
      state_E, Turing_Machine.LEFT, tape.tape)
    rule_d2 = prover.prove_rule(stripped_config, full_config, delta_loop = 10)
    self.assertIsNotNone(rule_d2)
    prover.add_rule(rule_d2, stripped_config)
    self.assertEqual(len(prover.rules), 2)
    # Test rule on an example
    #   $ <E 11^20 10 00^32 11^40 10 $ -> $ <E 11^20+2*30 10 00^2 11^40 10 $
    success, rest = prover.apply_rule(rule_d2, full_config)
    self.assertTrue(success)
    result, _ = rest
    self.assertEqual(result.condition, Proof_System.APPLY_RULE)
    self.assertEqual(str(result.new_tape), "00^inf <- 11^78 10^1 00^1 11^40 10^1 00^inf")


    # Linear Rule:
    #   $ <E 11^g 10 00 11^f 10 $ -> $ <E 11^2g+6 10 00 11^f-1 10 $
    tape = Tape.Chain_Tape()
    tape.init(0, 0, self.options)
    tape.dir = Turing_Machine.LEFT
    tape.tape[0] = [Tape.Repeated_Symbol(Block_Symbol((0, 0)), math.inf),
                   ]
    tape.tape[1] = [Tape.Repeated_Symbol(Block_Symbol((0, 0)), math.inf),
                    Tape.Repeated_Symbol(Block_Symbol((1, 0)), 1),
                    Tape.Repeated_Symbol(Block_Symbol((1, 1)), 5),
                    Tape.Repeated_Symbol(Block_Symbol((0, 0)), 1),
                    Tape.Repeated_Symbol(Block_Symbol((1, 0)), 1),
                    Tape.Repeated_Symbol(Block_Symbol((1, 1)), 20),
                   ]

    full_config = (state_E, tape, None)
    stripped_config = Proof_System.strip_config(
      state_E, Turing_Machine.LEFT, tape.tape)
    rule_linear = prover.prove_rule(stripped_config, full_config, delta_loop = 28)
    self.assertIsNotNone(rule_linear)
    self.assertTrue(isinstance(rule_linear, Proof_System.Linear_Rule))
    self.assertIn("Linear Rule", repr(rule_linear))
    self.assertIn("Level:", repr(rule_linear))
    self.assertIn("General Rule", repr(rule_linear.gen_rule))
    prover.add_rule(rule_linear, stripped_config)
    self.assertEqual(len(prover.rules), 3)
    # Test rule on an example:
    #   $ <E 11^20 10 00 11^5 10 $ -> $ <E 11^{26 2^4 - 6} 10 00 11^1 10 $
    success, rest = prover.apply_rule(rule_linear, full_config)
    self.assertTrue(success)
    result, _ = rest
    self.assertEqual(result.condition, Proof_System.APPLY_RULE)
    self.assertEqual(str(result.new_tape), f"00^inf <- 11^(-6 + 13 * 2^5) 10^1 00^1 11^1 10^1 00^inf")


    # Meta Rule:
    #   $ <E 11^h 10 00 11 10 $ -> $ <E 11^(-6 + 5 * 2^(2 h + 8)) 10 00 11 10 $
    tape = Tape.Chain_Tape()
    tape.init(0, 0, self.options)
    tape.dir = Turing_Machine.LEFT
    tape.tape[0] = [Tape.Repeated_Symbol(Block_Symbol((0, 0)), math.inf),
                   ]
    tape.tape[1] = [Tape.Repeated_Symbol(Block_Symbol((0, 0)), math.inf),
                    Tape.Repeated_Symbol(Block_Symbol((1, 0)), 1),
                    Tape.Repeated_Symbol(Block_Symbol((1, 1)), 1),
                    Tape.Repeated_Symbol(Block_Symbol((0, 0)), 1),
                    Tape.Repeated_Symbol(Block_Symbol((1, 0)), 1),
                    Tape.Repeated_Symbol(Block_Symbol((1, 1)), 10),
                   ]

    full_config = (state_E, tape, None)
    stripped_config = Proof_System.strip_config(
      state_E, Turing_Machine.LEFT, tape.tape)
    rule_meta = prover.prove_rule(stripped_config, full_config, delta_loop = 68)
    # Check that rule was proven successfully
    self.assertIsNotNone(rule_meta)
    self.assertTrue(isinstance(rule_meta, Proof_System.Exponential_Rule))
    self.assertTrue(rule_meta.infinite)
    self.assertIn("Exponential Rule", repr(rule_meta))
    self.assertIn("Level:", repr(rule_meta))

    # Test that applying the infinite rule returns INF_REPEAT
    success_inf, rest_inf = prover.apply_rule(rule_meta, full_config)
    self.assertTrue(success_inf)
    result_inf, _ = rest_inf
    self.assertEqual(result_inf.condition, Proof_System.INF_REPEAT)

    # Test that rule_meta has used substitution correctly!
    # Note: This is an infinite rule, so we must monkey with things a bit to
    # allow us to apply it only once.
    rule_meta.infinite = False
    # Test rule on an example:
    #   $ <E 11^10 10 00 11 10 $ -> $ <E 11^(-6 + 5 * 2^(20 + 8)) 10 00 11 10 $
    success, rest = prover.apply_rule(rule_meta, full_config)
    self.assertTrue(success)
    result, _ = rest
    self.assertEqual(result.condition, Proof_System.APPLY_RULE)
    self.assertEqual(str(result.new_tape), f"00^inf <- 11^(-6 + 5 * 2^28) 10^1 00^1 11^1 10^1 00^inf")


  def test_apply_linear_rule_exp_disabled(self):
    """Test apply_linear_rule fallback to apply_general_rule when exp_linear_rules=False.

    Also exercises apply_general_rule finite loop and infinite paths.
    """
    # Setup same TM as test_meta_linear_rule
    tm = IO.parse_tm("1RB1RA_0LC1RF_1LE1LD_0LB1LC_0RA---_0RD0LF")
    tm = Turing_Machine.Block_Macro_Machine(tm, 2)
    self.options.recursive = True
    self.options.exp_linear_rules = True
    self.options.exp_meta_linear_rules = True
    self.options.compute_steps = True
    self.options.max_num_reps = 3
    prover = Proof_System.Proof_System(tm, self.options, "")

    state_E = Turing_Machine.Simple_Machine_State(4)

    # Prove Diff Rule 1
    tape = Tape.Chain_Tape()
    tape.init(0, 0, self.options)
    tape.dir = Turing_Machine.LEFT
    tape.tape[0] = [Tape.Repeated_Symbol(Block_Symbol((0, 0)), math.inf)]
    tape.tape[1] = [Tape.Repeated_Symbol(Block_Symbol((0, 0)), math.inf),
                    Tape.Repeated_Symbol(Block_Symbol((1, 0)), 1),
                    Tape.Repeated_Symbol(Block_Symbol((0, 0)), 30),
                    Tape.Repeated_Symbol(Block_Symbol((1, 0)), 1),
                    Tape.Repeated_Symbol(Block_Symbol((1, 1)), 20)]
    full_config = (state_E, tape, None)
    stripped_config = Proof_System.strip_config(state_E, Turing_Machine.LEFT, tape.tape)
    rule_d1 = prover.prove_rule(stripped_config, full_config, delta_loop=10)
    self.assertIsNotNone(rule_d1)
    prover.add_rule(rule_d1, stripped_config)

    # Prove Diff Rule 2
    tape = Tape.Chain_Tape()
    tape.init(0, 0, self.options)
    tape.dir = Turing_Machine.LEFT
    tape.tape[0] = [Tape.Repeated_Symbol(Block_Symbol((0, 0)), math.inf)]
    tape.tape[1] = [Tape.Repeated_Symbol(Block_Symbol((0, 0)), math.inf),
                    Tape.Repeated_Symbol(Block_Symbol((1, 0)), 1),
                    Tape.Repeated_Symbol(Block_Symbol((1, 1)), 40),
                    Tape.Repeated_Symbol(Block_Symbol((0, 0)), 30),
                    Tape.Repeated_Symbol(Block_Symbol((1, 0)), 1),
                    Tape.Repeated_Symbol(Block_Symbol((1, 1)), 20)]
    full_config = (state_E, tape, None)
    stripped_config = Proof_System.strip_config(state_E, Turing_Machine.LEFT, tape.tape)
    rule_d2 = prover.prove_rule(stripped_config, full_config, delta_loop=10)
    self.assertIsNotNone(rule_d2)
    prover.add_rule(rule_d2, stripped_config)

    # Prove Linear Rule
    tape = Tape.Chain_Tape()
    tape.init(0, 0, self.options)
    tape.dir = Turing_Machine.LEFT
    tape.tape[0] = [Tape.Repeated_Symbol(Block_Symbol((0, 0)), math.inf)]
    tape.tape[1] = [Tape.Repeated_Symbol(Block_Symbol((0, 0)), math.inf),
                    Tape.Repeated_Symbol(Block_Symbol((1, 0)), 1),
                    Tape.Repeated_Symbol(Block_Symbol((1, 1)), 5),
                    Tape.Repeated_Symbol(Block_Symbol((0, 0)), 1),
                    Tape.Repeated_Symbol(Block_Symbol((1, 0)), 1),
                    Tape.Repeated_Symbol(Block_Symbol((1, 1)), 20)]
    full_config = (state_E, tape, None)
    stripped_config = Proof_System.strip_config(state_E, Turing_Machine.LEFT, tape.tape)
    rule_linear = prover.prove_rule(stripped_config, full_config, delta_loop=28)
    self.assertIsNotNone(rule_linear)
    self.assertIsInstance(rule_linear, Proof_System.Linear_Rule)
    # rule_linear.gen_rule is the embedded General_Rule with infinite=False
    self.assertFalse(rule_linear.gen_rule.infinite)

    # Test apply_linear_rule with exp_linear_rules=False (fallback to apply_general_rule).
    # This exercises the apply_general_rule finite loop path (and compute_steps=True path).
    prover2 = Proof_System.Proof_System(tm, self.options, "")
    prover2.exp_linear_rules = False
    success, rest = prover2.apply_linear_rule(rule_linear, full_config)
    self.assertTrue(success)
    result, _ = rest
    self.assertEqual(result.condition, Proof_System.APPLY_RULE)

    # Test apply_rule dispatching directly to apply_general_rule (line 1061).
    success_gr, rest_gr = prover2.apply_rule(rule_linear.gen_rule, full_config)
    self.assertTrue(success_gr)
    result_gr, _ = rest_gr
    self.assertEqual(result_gr.condition, Proof_System.APPLY_RULE)

    # Test exp_meta_linear_rules=False path in apply_linear_rule (line 1278).
    prover3 = Proof_System.Proof_System(tm, self.options, "")
    prover3.exp_meta_linear_rules = False
    success_nml, rest_nml = prover3.apply_linear_rule(rule_linear, full_config)
    self.assertTrue(success_nml)
    result_nml, _ = rest_nml
    self.assertEqual(result_nml.condition, Proof_System.APPLY_RULE)

    # Test below-min config in apply_linear_rule.
    bad_tape = Tape.Chain_Tape()
    bad_tape.init(0, 0, self.options)
    bad_tape.dir = Turing_Machine.LEFT
    bad_tape.tape[0] = [Tape.Repeated_Symbol(Block_Symbol((0, 0)), math.inf)]
    bad_tape.tape[1] = [Tape.Repeated_Symbol(Block_Symbol((0, 0)), math.inf),
                        Tape.Repeated_Symbol(Block_Symbol((1, 0)), 1),
                        Tape.Repeated_Symbol(Block_Symbol((1, 1)), 1),  # f=1, likely below min
                        Tape.Repeated_Symbol(Block_Symbol((0, 0)), 1),
                        Tape.Repeated_Symbol(Block_Symbol((1, 0)), 1),
                        Tape.Repeated_Symbol(Block_Symbol((1, 1)), 20)]
    bad_config = (state_E, bad_tape, None)
    success_bad, _ = prover.apply_linear_rule(rule_linear, bad_config)
    self.assertFalse(success_bad)

    # Test apply_general_rule with infinite=True (monkey-patch).
    # This exercises the INF_REPEAT path in apply_general_rule.
    rule_linear.gen_rule.infinite = True
    success_inf, rest_inf = prover2.apply_general_rule(rule_linear.gen_rule, full_config)
    self.assertTrue(success_inf)
    result_inf, _ = rest_inf
    self.assertEqual(result_inf.condition, Proof_System.INF_REPEAT)
    rule_linear.gen_rule.infinite = False  # restore


  def test_verbose_mode(self):
    """Test that verbose_prover=True doesn't crash and covers verbose print paths."""
    import contextlib, io
    tm = IO.parse_tm("1RB------_"
                     "0RB0LC1LD_"
                     "0LC1RA---_"
                     "1LD0LE---_"
                     "1RA0LE---")
    self.options.recursive = True
    self.options.verbose_prover = True
    prover = Proof_System.Proof_System(tm, self.options, "")

    # Suppress the verbose output so test logs stay clean.
    dev_null = io.StringIO()

    # Prove a base Diff_Rule in verbose mode.
    tape = Tape.Chain_Tape()
    tape.init(0, 0, self.options)
    tape.dir = Turing_Machine.RIGHT
    tape.tape[0] = [Tape.Repeated_Symbol(0, math.inf),
                    Tape.Repeated_Symbol(1, 10)]
    tape.tape[1] = [Tape.Repeated_Symbol(0, math.inf),
                    Tape.Repeated_Symbol(2, 40),
                    Tape.Repeated_Symbol(1, 30),
                    Tape.Repeated_Symbol(0, 20)]
    state_A = Turing_Machine.Simple_Machine_State(0)
    base_config = (state_A, tape, None)
    base_stripped = Proof_System.strip_config(state_A, Turing_Machine.RIGHT, tape.tape)

    with contextlib.redirect_stdout(dev_null):
      base_rule = prover.prove_rule(base_stripped, base_config, delta_loop=5)
    self.assertIsNotNone(base_rule)
    prover.add_rule(base_rule, base_stripped)

    # Apply the rule in verbose mode (covers apply_rule and apply_diff_rule verbose paths).
    with contextlib.redirect_stdout(dev_null):
      success, rest = prover.apply_rule(base_rule, base_config)
    self.assertTrue(success)
    result, _ = rest
    # Base rule applies finitely (steps printed in verbose).
    self.assertEqual(result.condition, Proof_System.APPLY_RULE)

    # Prove a meta Diff_Rule in verbose mode.
    tape2 = Tape.Chain_Tape()
    tape2.init(0, 0, self.options)
    tape2.dir = Turing_Machine.RIGHT
    tape2.tape[0] = [Tape.Repeated_Symbol(0, math.inf),
                     Tape.Repeated_Symbol(1, 10)]
    tape2.tape[1] = [Tape.Repeated_Symbol(0, math.inf),
                     Tape.Repeated_Symbol(2, 4),
                     Tape.Repeated_Symbol(0, 20)]
    meta_config = (state_A, tape2, None)
    meta_stripped = Proof_System.strip_config(state_A, Turing_Machine.RIGHT, tape2.tape)

    with contextlib.redirect_stdout(dev_null):
      meta_rule = prover.prove_rule(meta_stripped, meta_config, delta_loop=36)
    self.assertIsNotNone(meta_rule)
    prover.add_rule(meta_rule, meta_stripped)

    # Apply meta rule in verbose mode (covers apply_diff_rule verbose paths).
    with contextlib.redirect_stdout(dev_null):
      success2, rest2 = prover.apply_rule(meta_rule, meta_config)
    self.assertTrue(success2)
    result2, _ = rest2
    self.assertEqual(result2.condition, Proof_System.APPLY_RULE)

    # Apply a hand-crafted Diff_Rule with all non-negative diffs to get INF_REPEAT
    # (covers the INF_REPEAT verbose path in apply_diff_rule).
    a_expr = Algebraic_Expression.Expression_from_string("(a+1)")
    inf_init = Tape.Chain_Tape()
    inf_init.init(0, 0, self.options)
    inf_init.dir = Turing_Machine.RIGHT
    inf_init.tape[0] = [Tape.Repeated_Symbol(0, math.inf)]
    inf_init.tape[1] = [Tape.Repeated_Symbol(0, math.inf),
                        Tape.Repeated_Symbol(1, a_expr)]
    inf_diff = Tape.Chain_Tape()
    inf_diff.init(0, 0, self.options)
    inf_diff.dir = Turing_Machine.RIGHT
    inf_diff.tape[0] = [Tape.Repeated_Symbol(0, math.inf)]  # 0^inf unchanged
    inf_diff.tape[1] = [Tape.Repeated_Symbol(0, math.inf),
                        Tape.Repeated_Symbol(1, 1)]           # diff = +1 (always grows)
    inf_rule = Proof_System.Diff_Rule(
        inf_init, inf_diff, state_A,
        Algebraic_Expression.ConstantToExpression(1), 1, 99, 1,
        states_last_seen={})
    inf_tape = Tape.Chain_Tape()
    inf_tape.init(0, 0, self.options)
    inf_tape.dir = Turing_Machine.RIGHT
    inf_tape.tape[0] = [Tape.Repeated_Symbol(0, math.inf)]
    inf_tape.tape[1] = [Tape.Repeated_Symbol(0, math.inf),
                        Tape.Repeated_Symbol(1, 5)]
    inf_config = (state_A, inf_tape, None)
    with contextlib.redirect_stdout(dev_null):
      success3, rest3 = prover.apply_rule(inf_rule, inf_config)
    self.assertTrue(success3)
    result3, _ = rest3
    self.assertEqual(result3.condition, Proof_System.INF_REPEAT)


if __name__ == '__main__':
  globals.init()
  unittest.main()
