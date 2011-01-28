"""
Shared constants and constructs.
"""

class Exit_Condition(object):
  """Basically an enum of Turing machine exit conditions."""
  # TODO(shawn): It'd be nice to convert these to strings or something less
  # cryptic. However, these constants have weasled there way throughout the
  # code. For example, they are in Turing_Machine_Sim.c, Macro_Machine.c and
  # Dual_Machine.c :/
  ERROR = -1
  HALT = 0
  UNDEF_CELL = 3
  INFINITE = 4

  # Generic unknown condition, we should move to this and add extra info as
  # reason text (Result.category_results).
  UNKNOWN = 2  # Make it redundant with MAX_STEPS for backwards compatibility.
  OVER_TAPE = 1
  MAX_STEPS = 2
  TIME_OUT = 5
  # Set of all unkown conditions
  UNKNOWN_SET = (UNKNOWN, OVER_TAPE, MAX_STEPS, TIME_OUT)
  
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
HALT_STATE = -1
