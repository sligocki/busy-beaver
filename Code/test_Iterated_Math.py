import pickle
import unittest

from Algebraic_Expression import Variable, VariableToExpression
from Exp_Int import exp_int
from Iterated_Expression import Iterated_Expression, Iterated_Math, Iterated_Term
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
    self.assertEqual(sum1, sum2)

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
    self.assertEqual(sum1, sum2)
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
    self.assertEqual(loaded_legacy, const_math)


if __name__ == "__main__":
  unittest.main()
