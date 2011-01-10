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
  
  @classmethod
  def name(cls, cond):
    if cond == Exit_Condition.ERROR:
      return "Error"
    elif cond == Exit_Condition.HALT:
      return "Halt"
    elif cond == Exit_Condition.OVER_TAPE:
      return "Over_Tape"
    elif cond == Exit_Condition.MAX_STEPS:
      return "Max_Steps"
    elif cond == Exit_Condition.UNDEF_CELL:
      return "Undefined_Cell"
    elif cond == Exit_Condition.INFINITE:
      return "Infinite"
    elif cond == Exit_Condition.TIME_OUT:
      return "Time_Out"
    else:
      raise Exception, "Invalid exit condition %r" % cond

HALT_TRANS = (1, 1, -1)
