#! /usr/bin/env python3

import Halting_Lib

import unittest

import io_pb2


def set_get_big_int(value):
  big = io_pb2.BigInt()
  Halting_Lib.set_big_int(big, value)
  return Halting_Lib.get_big_int(big)

class SystemTest(unittest.TestCase):
  def test_big_int_success(self):
    self.assertEqual(set_get_big_int(0), 0)
    self.assertEqual(set_get_big_int(138), 138)
    self.assertEqual(set_get_big_int(1_000_000), 1_000_000)
    self.assertEqual(set_get_big_int(1_000_000_000_000), 1_000_000_000_000)
    self.assertEqual(set_get_big_int(1_000_000_000_000_000_000_000_000),
                     1_000_000_000_000_000_000_000_000)
    self.assertEqual(set_get_big_int(13**138), 13**138)

  def test_big_int_near_split(self):
    self.assertEqual(set_get_big_int(2**64 - 1), 2**64 - 1)
    self.assertEqual(set_get_big_int(2**64), 2**64)
    self.assertEqual(set_get_big_int(2**64 + 1), 2**64 + 1)

  def test_big_int_error(self):
    # Error cases
    with self.assertRaises(ValueError):
      set_get_big_int(-1)
    with self.assertRaises(TypeError):
      set_get_big_int(13.8)


if __name__ == "__main__":
  unittest.main()
