"""
Turing Machine tape which compresses repeating symbols.

Combined with the k-block macro machine, this is very powerful compression.
Combined with an automated prover, this can prove Xmas Trees.
"""

class Infinity(object):
  """An identifier of infinity, only to be used for comparison purposes. A single object class."""
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

class Repeated_Symbol:
  """Slice of tape with repatitions."""
  def __init__(self, symbol, number_of_repetitions):
    self.symbol = symbol
    self.num = number_of_repetitions
  def __repr__(self):
    return "%s^%s" % (str(self.symbol), str(self.num))
  def __eq__(self, other):
    return isinstance(other, Repeated_Symbol) and \
           self.symbol == other.symbol and self.num == other.num
  def copy(self):
    return Repeated_Symbol(self.symbol, self.num)

class Chain_Tape:
  """Stores the turing machine tape with repetition compression."""
  def init(self, init_symbol, init_dir):
    self.dir = init_dir
    self.tape = [[], []]
    self.tape[0].insert(0, Repeated_Symbol(init_symbol, INF))
    self.tape[1].insert(0, Repeated_Symbol(init_symbol, INF))
    # Measures head displacement from initial position
    self.displace = 0
  def __repr__(self):
    if self.dir:  dir = " -> "
    else:         dir = " <- "
    return repr(reverse(self.tape[0]))+dir+repr(self.tape[1])
  def copy(self):
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
    return self.tape[self.dir][0]
  def get_top_symbol(self):
    """Simply returns the current symbol"""
    return self.tape[self.dir][0].symbol
  def apply_single_move(self, new_symbol, dir):
    """Apply a single macro step.  del old symbol, push new one."""
    ## Delete old symbol
    stack = self.tape[self.dir]
    top = stack[0]
    if top.num is not INF:  # Don't decriment infinity
      top.num -= 1
      # If there are none left, remove from stack.
      if top.num == 0:
        stack.pop(0)
    ## Push new symbol
    stack = self.tape[not dir]
    top = stack[0]
    # If it is identical to the top symbol, combine them.
    if top.symbol == new_symbol:
      if top.num is not INF:
        top.num += 1
    # Otherwise, just add it seperately.
    else:
      stack.insert(0, Repeated_Symbol(new_symbol, 1))
    # Update direction
    self.dir = dir
    # Update head displacement
    if dir:
      self.displace += 1
    else:
      self.displace -= 1
  def apply_chain_move(self, new_symbol):
    """Apply a chain step which replaces an entire string of symbols.
    Returns the number of symbols replaced."""
    # Pop off old sequence
    num = self.tape[self.dir][0].num
    if num is INF:
      return INF
    self.tape[self.dir].pop(0)
    # Push on new one behind us
    stack = self.tape[not self.dir]
    top = stack[0]
    if top.symbol == new_symbol:
      if top.num is not INF:
        top.num += num
    else:
      stack.insert(0, Repeated_Symbol(new_symbol, num))
    # Update head displacement
    if dir:
      self.displace += num
    else:
      self.displace -= num
    return num
