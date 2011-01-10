"""
Shared constants and constructs.
"""

class Exit_Condition(object):
  """Basically an enum of Turing machine exit conditions."""
  ERROR = -1
  HALT = 0
  OVER_TAPE = 1
  MAX_STEPS = 2
  UNDEF_CELL = 3
  INFINITE = 4
  TIME_OUT = 5
  UNKNOWN = (OVER_TAPE, MAX_STEPS, TIME_OUT)

HALT_TRANS = (1, 1, -1)
