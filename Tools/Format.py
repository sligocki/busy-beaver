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
    # Note, these last 2 are only valid if condition is halt
    self.SYMBOLS     = field_data(6, float)
    self.STEPS       = field_data(7, float)

class tests_container:
  def __init__(self):
    self.ALL           = lambda x: True
    self.IS_HALT       = lambda x: x == 0
    self.IS_INFINITE   = lambda x: x == 4
    self.IS_UNKNOWN    = lambda x: x in [1, 2]
    self.IS_OVER_TAPE  = lambda x: x == 1
    self.IS_OVER_STEPS = lambda x: x == 2
    self.IS_ERROR      = lambda x: x == -1

FIELD = fields_container()
TEST = tests_container()
