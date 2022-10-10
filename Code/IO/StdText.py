"""
Standard one-line TM format.

See http://discuss.bbchallenge.org/t/standard-tm-text-format/60/28

Format looks like:
1RB---_1LB0LB
1RB1LC_1RC1RB_1RD0LE_1LA1LD_1RZ0LA
1RB2LA1RA1RA_1LB1LA3RB1RZ
"""

import io
import string
import sys

from Common import Exit_Condition
import Halting_Lib
import IO
from IO import TM_Record
from Macro import Turing_Machine
import TM_Enum


SYMBOLS_DISPLAY = string.digits
DIRS_DISPLAY = "LR"
STATES_DISPLAY = string.ascii_uppercase

def parse_ttable(line : str):
  """Read transition table given a string representation."""
  ttable = []
  rows = line.strip().split("_")
  num_states = len(rows)
  for row in rows:
    ttable_row = []
    for i in range(0, len(row), 3):
      trans_str = row[i:i+3]
      assert len(trans_str) == 3, trans_str
      if trans_str == "---":
        ttable_row.append((-1, 0, -1))
      else:
        symb_out = SYMBOLS_DISPLAY.find(trans_str[0])
        dir_out = DIRS_DISPLAY.find(trans_str[1])
        state_out = STATES_DISPLAY.find(trans_str[2])
        if state_out >= num_states:
          state_out = -1
        assert symb_out >= 0
        assert dir_out in [0, 1]
        assert state_out >= -1
        ttable_row.append((symb_out, dir_out, state_out))
    ttable.append(ttable_row)
  return ttable

def parse_tm(line : str) -> Turing_Machine.Simple_Machine:
  ttable = parse_ttable(line)
  return Turing_Machine.Simple_Machine(ttable)


class Writer:
  def __init__(self, outfilename : str):
    self.outfilename = outfilename
    self.outfile = None

  def __enter__(self):
    self.outfile = open(self.outfilename, "w")
    return self

  def __exit__(self, *args):
    self.outfile.close()

  def write_record(self, tm_record : TM_Record) -> None:
    self.outfile.write(tm_record.tm().ttable_string())
    self.outfile.write("\n")

  def flush(self):
    self.outfile.flush()


class Reader:
  def __init__(self, infilename : str):
    self.infilename = infilename
    self.infile = None

  def __enter__(self):
    self.infile = open(self.infilename, "r")
    return self

  def __exit__(self, *args):
    self.infile.close()

  def read_record(self):
    line = self.infile.readline()
    line = line.strip()
    if line:
      tm = parse_tm(line)
      tm_enum = TM_Enum.TM_Enum(tm, allow_no_halt = False)
      tm_record = TM_Record.TM_Record(tm_enum = tm_enum)
      return tm_record

  def skip_record(self):
    self.infile.readline()

  def __iter__(self):
    tm_record = self.read_record()
    while tm_record:
      yield tm_record
      tm_record = self.read_record()


def load_record(filename : str, record_num : int) -> TM_Record:
  """Load one record from a filename."""
  with Reader(filename) as reader:
    for _ in range(record_num):
      reader.skip_record()
    return reader.read_record()
