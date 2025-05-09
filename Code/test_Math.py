#! /usr/bin/env python3

from Math import *

import unittest


class MathTest(unittest.TestCase):
  def test_gcd(self):
    self.assertEqual(gcd(91, 169), 13)
    self.assertEqual(gcd(169, 91), 13)
    self.assertEqual(gcd(91, 170), 1)
    self.assertEqual(gcd(138, 138), 138)
    self.assertEqual(gcd(1, 813), 1)

    self.assertEqual(gcd(-43, 2), 1)
    self.assertEqual(gcd(7, 0), 7)
    self.assertEqual(gcd(11, -22), 11)

  def test_lcm(self):
    self.assertEqual(lcm(91, 169), 1183)
    self.assertEqual(lcm(169, 91), 1183)
    self.assertEqual(lcm(91, 170), 91*170)
    self.assertEqual(lcm(138, 138), 138)
    self.assertEqual(lcm(1, 813), 813)

  def test_int_pow(self):
    # Only valid for non-int-power bases (list skips 4, 8, 9)
    for n in [2, 3, 5, 6, 7, 10, 11]:
      for k in range(2, 12):
        self.assertEqual(int_pow(n**k), (n, k))

    self.assertEqual(int_pow(9**2), (3, 4))
    self.assertEqual(int_pow(13), (13, 1))
    self.assertEqual(int_pow(138), (138, 1))

  def test_prime_factor(self):
    self.assertEqual(prime_factor(1), [])
    self.assertEqual(prime_factor(11), [(11, 1)])
    self.assertEqual(prime_factor(77), [(7, 1), (11, 1)])
    self.assertEqual(prime_factor(49), [(7, 2)])
    self.assertEqual(prime_factor(12), [(2, 2), (3, 1)])

    self.assertEqual(prime_factor(3**10), [(3, 10)])
    self.assertEqual(prime_factor(2**5 * 3**4 * 13**3), [(2, 5), (3, 4), (13, 3)])

  def test_exp_mod(self):
    for b in range(2, 11):
      for m in range(2, 101):
        for k in range(100):
          self.assertEqual(exp_mod(b, k, m), pow(b, k, m))

    for k in range(3, 20):
      self.assertEqual(exp_mod(3, 2**(k-2) + 1, 2**k), 3)

  def test_prec_mult(self):
    self.assertEqual(prec_mult(10**10_000, 1.5), 15 * 10**9_999)
    # Note that we cannot multiply these directly!
    with self.assertRaises(OverflowError):
      10**10_000 * 1.5


if __name__ == '__main__':
  unittest.main()
