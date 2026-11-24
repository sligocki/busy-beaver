import optparse
import os
import unittest

import IO
from Big_Interval import BigInterval, Knuth10, NotComparable
from Exp_Int import exp_int
from Macro import Proof_System, Simulator, Turing_Machine
from NatExpr import ConstInt


class TestKnuth10(unittest.TestCase):
  def test_lower_bound_from_int(self):
    # With C=10
    self.assertEqual(Knuth10.lower_bound_from_int(9).args, (9,))
    self.assertEqual(Knuth10.lower_bound_from_int(10).args, (10,))
    self.assertEqual(Knuth10.lower_bound_from_int(1000).args, (1000,))
    self.assertEqual(Knuth10.lower_bound_from_int(10**1000).args, (1000, 1))
    self.assertEqual(Knuth10.lower_bound_from_int(10**10000).args, (10000, 1))

  def test_safe_upper_bound(self):
    # Base increment
    # 10^1000 +1 ≤ 10^1001
    self.assertEqual(Knuth10(1000, 1).safe_upper_bound().args, (1001, 1))
    # Rollover to next operation
    # 10^{10^1000 - 1} +1 ≤ 10^10^1000
    self.assertEqual(Knuth10(10**1000 - 1, 1).safe_upper_bound().args, (1000, 2))
    # Rollover past max allowed a_i
    # (10^)^997 (10^1000 - 1) +1 ≤ 10^^1000
    self.assertEqual(Knuth10(10**1000 - 1, 997).safe_upper_bound().args, (1000, 0, 1))

  def test_compare(self):
    self.assertTrue(Knuth10(100) < Knuth10(10, 1))
    self.assertTrue(Knuth10(10, 1) < Knuth10(11, 1))
    self.assertTrue(Knuth10(10**10 - 1, 8) < Knuth10(10, 0, 1))
    self.assertTrue(Knuth10(10, 0, 1) == Knuth10(10, 0, 1))

  def test_uparrow_str_formatting(self):
    k3 = Knuth10(1000, 0, 0, 1)
    self.assertEqual(str(k3), "10↑↑↑ 1000")
    self.assertEqual(k3.approx_str(), "10↑↑↑ 1000")

    k4 = Knuth10(1000, 0, 0, 0, 1)
    self.assertEqual(str(k4), "10↑⁴ 1000")
    self.assertEqual(k4.approx_str(), "10↑⁴ 1000")

    k6_rep = Knuth10(1000, 0, 0, 0, 0, 0, 3)
    self.assertEqual(str(k6_rep), "(10↑⁶)^3 1000")
    self.assertEqual(k6_rep.approx_str(), "(10↑⁶)^3 1000")

    k11 = Knuth10(1000, *([0] * 10), 1)
    self.assertEqual(str(k11), "10↑¹¹ 1000")
    self.assertEqual(k11.approx_str(), "10↑¹¹ 1000")


