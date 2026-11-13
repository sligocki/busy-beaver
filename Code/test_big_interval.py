import optparse
import os
import unittest

import IO
from Big_Interval import BigInterval, Knuth10, NotComparable
from Exp_Int import exp_int
from Macro import Simulator, Turing_Machine
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
    options.recursive = True
    options.exp_linear_rules = True
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
    opts, _ = parser.parse_args(["--exp-linear-rules", "--exp-meta-linear-rules", "--recursive"])
    opts.prover = True
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

    bi_ack = self._run_tm_nonzeros_bi("1RB3LB1RZ2RA_2LC3RB1LC2RA_3RB1LB3LC2RC", 2, max_loops=10000, max_steps_back=250)
    self.assertEqual(len(bi_ack.lower.args), 4)
    self.assertEqual(len(bi_ack.upper.args), 4)
    self.assertEqual(bi_ack.lower.args[1:], (0, 1, 1))
    self.assertEqual(bi_ack.upper.args[1:], (0, 1, 1))
    self.assertTrue(bi_ack.lower.args[0] <= 65534 <= bi_ack.upper.args[0])

  def test_nat_expr_approx_and_full_str_uses_big_interval(self):
    from NatExpr import approx_and_full_str, approx_or_full_str, big_interval_str

    self.assertEqual(big_interval_str(12345), "12_345")
    e = exp_int(2, 10000)
    self.assertEqual(big_interval_str(e), "[10↑ 3010, 10↑ 3012]")
    self.assertEqual(approx_or_full_str(e, max_chars=5), "[10↑ 3010, 10↑ 3012]")
    self.assertTrue(approx_and_full_str(e, max_chars=5).startswith("[10↑ 3010, 10↑ 3012] (_"))


if __name__ == "__main__":
  unittest.main()
