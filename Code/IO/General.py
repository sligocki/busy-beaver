"""
Generalized reader that can read from either Proto or Text format.
"""

import IO
from pathlib import Path


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
