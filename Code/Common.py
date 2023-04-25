"""
Shared constants and constructs.
"""

from fractions import Fraction

from Exp_Int import ExpInt


class GenContainer(object):
  """Generic container class"""
  def __init__(self, **args):
    for atr in args:
      self.__dict__[atr] = args[atr]

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
  # reason text (IO.Record.category_reason).
  UNKNOWN = 6
  OVER_TAPE = 1
  MAX_STEPS = 2
  TIME_OUT = 5
  NOT_RUN = 7
  OVER_STEPS_IN_MACRO = 8
  # Set of all unkown conditions
  UNKNOWN_SET = (UNKNOWN, OVER_TAPE, MAX_STEPS, TIME_OUT, NOT_RUN)

  names = { ERROR: "Error",
            HALT: "Halt",
            UNDEF_CELL: "Undefined_Cell",
            INFINITE: "Infinite",
            # TODO(shawn): Print out "Unknown" for all of these.
            UNKNOWN: "Unknown",
            OVER_TAPE: "Over_Tape",
            MAX_STEPS: "Max_Steps",
            TIME_OUT: "Time_Out",
            NOT_RUN: "Not_Run",
            OVER_STEPS_IN_MACRO: "Macro_Over_Steps",
            }
  condition_from_name = {name: cond for (cond, name) in names.items()}

  @classmethod
  def name(cls, cond):
    """Convert Exit_Conditions to strings."""
    return cls.names[cond]

  @classmethod
  def read(cls, name):
    """Read Exit_Condition strings into constants."""
    return cls.condition_from_name[name]

HALT_TRANS = (1, 1, -1)
HALT_STATE = -1

# Numeric helpers
def is_scalar(value):
  """Is this a "scalar" value? An integer or fraction in various formats."""
  return isinstance(value, (int, Fraction, ExpInt))
