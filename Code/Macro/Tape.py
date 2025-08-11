"""
Turing Machine tape which compresses repeating symbols.

Combined with the k-block macro machine, this is very powerful compression.
Combined with an automated prover, this can prove Xmas Trees.
"""

import math
import sys

sys.path.append("..")
from Halting_Lib import big_int_approx_or_full_str

# Serves as numerical infinity
INF = math.inf

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

  def __eq__(self, other):
    return (isinstance(other, self.__class__) and
            other.symbol   == self.symbol     and
            other.num      == self.num        and
            other.id       == self.id)

  def __hash__(self):
    return self.symbol + self.num

  def to_string(self, html_format, full_reps):
    if html_format:
      return "%s<sup>%s</sup>" % (str(self.symbol),
                                  big_int_approx_or_full_str(self.num))
    else:
      return "%s^%s" % (str(self.symbol),
                        big_int_approx_or_full_str(self.num))

  def __repr__(self):
    return self.to_string(html_format=False, full_reps=False)

  def copy(self):
    return Repeated_Symbol(self.symbol, self.num, self.id)

class Chain_Tape(object):
  """Stores the turing machine tape with repetition compression."""
  # Total number of times tapes are copied. Copies are expensive.
  num_copies = 0
  def init(self, init_symbol, init_dir, options):
    self.dir = init_dir
    self.tape = [[], []]
    self.tape[0].append(Repeated_Symbol(init_symbol, INF))
    self.tape[1].append(Repeated_Symbol(init_symbol, INF))
    self.options = options

  def compressed_size(self):
    """Get compressed length of tape."""
    return len(self.tape[0]) + len(self.tape[1])

  def __eq__(self, other):
    return (isinstance(other, self.__class__) and
            other.dir      == self.dir        and
            other.tape     == self.tape)

  def __repr__(self):
    return self.print_with_state(None)

  def print_with_state(self, state):
    left_tape = " ".join(sym.to_string(self.options.html_format,
                                       self.options.full_reps)
                         for sym in self.tape[0])
    right_tape = " ".join(sym.to_string(self.options.html_format,
                                        self.options.full_reps)
                          for sym in reverse(self.tape[1]))

    if state is None:
      state_str = "-"
    else:
      state_str = state.print_with_dir(self.dir)

    if self.dir:
      dir_str = "%s>" % state_str
    else:
      dir_str = "<%s" % state_str

    if self.options.html_format:
      dir_str = "<b>%s</b>" % dir_str

    return left_tape + " " + dir_str + " " + right_tape


  def copy(self):
    Chain_Tape.num_copies += 1
    new = Chain_Tape()
    new.dir = self.dir
    s0 = [x.copy() for x in self.tape[0]]
    s1 = [x.copy() for x in self.tape[1]]
    new.tape = [s0, s1]
    new.options = self.options
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
    # Otherwise, just add it separately.
    else:
      half_tape.append(Repeated_Symbol(new_symbol, 1))
    # Update direction
    self.dir = new_dir

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
    return num
