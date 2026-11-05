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


if __name__ == "__main__":
  unittest.main()
