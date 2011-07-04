#
# Format_Old_File.py
#
"""
Old classes to support storing TMs and information about them.
"""

class field_data:
  def __init__(self, num, type_func):
    self.num = num
    self.type = type_func

# m# states symbols tape_length max_steps end_condition [symbols steps]
class fields_container:
  def __init__(self):
    self.MACHINE_NUM = field_data(0, int)
    self.NUM_STATES  = field_data(1, int)
    self.NUM_SYMBOLS = field_data(2, int)
    self.TAPE_LENGTH = field_data(3, int)
    self.MAX_STEPS   = field_data(4, int)
    self.CONDITION   = field_data(5, int)
    # If Condition is halt or unknown:
    self.SYMBOLS     = field_data(6, int)
    self.STEPS       = field_data(7, int)
    # If Condition is infinte:
    self.INF_TYPE    = field_data(6, int)

class tests_container:
  def __init__(self):
    self.ALL           = lambda x: True
    self.IS_HALT       = lambda x: x == 0
    self.IS_INFINITE   = lambda x: x == 4
    self.IS_UNKNOWN    = lambda x: x in [1, 2]
    self.IS_OVER_TAPE  = lambda x: x == 1
    self.IS_OVER_STEPS = lambda x: x == 2
    # Note, these should never actually appear in program outputs at time of
    # writing (Dec 26, 2005).
    self.IS_UNDEFINED  = lambda x: x == 3
    self.IS_ERROR      = lambda x: x == -1

FIELD = fields_container()
TEST = tests_container()
