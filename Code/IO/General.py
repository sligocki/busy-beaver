"""
Generalized reader that can read from either Proto or Text format.
"""

from pathlib import Path

import IO
from Macro import Turing_Machine


def Reader(filename : Path, *, text_allow_no_halt : bool = False):
  # Currently we depend upon filename suffixes to decide filetype.
  #
  # TODO-maybe: Look at first 4 bytes to make an educated guess perhaps.
  # For Text first 4 bytes will be "1RB " or more generally (3 ASCII values
  # + space). For Proto they will be a little endian encoding of a small
  # integer. So, for example, byte 4 == " " would be a good check for Text.
  filename = Path(filename)
  if ".pb" in filename.suffixes:
    return IO.Proto.Reader(filename)
  else:
    return IO.StdText.Reader(filename)

def load_tm(filename : Path, record_num : int) -> Turing_Machine.Simple_Machine:
  filename = Path(filename)
  if ".pb" in filename.suffixes:
    record = IO.Proto.load_record(filename, record_num)
    return record.tm()
  else:
    record = IO.StdText.load_record(filename, record_num)
    return record.tm()
