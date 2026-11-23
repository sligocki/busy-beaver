import pickle
import unittest

from Algebraic_Expression import Variable, VariableToExpression
from Exp_Int import exp_int, struct_eq
import Iterated_Expression as IE
from Iterated_Expression import Iterated_Expression, Iterated_Math, Iterated_Term, IteratedExprGaveUp
from Macro import Tape


class TestIteratedMath(unittest.TestCase):
  def setUp(self):
    self.x = Variable(0)
    self.expr_x = VariableToExpression(self.x)
    # A function that grows fast
    self.f1 = self.expr_x + 1
    self.f2 = self.expr_x * 2
    self.it1 = Iterated_Expression(self.f1, self.x, 1, 100)
    self.it2 = Iterated_Expression(self.f2, self.x, 1, 200)

  def test_addition_commutativity_two_iterated(self):
    sum1 = self.it1 + self.it2
    sum2 = self.it2 + self.it1

    self.assertIsInstance(sum1, Iterated_Math)
    self.assertIsInstance(sum2, Iterated_Math)
    self.assertEqual(len(sum1.terms), 2)
    self.assertEqual(len(sum2.terms), 2)
    # Both should have the same uparrow_size_approx
    self.assertEqual(sum1.uparrow_size_approx, sum2.uparrow_size_approx)
    # Both should format identically because terms are normalized and sorted by size
    self.assertEqual(str(sum1), str(sum2))
    self.assertTrue(struct_eq(sum1, sum2))

  def test_combine_like_terms(self):
    # Adding the same Iterated_Expression combines coefficients
    m = self.it1 + self.it1
    self.assertIsInstance(m, Iterated_Math)
    self.assertEqual(len(m.terms), 1)
    self.assertEqual(m.terms[0].coef, 2)
    self.assertEqual(m.terms[0].it_expr, self.it1)

    # Add another one
    m3 = m + self.it1
    self.assertEqual(len(m3.terms), 1)
    self.assertEqual(m3.terms[0].coef, 3)

  def test_addition_with_exp_int(self):
    ei = exp_int(2, 500)
    sum1 = self.it1 + ei
    sum2 = ei + self.it1

    self.assertIsInstance(sum1, Iterated_Math)
    self.assertIsInstance(sum2, Iterated_Math)
    self.assertTrue(struct_eq(sum1, sum2))
    self.assertEqual(str(sum1), str(sum2))

  def test_size_dominated_by_const_or_term(self):
    # Suppose const is an enormous ExpInt with arrow level 3, while it_expr has arrow level 2
    f = self.expr_x * 2
    # it_fast iterates 2*x, which gives tower (arr=2)
    it_tower = Iterated_Expression(self.f1, self.x, 1, 10)
    # create an Iterated_Expression with arr=3 (pentation)
    it_pent = Iterated_Expression(f, self.x, 1, 10)
    m = Iterated_Math([Iterated_Term(it_tower, 1)], const=it_pent)
    # uparrow_size_approx should reflect the larger it_pent
    self.assertEqual(m.uparrow_size_approx, it_pent.uparrow_size_approx)

  def test_subtraction_and_negation(self):
    m = self.it1 + 5
    neg_m = -m
    self.assertEqual(neg_m.terms[0].coef, -1)
    self.assertEqual(neg_m.const, -5)

    sub = self.it1 - 5
    self.assertEqual(sub.const, -5)

    sub_it = self.it1 - self.it2
    self.assertEqual(len(sub_it.terms), 2)

  def test_scalar_mul(self):
    m = (self.it1 + 3) * 4
    self.assertEqual(m.terms[0].coef, 4)
    self.assertEqual(m.const, 12)

    m_r = 4 * (self.it1 + 3)
    self.assertEqual(m_r.terms[0].coef, 4)
    self.assertEqual(m_r.const, 12)

  def test_divmod(self):
    m = 4 * self.it1 + 10
    q, r = divmod(m, 2)
    self.assertEqual(q.terms[0].coef, 2)
    self.assertEqual(q.const, 5)
    self.assertEqual(r, 0)

  def test_addition_size_dominance_with_exp_int(self):
    # Regression test: Adding a large ExpInt (arrow level 4) and a smaller
    # Iterated_Expression (arrow level 3) should be dominated by the ExpInt
    # regardless of addition order.
    f_arr2 = exp_int(2, self.expr_x)
    it_arr3 = Iterated_Expression(f_arr2, self.x, 1, 10)
    f_arr3 = Iterated_Expression(f_arr2, self.x, 1, self.expr_x)
    it_arr4 = Iterated_Expression(f_arr3, self.x, 1, 10)
    ei_arr4 = exp_int(2, it_arr4)

    sum1 = ei_arr4 + it_arr3
    sum2 = it_arr3 + ei_arr4
    self.assertEqual(sum1.uparrow_size_approx, ei_arr4.uparrow_size_approx)
    self.assertEqual(sum2.uparrow_size_approx, ei_arr4.uparrow_size_approx)
    self.assertEqual(sum1.approx_str(), ei_arr4.approx_str())
    self.assertEqual(sum2.approx_str(), ei_arr4.approx_str())

  def test_addition_size_dominance_two_iterated(self):
    f_arr2 = exp_int(2, self.expr_x)
    it_arr3 = Iterated_Expression(f_arr2, self.x, 1, 10)
    f_arr3 = Iterated_Expression(f_arr2, self.x, 1, self.expr_x)
    it_arr4 = Iterated_Expression(f_arr3, self.x, 1, 10)

    sum1 = it_arr4 + it_arr3
    sum2 = it_arr3 + it_arr4
    self.assertEqual(sum1.uparrow_size_approx, it_arr4.uparrow_size_approx)
    self.assertEqual(sum2.uparrow_size_approx, it_arr4.uparrow_size_approx)
    self.assertEqual(sum1.approx_str(), it_arr4.approx_str())
    self.assertEqual(sum2.approx_str(), it_arr4.approx_str())

  def test_tape_nonzeros_order_independence(self):
    # Regression test for tape.get_nonzeros() when tape contains mixed blocks:
    # an earlier block with high arrow size (ExpInt at level 4) followed by
    # a later block with lower arrow size (Iterated_Expression at level 3).
    # Tape.get_nonzeros() accumulates blocks sequentially; the final count
    # must not be underestimated or reduced to the size of the smaller block.
    f_arr2 = exp_int(2, self.expr_x)
    it_arr3 = Iterated_Expression(f_arr2, self.x, 1, 10)
    f_arr3 = Iterated_Expression(f_arr2, self.x, 1, self.expr_x)
    it_arr4 = Iterated_Expression(f_arr3, self.x, 1, 10)
    ei_arr4 = exp_int(2, it_arr4)

    # Order 1: Large block first, then small block
    tape1 = Tape.Chain_Tape()
    tape1.init(0, 0, None)
    tape1.tape[0].append(Tape.Repeated_Symbol(1, ei_arr4))
    tape1.tape[0].append(Tape.Repeated_Symbol(1, it_arr3))
    nonzeros1 = tape1.get_nonzeros(lambda s: s, 0)
    self.assertEqual(nonzeros1.uparrow_size_approx, ei_arr4.uparrow_size_approx)
    self.assertEqual(nonzeros1.approx_str(), ei_arr4.approx_str())

    # Order 2: Small block first, then large block
    tape2 = Tape.Chain_Tape()
    tape2.init(0, 0, None)
    tape2.tape[0].append(Tape.Repeated_Symbol(1, it_arr3))
    tape2.tape[0].append(Tape.Repeated_Symbol(1, ei_arr4))
    nonzeros2 = tape2.get_nonzeros(lambda s: s, 0)
    self.assertEqual(nonzeros2.uparrow_size_approx, ei_arr4.uparrow_size_approx)
    self.assertEqual(nonzeros2.approx_str(), ei_arr4.approx_str())

  def test_to_big_interval(self):
    bi1 = self.it1.to_BigInterval()
    self.assertEqual(bi1.lower.args, (101,))
    self.assertEqual(bi1.upper.args, (101,))

    bi2 = self.it2.to_BigInterval()
    self.assertEqual(str(bi2), str((self.expr_x.to_BigInterval({self.x: 2}) ** 200)))

    bi_math = (3 * self.it1 + 5).to_BigInterval()
    self.assertEqual(bi_math.lower.args, (308,))
    self.assertEqual(bi_math.upper.args, (308,))

    bi_sub = (self.it2 - self.it1).to_BigInterval()
    self.assertTrue(bi_sub.lower >= bi2.lower.div10())

    # Exponential step with negative offset and nested hyper-exponential step
    f_exp = exp_int(2, self.expr_x) - 3
    it_exp = Iterated_Expression(f_exp, self.x, 10, 100)
    bi_exp = it_exp.to_BigInterval()
    self.assertEqual(bi_exp.lower.args[1:], (98,))

    f_hyper = Iterated_Expression(exp_int(2, self.expr_x), self.x, 2, self.expr_x)
    it_hyper = Iterated_Expression(f_hyper, self.x, 10, 5)
    bi_hyper = it_hyper.to_BigInterval()
    self.assertEqual(len(bi_hyper.lower.args), 3)
    self.assertEqual(len(bi_hyper.upper.args), 3)
    self.assertEqual(bi_hyper.lower.args[2], bi_hyper.upper.args[2])
    self.assertGreaterEqual(bi_hyper.lower.args[2], 3)

  def test_legacy_unpickle_is_const(self):
    # Simulate pickles created before is_const was stored as an instance attribute.
    const_it = Iterated_Expression(self.f1, self.x, 1, 100)
    const_it.__dict__.pop("is_const", None)
    loaded_it = pickle.loads(pickle.dumps(const_it))
    self.assertTrue(loaded_it.is_const)
    self.assertTrue(loaded_it > 10)
    self.assertEqual(loaded_it.to_BigInterval().lower.args, (101,))

    y = Variable(1)
    non_const_it = Iterated_Expression(self.f1, self.x, VariableToExpression(y), 100)
    non_const_it.start_val.__dict__.pop("is_const", None)
    non_const_it.__dict__.pop("is_const", None)
    loaded_non_const_it = pickle.loads(pickle.dumps(non_const_it))
    self.assertFalse(loaded_non_const_it.is_const)

    const_math = 3 * self.it1 + 5
    const_math.terms[0].it_expr.__dict__.pop("is_const", None)
    const_math.__dict__.pop("is_const", None)
    loaded_math = pickle.loads(pickle.dumps(const_math))
    self.assertTrue(loaded_math.is_const)
    self.assertTrue(loaded_math > 10)
    self.assertEqual(loaded_math.to_BigInterval().lower.args, (308,))

    non_const_math = 3 * non_const_it + 5
    non_const_math.terms[0].it_expr.__dict__.pop("is_const", None)
    non_const_math.__dict__.pop("is_const", None)
    loaded_non_const_math = pickle.loads(pickle.dumps(non_const_math))
    self.assertFalse(loaded_non_const_math.is_const)

    # Legacy Iterated_Math format with (it_expr, coef, const) instead of terms.
    legacy_math = Iterated_Math(self.it1, 5, coef=3)
    del legacy_math.__dict__["terms"]
    del legacy_math.__dict__["is_const"]
    legacy_math.__dict__["it_expr"] = self.it1
    legacy_math.__dict__["coef"] = 3
    loaded_legacy = pickle.loads(pickle.dumps(legacy_math))
    self.assertTrue(loaded_legacy.is_const)
    self.assertTrue(struct_eq(loaded_legacy, const_math))

  def test_uparrow_size_approx_const_expression_reps(self):
    from Algebraic_Expression import ConstantToExpression

    reps_expr = ConstantToExpression(3066)
    it = Iterated_Expression(exp_int(2, self.expr_x), self.x, 8, reps_expr)
    approx = it.uparrow_size_approx
    self.assertIsInstance(approx[1], (int, float))
    m = Iterated_Math([Iterated_Term(it, 1)], 100)
    self.assertEqual(m.uparrow_size_approx, approx)

  def test_mul_with_exp_int_and_expression(self):
    ei = exp_int(2, 1000)
    m = self.it1 + 3

    prod1 = m * ei
    prod2 = ei * m
    self.assertIsInstance(prod1, Iterated_Math)
    self.assertTrue(struct_eq(prod1, prod2))
    self.assertTrue(struct_eq(prod1.terms[0].coef, ei))
    self.assertTrue(struct_eq(prod1.const, 3 * ei))

    y = Variable(1)
    expr_y = VariableToExpression(y)
    prod_expr1 = m * expr_y
    self.assertIsInstance(prod_expr1, Iterated_Math)
    self.assertEqual(prod_expr1.terms[0].coef, expr_y)
    self.assertEqual(prod_expr1.const, 3 * expr_y)
    self.assertEqual(prod_expr1.variables(), {y})

    prod_expr2 = expr_y * m
    self.assertEqual(prod_expr2.variables(), {y})

  def test_truediv(self):
    ei = exp_int(3, 1000)
    m = (2 * ei) * self.it1 + (3 * ei - 1)
    q = m / 2
    self.assertIsInstance(q, Iterated_Math)
    self.assertTrue(struct_eq(q.terms[0].coef, (2 * ei) / 2))
    self.assertTrue(struct_eq(q.const, (3 * ei - 1) / 2))
    self.assertTrue(struct_eq(m / 1, m))

  def test_mult_func_apply_rep_with_iterated_math(self):
    from Macro.Rule_Func import Mult_Func

    # x -> 2x + 1 (m = 1)
    func2 = Mult_Func(self.x, min=1, coef=2, const=1)
    res2 = func2.apply_rep(self.it1 + 3, 1000)
    self.assertIsInstance(res2, Iterated_Math)
    ei2 = exp_int(2, 1000)
    self.assertTrue(struct_eq(res2.terms[0].coef, ei2))
    self.assertTrue(struct_eq(res2.const, 4 * ei2 - 1))
    self.assertIsNotNone(res2.to_BigInterval())

    # x -> 3x + 2 (m = 2)
    func3 = Mult_Func(self.x, min=1, coef=3, const=2)
    res3 = func3.apply_rep(self.it1 + 3, 1000)
    self.assertIsInstance(res3, Iterated_Math)
    ei3 = exp_int(3, 1000)
    self.assertTrue(struct_eq(res3.terms[0].coef, (2 * ei3) / 2))
    self.assertTrue(struct_eq(res3.const, (8 * ei3 - 2) / 2))
    self.assertIsNotNone(res3.to_BigInterval())

    # Also test starting directly from Iterated_Expression and num_reps=0
    res_it = func3.apply_rep(self.it1, 1000)
    self.assertIsInstance(res_it, Iterated_Math)
    res_zero = func3.apply_rep(5, 0)
    self.assertEqual(res_zero, 5)
    self.assertIsInstance(res_zero, int)

  def _enable_mod_iterated(self):
    prev = IE.ALLOW_MOD_ITERATED
    IE.ALLOW_MOD_ITERATED = True
    self.addCleanup(setattr, IE, "ALLOW_MOD_ITERATED", prev)

  def test_mod_disabled_by_default(self):
    self.assertFalse(IE.ALLOW_MOD_ITERATED)
    f = self.expr_x + 1
    it = Iterated_Expression(f, self.x, 2, 10)
    self.assertEqual(it % 1, 0)
    with self.assertRaises(IteratedExprGaveUp):
      _ = it % 6

  def test_mod_linear_cycle(self):
    self._enable_mod_iterated()
    # f(x) = x + 1, start=2: f^N(2) = 2 + N
    f = self.expr_x + 1
    for n in range(10):
      it = Iterated_Expression(f, self.x, 2, n)
      self.assertEqual(it % 6, (2 + n) % 6)
    # Huge ExpInt num_reps: 2^100 % 6 == 4 -> (2 + 4) % 6 == 0
    it_big = Iterated_Expression(f, self.x, 2, exp_int(2, 100))
    self.assertEqual(it_big % 6, (2 + pow(2, 100, 6)) % 6)
    self.assertEqual(it_big % 1, 0)

  def test_mod_exp_with_small_start_warmup(self):
    self._enable_mod_iterated()
    # f(x) = 2^x starting at 0: 0, 1, 2, 4, 16, 65536, ...
    f = exp_int(2, self.expr_x)
    exact = [0, 1, 2, 4, 16, 65536]
    for m in (2, 3, 5, 7, 10, 18):
      for n, val in enumerate(exact):
        it = Iterated_Expression(f, self.x, 0, n)
        self.assertEqual(it % m, val % m, f"n={n}, m={m}")
    # For N >= 4, 2^^N % 10 == 6
    self.assertEqual(Iterated_Expression(f, self.x, 0, exp_int(2, 200)) % 10, 6)

  def test_mod_closure_modulus_larger_than_target(self):
    self._enable_mod_iterated()
    # f(x) = 2^x + 1 mod 7 requires closure modulus L = lcm(7, 3, 2) = 42
    f = exp_int(2, self.expr_x) + 1
    vals = [1]
    for _ in range(4):
      vals.append(2 ** vals[-1] + 1)
    for n, val in enumerate(vals):
      it = Iterated_Expression(f, self.x, 1, n)
      self.assertEqual(it % 7, val % 7, f"n={n}")
    # Check stability for large N (for n >= 3, 2^x + 1 mod 7 is fixed at 2)
    # Wait: vals = [1, 3, 9, 513, 2^513+1, ...]
    # 513 % 7 == 2; 513 % 3 == 0 -> (2^513 + 1) % 7 = 2^0 + 1 = 2; 513 % 2 == 1
    # -> 2^513+1 ≡ 1 (mod 2) -> (2^1+1)%3=0 -> fixed at 2!
    self.assertEqual(Iterated_Expression(f, self.x, 1, 100) % 7, 2)
    self.assertEqual(Iterated_Expression(f, self.x, 1, exp_int(2, 200)) % 7, 2)

  def test_mod_tower_with_period_3_orbit(self):
    self._enable_mod_iterated()
    # Regression test for Iterated_Expression.__mod__ assuming period 1.
    # Build the 12-level tower from 1RB0LD_1RC1RF_1LA1RG_0LC1LE_0RA0LA_1RE0RC_1RB1RZ_------:
    # q -> (-16 + 7*2^((-4 + 7*2^((-4 + 7*2^(... (8q+40) ...))/3))/3))/3
    # Mod 6, this has a 3-cycle: 4 -> 0 -> 2 -> 4.
    cur = 8 * self.expr_x + 40
    for c in [-4, 5, -8] * 3 + [-4, -4, -16]:
      cur = (c + 7 * exp_int(2, cur)) / 3

    expected_mod6 = [4, 0, 2]
    for n in range(9):
      it = Iterated_Expression(cur, self.x, 4, n)
      self.assertEqual(it % 6, expected_mod6[n % 3], f"n={n}")

    # Test with huge ExpInt num_reps for all residues mod 3
    for offset in range(3):
      reps = exp_int(2, 100) + offset  # 2^100 % 3 == 1
      it = Iterated_Expression(cur, self.x, 4, reps)
      self.assertEqual(it % 6, expected_mod6[(1 + offset) % 3], f"offset={offset}")

    # Test with nested Iterated_Expression as num_reps
    inner_reps = Iterated_Expression(
      cur, self.x, 4, exp_int(2, 100)
    )  # 2^100 % 3 == 1 -> inner ≡ 0 (mod 6) -> 0 (mod 3)
    outer = Iterated_Expression(cur, self.x, 4, inner_reps)
    self.assertEqual(outer % 6, expected_mod6[0])


if __name__ == "__main__":
  unittest.main()
