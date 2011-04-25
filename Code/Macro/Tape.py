"""
Turing Machine tape which compresses repeating symbols.

Combined with the k-block macro machine, this is very powerful compression.
Combined with an automated prover, this can prove Xmas Trees.
"""

import math

class Infinity(object):
  """An identifier of infinity, only to be used for comparison purposes.
  There is one instance 'INF' of this class."""
  def __cmp__(self, other):
    if isinstance(other, Infinity):
      return 0  # Inf == Inf
    else:
      return 1  # Inf > (anything other than Inf)
  def __repr__(self):
    return "Infinity()"
  def __str__(self):
    return "Inf"
# Serves as numerical infinity
INF = Infinity()

# Useful Tool
def reverse(in_list):
  reversed_in_list = list(in_list)
  reversed_in_list.reverse()
  return reversed_in_list

class Repeated_Symbol(object):
  """Slice of tape with repatitions."""
  def __init__(self, symbol, number_of_repetitions, id = None):
    self.symbol = symbol
    self.num = number_of_repetitions
    self.id = id
  
  def __repr__(self):
    if type(self.num) not in (int, long) or self.num < 1000000:
      num_string = str(self.num)
    else:
      num_string = "(~10^%.1f)" % math.log10(self.num)
    return "%s^%s" % (str(self.symbol), num_string)
  
  def copy(self):
    return Repeated_Symbol(self.symbol, self.num, self.id)

class Chain_Tape(object):
  """Stores the turing machine tape with repetition compression."""
  # Total number of times tapes are copied. Copies are expensive.
  num_copies = 0
  def init(self, init_symbol, init_dir):
    self.dir = init_dir
    self.tape = [[], []]
    self.tape[0].append(Repeated_Symbol(init_symbol, INF))
    self.tape[1].append(Repeated_Symbol(init_symbol, INF))
    # Measures head displacement from initial position
    self.displace = 0

  def __cmp__(self, other):
    return (isinstance(other, self.__class__) and
            other.dir      == self.dir        and
            other.tape     == self.tape       and
            other.displace == self.displace)
  
  def __repr__(self):
    return self.print_with_state(None)

  def print_with_state(self, state):
    retval = ""
    for sym in self.tape[0]:
      retval = retval + `sym` + " "

    if state is None:
      if self.dir:  dir = "-> "
      else:         dir = "<- "
      retval = retval + dir
    else:
      if self.dir:  dir = "%s> " % state.print_with_dir(self.dir)
      else:         dir = "<%s " % state.print_with_dir(self.dir)
      retval = retval + dir

    for sym in reverse(self.tape[1]):
      retval = retval + `sym` + " "

    return retval
    
  
  def copy(self):
    Chain_Tape.num_copies += 1
    new = Chain_Tape()
    new.dir = self.dir
    new.displace = self.displace
    s0 = [x.copy() for x in self.tape[0]]
    s1 = [x.copy() for x in self.tape[1]]
    new.tape = [s0, s1]
    return new
  
  def get_nonzeros(self, eval_symbol, state_value):
    """Return number of nonzero symbols on the tape."""
    n = state_value
    for dir in range(2):
      for block in self.tape[dir]:
        if block.num is not INF:
          n += eval_symbol(block.symbol)*block.num
    return n
  
  def get_top_block(self):
    """Simply returns the current symbol"""
    return self.tape[self.dir][-1]
  
  def get_top_symbol(self):
    """Simply returns the current symbol"""
    return self.tape[self.dir][-1].symbol
  
  def apply_single_move(self, new_symbol, new_dir):
    """Apply a single macro step.  del old symbol, push new one."""
    ## Delete old symbol
    half_tape = self.tape[self.dir]
    top = half_tape[-1]
    if top.num is not INF:  # Don't decriment infinity
      # If not infinity, decrement (delete one symbol)
      top.num -= 1
      # If there are none left, remove from the tape
      if top.num == 0:
        half_tape.pop()
    ## Push new symbol
    half_tape = self.tape[not new_dir]
    top = half_tape[-1]
    # If it is identical to the top symbol, combine them.
    if top.symbol == new_symbol:
      if top.num is not INF:
        top.num += 1
    # Otherwise, just add it seperately.
    else:
      half_tape.append(Repeated_Symbol(new_symbol, 1))
    # Update direction
    self.dir = new_dir
    # Update head displacement
    if new_dir:
      self.displace += 1
    else:
      self.displace -= 1
  
  def apply_chain_move(self, new_symbol):
    """Apply a chain step which replaces an entire string of symbols.
    Returns the number of symbols replaced."""
    # Pop off old sequence
    num = self.tape[self.dir][-1].num
    # Can't pop off infinite symbols, TM will never halt
    if num is INF:
      return INF
    self.tape[self.dir].pop()
    # Push on new one behind us
    half_tape = self.tape[not self.dir]
    top = half_tape[-1]
    if top.symbol == new_symbol:
      if top.num is not INF:
        top.num += num
    else:
      half_tape.append(Repeated_Symbol(new_symbol, num))
    # Update head displacement
    if self.dir:
      self.displace += num
    else:
      self.displace -= num
    return num