class TestBigInterval(unittest.TestCase):
  def test_small_add(self):
    # [10, 10] + [20, 20] = [30, 30]
    A = BigInterval(10)
    B = BigInterval(20)
    C = A + B
    self.assertEqual(C.lower.args, (30,))
    self.assertEqual(C.upper.args, (30,))

  def test_huge_add(self):
    # 10^100 + 10^200 -> bounds around 10^200
    A = BigInterval(10**1000)
    B = BigInterval(10**2000)
    C = A + B
    self.assertEqual(C.lower.args, (2000, 1))
    self.assertEqual(C.upper.args, (2001, 1))

  def test_small_mul(self):
    # [10, 10] * [20, 20] = [200, 200]
    A = BigInterval(10)
    B = BigInterval(20)
    C = A * B
    self.assertEqual(C.lower.args, (200,))
    self.assertEqual(C.upper.args, (200,))

  def test_huge_mul(self):
    # 10^100 * 10^200 -> exact lower and upper bound 10^300
    A = BigInterval(10**1000)
    B = BigInterval(10**2000)
    C = A * B
    self.assertEqual(C.lower.args, (2000, 1))
    self.assertEqual(C.upper.args, (3000, 1))

  def test_mul_x_squared(self):
    # X = 10^100. X^2 = 10^200.
    A = BigInterval(10**1000)
    C = A * A
    self.assertEqual(C.lower.args, (1000, 1))
    self.assertEqual(C.upper.args, (2000, 1))

    # Test X^2 logic without exact eval (use 10^10000)
    A = BigInterval(Knuth10(10000, 1), Knuth10(10000, 1))
    C = A * A
    self.assertEqual(C.lower.args, (10000, 1))  # lower bound is max(A, B) when not eval'd
    self.assertEqual(C.upper.args, (20000, 1))  # upper bound uses X^2 special logic

  def test_pow(self):
    # 10 ** 100 -> (100, 1)
    A = BigInterval(10)
    B = BigInterval(1000)
    C = A**B
    self.assertEqual(C.lower.args, (1000, 1))
    self.assertEqual(C.upper.args, (1001, 1))

    # 2 ** 100
    A = BigInterval(2)
    B = BigInterval(10000)
    C = A**B
    self.assertEqual(C.lower.args, (3010, 1))
    self.assertEqual(C.upper.args, (3011, 1))

  def test_huge_pow(self):
    # 10 ** (10**100)
    A = BigInterval(10)
    B = BigInterval(10**1000)
    C = A**B
    self.assertEqual(C.lower.args, (1000, 2))
    self.assertEqual(C.upper.args, (1000, 2))

  def test_truediv(self):
    A = BigInterval(100)
    B = BigInterval(3)
    C = A / B
    self.assertEqual(C.lower.args, (33,))
    self.assertEqual(C.upper.args, (34,))

  def test_apply_g1_len3_and_carry(self):
    # Regression: apply_g1() on len(args) >= 3 must not increment a[1]
    x = Knuth10(4294967295, 0, 1)
    lo = x.apply_g1()
    hi = x.apply_g1_upper()
    self.assertEqual(lo.args, (4294967296, 0, 1))
    self.assertEqual(hi.args, (4294967296, 0, 1))

    # Boundary carry at a_1 > MAX_A = 997: requires a_0 >= 10**10 to reach (C, 0, 1)
    small_a0 = Knuth10(1000, 997).apply_g1()
    self.assertEqual(small_a0.args, (10 ** (Knuth10.C - 1), Knuth10.MAX_A))
    big_a0 = Knuth10(10**10, 997).apply_g1()
    self.assertEqual(big_a0.args, (Knuth10.C, 0, 1))

  def test_sub_and_const_int(self):
    # ConstInt initialization
    ci = BigInterval(ConstInt(42))
    self.assertEqual(ci.lower.args, (42,))
    self.assertEqual(ci.upper.args, (42,))

    # Small subtraction
    res = BigInterval(100) - BigInterval(35)
    self.assertEqual(res.lower.args, (65,))
    self.assertEqual(res.upper.args, (65,))

    # Large subtraction where other << self / 10
    big_sub = (BigInterval(2) ** 10000) - (BigInterval(2) ** 5000)
    self.assertTrue(big_sub.lower >= Knuth10(1000, 1))
    self.assertTrue(big_sub.lower <= big_sub.upper)

    with self.assertRaises(ValueError):
      _ = BigInterval(10) - BigInterval(20)

  def test_truediv_large_denom(self):
    A = BigInterval(Knuth10(10**500, 1), Knuth10(10**500, 1))
    C = A / BigInterval(100)
    self.assertEqual(C.lower.args, (10**500 - 3, 1))

  def test_truediv_large_exact_int(self):
    A = BigInterval(10**500)
    C = A / BigInterval(2)
    self.assertEqual(C.lower.try_eval(), (10**500) // 2)
    self.assertEqual(C.upper.try_eval(), (10**500) // 2)

    D = BigInterval(10**500 + 1) / BigInterval(3)
    self.assertEqual(D.lower.try_eval(), (10**500 + 1) // 3)
    self.assertEqual(D.upper.try_eval(), (10**500 + 3) // 3)

  def test_exp_int_negative_terms(self):
    e1 = exp_int(2, 10000) - exp_int(2, 5000)
    bi1 = e1.to_BigInterval()
    self.assertEqual(bi1.lower, Knuth10(3009, 1))
    self.assertTrue(bi1.upper <= Knuth10(3015, 1))

    # 6x2 t15 (-11 + 3^(...)) / 2
    import Halting_Lib
    import Macro_Simulator
    import TM_Enum
    from IO import TM_Record

    tm_record = TM_Record.TM_Record(
      tm_enum=TM_Enum.TM_Enum(IO.parse_tm("1RB0LD_1RC0RF_1LC1LA_0LE1RZ_1LF0RB_0RC0RE"), allow_no_halt=False)
    )
    parser = optparse.OptionParser()
    Macro_Simulator.add_option_group(parser)
    options, _ = parser.parse_args([])
    options.time = 0
    options.prover_level = Proof_System.ProverLevel.EXP
    options.compute_steps = True
    options.max_loops = 1_000_000
    options.max_block_size = 100
    Macro_Simulator.run_options(tm_record, options)
    score_expr = Halting_Lib.get_big_int(tm_record.proto.status.halt_status.halt_score)
    bi_t15 = score_expr.to_BigInterval()
    self.assertEqual(bi_t15.approx_str(), "[10↑↑15, 10↑↑16]")

  def _run_tm_nonzeros_bi(self, tm_or_path, block_size, max_loops=0, max_steps_back=1000):
    parser = optparse.OptionParser()
    Simulator.add_option_group(parser)
    opts, _ = parser.parse_args(["-l", "max"])
    opts.backsymbol = True
    if "_" in tm_or_path:
      tm = IO.parse_tm(tm_or_path)
    else:
      root = os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir))
      tm = IO.get_tm(os.path.join(root, tm_or_path))
    m = Turing_Machine.Block_Macro_Machine(tm, block_size)
    m = Turing_Machine.Backsymbol_Macro_Machine(m, max_sim_steps_per_symbol=max_steps_back)
    sim = Simulator.Simulator(m, opts)
    if max_loops:
      sim.loop_seek(max_loops)
    else:
      while sim.op_state == Turing_Machine.RUNNING:
        sim.loop_run(1000)
    return sim.get_nonzeros().to_BigInterval()

  def test_7state_n12_n24_big_interval_consistency(self):
    tm = "1RB0RF_1RC0LF_1LD1LE_1RA1LC_0LB0RG_1RC1RA_1RZ0RE"
    bi12 = self._run_tm_nonzeros_bi(tm, 12)
    bi24 = self._run_tm_nonzeros_bi(tm, 24)
    self.assertEqual(bi12.approx_str(), "[(10↑↑)^21 10^9, (10↑↑)^21 10^10]")
    self.assertEqual(bi24.approx_str(), "[(10↑↑)^21 10^9, (10↑↑)^21 10^10]")
    with self.assertRaises(NotComparable):
      bi12.cmp(bi24)

  def test_ack34_and_11x2_green_big_interval(self):
    bi_green = self._run_tm_nonzeros_bi("Machines/11x2-Green", 2)
    self.assertEqual(bi_green.approx_str(), "[10↑↑↑ 10^15, 10↑↑↑ 10^16]")

    bi_ack = self._run_tm_nonzeros_bi("1RB3LB1RZ2RA_2LC3RB1LC2RA_3RB1LB3LC2RC", 2, max_loops=21000, max_steps_back=250)
    self.assertEqual(len(bi_ack.lower.args), 4)
    self.assertEqual(len(bi_ack.upper.args), 4)
    self.assertEqual(bi_ack.lower.args[1:3], (0, 1))
    self.assertEqual(bi_ack.upper.args[1:3], (0, 1))
    self.assertGreaterEqual(bi_ack.lower.args[3], 1)
    self.assertEqual(bi_ack.lower.args[3], bi_ack.upper.args[3])
    self.assertTrue(bi_ack.lower.args[0] <= 65534 <= bi_ack.upper.args[0])

  def test_nat_expr_approx_and_full_str_uses_big_interval(self):
    from NatExpr import approx_and_full_str, approx_or_full_str, big_interval_str

    self.assertEqual(big_interval_str(12345), "12_345")
    e = exp_int(2, 10000)
    self.assertEqual(big_interval_str(e), "[10↑ 3010, 10↑ 3012]")
    self.assertEqual(approx_or_full_str(e, max_chars=5), "[10↑ 3010, 10↑ 3012]")
    self.assertTrue(approx_and_full_str(e, max_chars=5).startswith("[10↑ 3010, 10↑ 3012] (_"))

  def test_deep_nested_exp_and_iterated_no_recursion_error(self):
    import sys
    from Algebraic_Expression import Variable, VariableToExpression
    from Iterated_Expression import Iterated_Expression
    from NatExpr import approx_and_full_str, approx_or_full_str

    v = Variable()
    step = exp_int(2, VariableToExpression(v) + 1)
    old_limit = sys.getrecursionlimit()
    try:
      sys.setrecursionlimit(200)
      cur = exp_int(2, 1000)
      for _ in range(100):
        it = Iterated_Expression(step, v, cur, 3)
        cur = exp_int(2, it + 1)
      bi = cur.to_BigInterval()
      self.assertTrue(len(bi.lower.args) >= 2)
      s = str(cur)
      self.assertGreater(len(s), 1000)
      self.assertTrue(approx_or_full_str(cur, max_chars=100).startswith("["))
      self.assertIn(f"(_{len(s)} chars_)", approx_and_full_str(cur, max_chars=100))
    finally:
      sys.setrecursionlimit(old_limit)

  def test_branching_dag_approx_and_full_str(self):
    from Algebraic_Expression import Variable, VariableToExpression
    from Iterated_Expression import Iterated_Expression
    from NatExpr import approx_and_full_str, approx_or_full_str, expr_str_len

    v = Variable()
    step = 2 * VariableToExpression(v) + 1
    cur = exp_int(2, 1000)
    for _ in range(80):
      cur = Iterated_Expression(step, v, cur, cur) + 1
    # Expanded string length is > 2^80, but DAG length/interval eval must not OOM or recurse.
    self.assertGreater(expr_str_len(cur), 2**80)
    self.assertTrue(approx_or_full_str(cur, max_chars=100).startswith("["))
    self.assertIn("chars_)", approx_and_full_str(cur, max_chars=100))

  def test_deep_iterated_tower_bounds_no_recursion_error(self):
    import sys
    from Algebraic_Expression import Variable, VariableToExpression
    from Iterated_Expression import Iterated_Expression

    v = Variable()
    inner_v = Variable()
    inner_step = exp_int(2, VariableToExpression(inner_v) + 1)
    old_limit = sys.getrecursionlimit()
    try:
      sys.setrecursionlimit(200)
      cur = VariableToExpression(v) + 1
      for _ in range(150):
        it = Iterated_Expression(inner_step, inner_v, 2, cur)
        cur = exp_int(2, exp_int(2, it + 1))
      outer = Iterated_Expression(cur, v, 10, 100)
      bi = outer.to_BigInterval()
      self.assertGreaterEqual(len(bi.lower.args), 3)
      self.assertGreaterEqual(len(bi.upper.args), 3)
    finally:
      sys.setrecursionlimit(old_limit)

  def test_tower_lower_overlapping_start_val_no_not_comparable(self):
    from Algebraic_Expression import Variable, VariableToExpression
    from Iterated_Expression import Iterated_Expression

    # When inner start_val has a non-degenerate interval [19, 21] overlapping the
    # threshold 20 in _tower_lower, it must compare Knuth10 endpoints without raising NotComparable.
    r = Variable()
    w = Variable()
    inner_step = exp_int(3, VariableToExpression(r) + 1)
    # start_val whose BigInterval is [19, 21] (contains 20 -> overlapping with BigInterval(20))
    start_overlap = (exp_int(2, 100) + exp_int(2, 99)) // exp_int(2, 95)
    mid_step = Iterated_Expression(inner_step, r, start_overlap, VariableToExpression(w) + 2)
    outer = Iterated_Expression(mid_step, w, 100, 100)
    bi = outer.to_BigInterval()
    self.assertTrue(bi.lower <= bi.upper)

  def test_tower_lower_constint_unroll_and_large_start(self):
    from Algebraic_Expression import Variable, VariableToExpression
    from Iterated_Expression import Iterated_Expression, _tower_lower
    from NatExpr import ConstInt

    # 1) ConstInt in Expression.const + 1-step unroll reaching threshold 20
    x = Variable()
    w = Variable()
    # -4 + 2^(x + ConstInt(4))
    step1 = exp_int(2, VariableToExpression(x) + ConstInt(4)) - 4
    it1 = Iterated_Expression(step1, x, 12, VariableToExpression(w) + ConstInt(1))
    tl = _tower_lower(it1, w, 2, BigInterval(65532))
    self.assertEqual(tl[0], 1)
    self.assertGreaterEqual(tl[1], 1)
    self.assertGreaterEqual(tl[2], 0)

    outer = Iterated_Expression(it1, w, 65532, 100)
    bi = outer.to_BigInterval()
    self.assertGreaterEqual(len(bi.lower.args), 3)
    self.assertTrue(bi.lower <= bi.upper)

    # 2) Large start_val (>= 10^1000, so try_eval() is None) with non-negative additive offset
    y = Variable()
    z = Variable()
    big_start = Iterated_Expression(exp_int(2, VariableToExpression(y)), y, 10, 10000)
    inner = Iterated_Expression(
      exp_int(2, VariableToExpression(y)) + ConstInt(5), y, 10, VariableToExpression(y) + ConstInt(3)
    )
    mid = Iterated_Expression(inner, y, big_start, VariableToExpression(z) + ConstInt(7))
    tl_mid = _tower_lower(mid, z, 3, BigInterval(big_start.to_BigInterval().lower, big_start.to_BigInterval().lower))
    self.assertEqual(tl_mid[0], 1)
    self.assertGreaterEqual(tl_mid[1], 1)

  def test_tower_lower_expint_at_level_ge_2_is_sound(self):
    from Algebraic_Expression import Variable, VariableToExpression
    from Iterated_Expression import _tower_lower

    x = Variable()
    # 3^(6*x + 19) is exponential (level 1), so at level_k=2 it must have h=0 (not h=1).
    e = exp_int(3, 6 * VariableToExpression(x) + 19)
    tl = _tower_lower(e, x, 2, BigInterval(100))
    self.assertEqual(tl[0], 0)

  def test_is_wide(self):
    # Exact and tight intervals are not wide
    self.assertFalse(BigInterval(42).is_wide())
    self.assertFalse(BigInterval(Knuth10(33), Knuth10(34)).is_wide())
    self.assertFalse(BigInterval(Knuth10(0), Knuth10(1)).is_wide())
    self.assertFalse(BigInterval(Knuth10(3010, 1), Knuth10(3012, 1)).is_wide())
    self.assertFalse(BigInterval(Knuth10(2161856886993798, 0, 0, 1), Knuth10(3242785330490752, 0, 0, 1)).is_wide())

    # Grid rollovers are not wide
    self.assertFalse(BigInterval(Knuth10(Knuth10.MAX_A0 - 1), Knuth10(Knuth10.C, 1)).is_wide())
    self.assertFalse(BigInterval(Knuth10(5 * 10 ** (Knuth10.C - 1), 1), Knuth10(Knuth10.C, 2)).is_wide())
    self.assertFalse(BigInterval(Knuth10(10 ** (Knuth10.C - 1), Knuth10.MAX_A), Knuth10(Knuth10.C, 0, 1)).is_wide())

    # Zero lower bound with large upper bound is wide
    self.assertTrue(BigInterval(Knuth10(0), Knuth10(100)).is_wide())
    self.assertTrue(BigInterval(Knuth10(0), Knuth10(442057658763040, 7)).is_wide())

    # Different arrow levels / tower heights are wide
    self.assertTrue(BigInterval(Knuth10(1000, 1), Knuth10(1000, 2)).is_wide())
    self.assertTrue(BigInterval(Knuth10(2161856886993690, 0, 1, 7), Knuth10(2161856886993945, 0, 1, 0, 1)).is_wide())

    # Large gap in a0 (> 10x) is wide
    self.assertTrue(BigInterval(Knuth10(1000, 1), Knuth10(10001, 1)).is_wide())
    self.assertTrue(BigInterval(Knuth10(10), Knuth10(101)).is_wide())

  def test_exp_int_overlapping_exponent_subtraction_tightening(self):
    # Two terms whose exponents have identical BigIntervals at height 2,
    # e.g. 3^(4*X/27) - 2*3^(5*X/54) where X = 3^(10000), so E0 - E1 = X/18 >> 1.
    x = exp_int(3, 10000)
    e0 = (4 * x + 19) // 27
    e1 = (5 * x + 23) // 54
    expr = exp_int(3, e0) - 2 * exp_int(3, e1)
    bi = expr.to_BigInterval()
    self.assertFalse(bi.is_wide())
    self.assertGreater(bi.lower, Knuth10(0))
    self.assertEqual(len(bi.lower.args), len(bi.upper.args))
    self.assertTrue(bi.lower <= bi.upper)

    # Soundness check: when the negative term is NOT dwarfed (e.g. 2*3^E - 3^E = 3^E,
    # or 3^(E+1) - 2*3^E = 3^E where coefs are close), lower bound must remain <= true value.
    e_close = (5 * x + 23) // 54
    # 3^(e_close + 1) - 2 * 3^(e_close) = 3^(e_close), wait: 3*3^e - 2*3^e = 3^e (normalizes to 1 term).
    # Instead construct 3^(X/2 + 2) - 4*3^(X/2) = 5 * 3^(X/2), where diff = 2 and 1*3^2 = 9 >= 2*1*4 = 8.
    expr_tight_ok = exp_int(3, e_close + 2) - 4 * exp_int(3, e_close)
    bi_ok = expr_tight_ok.to_BigInterval()
    self.assertTrue(bi_ok.lower <= bi_ok.upper)

    # Regression test for 4x3_exception.pb:11 (previously [0, (10↑)^7 442057658763040])
    bi_tm = self._run_tm_nonzeros_bi("1RB2LA2LC_1LA1RA0RC_0LA2RB0LD_2RB---0RA", 2)
    self.assertFalse(bi_tm.is_wide())
    self.assertGreater(bi_tm.lower, Knuth10(442057658762000, 7))
    self.assertLessEqual(bi_tm.upper, Knuth10(442057658764000, 7))


if __name__ == "__main__":
  unittest.main()
