"""
Turing Machine tape which compresses repeating symbols.

Combined with the k-block macro machine, this is very powerful compression.
Combined with an automated prover, this can prove Xmas Trees.
"""

# Serves as numerical infinity
INF = "Inf"

# Useful Tool
def reverse(in_list):
  reversed_in_list = list(in_list)
  reversed_in_list.reverse()
  return reversed_in_list

class Stack(list):
  """Generic Stack class based on built-in list."""
  def pop(self):
    return list.pop(self, 0)
  def push(self, item):
    list.insert(self, 0, item)
  def copy(self):
    return Stack([x.copy() for x in self])

class Repeated_Symbol:
  """Slice of tape with repatitions."""
  def __init__(self, symbol, number_of_repetitions):
    self.symbol = symbol
    self.num = number_of_repetitions
  def __repr__(self):
    return "%s^%s" % (str(self.symbol), str(self.num))
  def copy(self):
    return Repeated_Symbol(self.symbol, self.num)

class Chain_Tape:
  """Stores the turing machine tape with repetition compression."""
  def init(self, init_symbol, init_dir):
    self.dir = init_dir
    self.tape = [Stack(), Stack()]
    self.tape[0].push(Repeated_Symbol(init_symbol, INF))
    self.tape[1].push(Repeated_Symbol(init_symbol, INF))
    # Measures head displacement from initial position
    self.displace = 0
  def __repr__(self):
    if self.dir:  dir = " -> "
    else:         dir = " <- "
    return `reverse(self.tape[0])`+dir+`self.tape[1]`
  def copy(self):
    new = Chain_Tape()
    new.dir = self.dir
    new.displace = self.displace
    s0 = self.tape[0].copy()
    s1 = self.tape[1].copy()
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
        stack.pop()
    ## Push new symbol
    stack = self.tape[not dir]
    top = stack[0]
    # If it is identical to the top symbol, combine them.
    if top.symbol == new_symbol:
      if top.num is not INF:
        top.num += 1
    # Otherwise, just add it seperately.
    else:
      stack.push(Repeated_Symbol(new_symbol, 1))
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
    self.tape[self.dir].pop()
    # Push on new one behind us
    stack = self.tape[not self.dir]
    top = stack[0]
    if top.symbol == new_symbol:
      if top.num is not INF:
        top.num += num
    else:
      stack.push(Repeated_Symbol(new_symbol, num))
    # Update head displacement
    if dir:
      self.displace += num
    else:
      self.displace -= num
    return num
