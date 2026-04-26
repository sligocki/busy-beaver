#! /usr/bin/env python3
"""
Unit test for "TM_Enum.py".
"""

import unittest

import TM_Enum
from Time_Limit import TimeLimit


class TM_EnumTest(unittest.TestCase):
  def test_deepcopy_with_active_timer(self):
    """Regression: deepcopy must work when the machine's time_limit has a live
    threading.Timer. Python 3.14+ cannot deepcopy _contextvars.Context, which
    threading.Timer captures at construction time."""
    tm_enum = TM_Enum.blank_tm_enum(2, 2, first_1rb=True, allow_no_halt=False)
    tl = TimeLimit()
    tl.start(600.0)
    try:
      tm_enum.tm.time_limit = tl
      # enum_children calls copy.deepcopy(self) internally.
      children = list(tm_enum.enum_children(0, 1))
      self.assertGreater(len(children), 0)
    finally:
      tl.cancel()

  def test_deepcopy_fresh(self):
    """deepcopy of a TM_Enum with no active timer must also work."""
    tm_enum = TM_Enum.blank_tm_enum(2, 2, first_1rb=True, allow_no_halt=False)
    children = list(tm_enum.enum_children(0, 1))
    self.assertGreater(len(children), 0)
    # Each child should be a distinct object with a distinct TM.
    self.assertIsNot(children[0], tm_enum)
    self.assertIsNot(children[0].tm, tm_enum.tm)


if __name__ == "__main__":
  unittest.main()
