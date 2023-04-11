"""
Standard one-line TM format.

See http://discuss.bbchallenge.org/t/standard-tm-text-format/60/28

Format looks like:
1RB---_1LB0LB
1RB1LC_1RC1RB_1RD0LE_1LA1LD_1RZ0LA
1RB2LA1RA1RA_1LB1LA3RB1RZ
"""

import Halting_Lib
import IO
from IO import TM_Record
from Macro import Turing_Machine
import TM_Enum


parse_ttable = TM_Record.parse_ttable
parse_tm = TM_Record.parse_tm

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
    self.outfile.write(tm_record.tm().ttable_str())
    halt_status = tm_record.proto.status.halt_status
    if halt_status.is_halting:
      self.outfile.write(f" Halt {Halting_Lib.get_big_int(halt_status.halt_steps)} {Halting_Lib.get_big_int(halt_status.halt_score)}")
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
