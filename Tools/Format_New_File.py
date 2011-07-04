#
# Format_New_File.py 
#
"""
Classes to support storing TMs and information about them.
"""

class field_data:
  def __init__(self, num, type_func):
    self.num = num
    self.type = type_func

# machine_num states symbols tape_length max_steps end_condition [symbols steps]
class fields_container:
  def __init__(self):
    self.LOG_NUM     = field_data(0, int)
    self.CONDITION   = field_data(1, str)
    # If Condition is halt or unknown:
    self.SYMBOLS     = field_data(6, int)
    self.STEPS       = field_data(7, int)
    # If Condition is infinte:
    self.INF_TYPE    = field_data(6, int)

class tests_container:
  def __init__(self):
    self.ALL           = lambda x: True
    self.IS_HALT       = lambda x: x == "Halt"
    self.IS_INFINITE   = lambda x: x == "Infinite"
    self.IS_UNKNOWN    = lambda x: x == "Unknown"
    # Note, these should never actually appear in program outputs at time of
    # writing (Dec 26, 2005).
    self.IS_UNDEFINED  = lambda x: x == "Undefined_Cell"
    self.IS_ERROR      = lambda x: x == -1

FIELD = fields_container()
TEST = tests_container()
