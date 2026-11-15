#! /usr/bin/env python3

import sys
import unittest

from Common import condense_traceback_str


class CommonTest(unittest.TestCase):
  def test_condense_traceback_repeating_cycle(self):
    def f(n):
      return g(n + 1)

    def g(n):
      if n >= 200:
        raise RecursionError("maximum recursion depth exceeded")
      return f(n + 1)

    try:
      f(0)
    except RecursionError:
      tb_str = condense_traceback_str(*sys.exc_info())
      self.assertIn("[Previous 2 frame(s) repeated", tb_str)
      self.assertIn("RecursionError: maximum recursion depth exceeded", tb_str)
      # Should be concise (< 30 lines) despite 200 frames
      self.assertLess(len(tb_str.splitlines()), 30)

  def test_condense_traceback_no_cycle(self):
    try:
      _ = 1 / 0
    except ZeroDivisionError:
      tb_str = condense_traceback_str(*sys.exc_info())
      self.assertNotIn("repeated", tb_str)
      self.assertIn("ZeroDivisionError: division by zero", tb_str)


if __name__ == "__main__":
  unittest.main()
