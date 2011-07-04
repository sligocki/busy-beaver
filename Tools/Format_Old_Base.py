#
# Format_Old_Base.py
#
"""
Contains old Busy Beaver output file format.

FIELD: functions to retreive field data from an outfile line.
TEST:  functions to test BB related parameters (currently exit condition).
"""

def _field_data(num, type_func):
  """Field retreival generator."""
  def get_field(line):
    """Retreives specified field from line."""
    fields = line.split()
    return type_func(fields[num])
  return get_field

# Line in data file is formatted like this
# m# states symbols tape_length max_steps end_condition [symbols steps]
class _fields_container:
  def __init__(self):
    self.MACHINE_NUM = _field_data(0, int)
    self.NUM_STATES  = _field_data(1, int)
    self.NUM_SYMBOLS = _field_data(2, int)
    self.TAPE_LENGTH = _field_data(3, int)
    self.MAX_STEPS   = _field_data(4, int)
    self.CONDITION   = _field_data(5, int)
    # If Condition is halt or unknown:
    self.SYMBOLS     = _field_data(6, int)
    self.STEPS       = _field_data(7, int)
    # If Condition is infinte:
    self.INF_TYPE    = _field_data(6, int)

class _tests_container:
  def __init__(self):
    self.ALL           = lambda x: True
    self.IS_HALT       = lambda x: x == 0
    self.IS_INFINITE   = lambda x: x == 4
    self.IS_UNKNOWN    = lambda x: x in [1, 2]
    self.IS_OVER_TAPE  = lambda x: x == 1
    self.IS_OVER_STEPS = lambda x: x == 2
    # Note, these should never actually appear in program outputs at time of
    # writing (Dec 26, 2005) unless major error occured.
    self.IS_UNDEFINED  = lambda x: x == 3
    self.IS_ERROR      = lambda x: x == -1

FIELD = _fields_container()
TEST = _tests_container()

# Module user should not access these objects.
del _field_data, _fields_container, _tests_container
