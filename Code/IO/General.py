"""
Generalized reader that can read from either Proto or Text format.
"""

from pathlib import Path
import re

import IO
from IO.TM_Record import parse_tm
from Macro import Turing_Machine


def guess_module(filename : Path):
  # Currently we depend upon filename suffixes to decide filetype.
  #
  # TODO-maybe: Look at first 4 bytes to make an educated guess perhaps.
  # For Text first 4 bytes will be "1RB " or more generally (3 ASCII values
  # + space). For Proto they will be a little endian encoding of a small
  # integer. So, for example, byte 4 == " " would be a good check for Text.

  filename = Path(filename)
  if ".pb" in filename.suffixes:
    return IO.Proto

  elif ".morphett" in filename.suffixes:
    return IO.Morphett

  else:
    return IO.StdText


def Reader(filename : Path, *, text_allow_no_halt : bool = False):
  return guess_module(filename).Reader(filename)

def load_tm(filename : Path, record_num : int) -> Turing_Machine.Simple_Machine:
  record = guess_module(filename).load_record(filename, record_num)
  return record.tm()

def get_tm(tm : str) -> Turing_Machine.Simple_Machine:
  """Load TM from string. Supports TM directly in StdText format, filename or filename:record_num."""
  if re.fullmatch(r"([0-9][LR][A-Z]|---|_)+", tm):
    # Parse literal TM.
    return parse_tm(tm)
  else:
    # If not literal TM, load from file.
    if ":" in tm:
      parts = tm.split(":")
      filename = Path(parts[0])
      record_num = int(parts[1])
    else:
      filename = Path(tm)
      record_num = 0
    return load_tm(filename, record_num)