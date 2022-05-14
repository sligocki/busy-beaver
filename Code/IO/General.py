"""
Generalized reader that can read from either Proto or Text format.
"""

from pathlib import Path

import IO
from Macro import Turing_Machine


# File types
PROTO = "PROTO"
TEXT  = "TEXT"

class Reader:
  def __init__(self, filename, *, text_allow_no_halt = False):
    self.filename = Path(filename)
    self.text_allow_no_halt = text_allow_no_halt

    # Currently we depend upon filename suffixes to decide filetype.
    #
    # TODO-maybe: Look at first 4 bytes to make an educated guess perhaps.
    # For Text first 4 bytes will be "1RB " or more generally (3 ASCII values
    # + space). For Proto they will be a little endian encoding of a small
    # integer. So, for example, byte 4 == " " would be a good check for Text.
    if ".pb" in self.filename.suffixes:
      self.type = PROTO
    else:
      self.type = TEXT

  def __enter__(self):
    if self.type == PROTO:
      self.file = open(self.filename, "rb")
      return IO.Proto.Reader(self.file)
    else:
      assert self.type == TEXT, self.type
      self.file = open(self.filename, "r")
      return IO.Text.Reader(self.file, allow_no_halt = self.text_allow_no_halt)

  def __exit__(self, *args):
    self.file.close()

def load_tm(filename : Path, record_num : int) -> Turing_Machine.Simple_Machine:
  filename = Path(filename)
  if ".pb" in filename.suffixes:
    record = IO.Proto.load_record(filename, record_num)
    return record.tm()
  else:
    line = record_num + 1
    ttable = IO.Text.load_TTable_filename(filename, line)
    return Turing_Machine.Simple_Machine(ttable)
