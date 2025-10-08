"""
Read CSV file where one column is the TM in StdText format.

See http://discuss.bbchallenge.org/t/standard-tm-text-format/60/28

Format looks like:
machine,status,decider,sigma,space,steps,machine_with_halt_transition
------_------,halt,LOOP1_params_6,1,1,1,1RZ---_------
0RA---_------,nonhalt,LOOP1_params_6,,,,
1RA---_------,nonhalt,LOOP1_params_6,,,,
0RB---_------,halt,LOOP1_params_6,1,2,2,0RB---_1RZ---
0RB---_0LA---,nonhalt,LOOP1_params_6,,,,
0RB---_1LA---,halt,LOOP1_params_6,1,2,4,0RB---_1LA1RZ
0RB---_1LA0LA,nonhalt,NGRAM_CPS_IMPL2_params_1_1_100,,,,
0RB---_1LA1LA,nonhalt,LOOP1_params_6,,,,
0RB---_1LA0RA,nonhalt,NGRAM_CPS_IMPL2_params_1_1_100,,,,
"""

import csv
import gzip
from pathlib import Path
from typing import TextIO

import Halting_Lib
from IO import TM_Record
from IO.Common import RecordLocateError
import TM_Enum


parse_tm = TM_Record.parse_tm

class Reader:
  def __init__(self, dest : Path | str | TextIO):
    self.infilename : Path | None
    self.infile : TextIO | None
    if isinstance(dest, (Path, str)):
      self.infilename = Path(dest)
      self.infile = None
      self.reader = None
    else:
      self.infilename = None
      self.infile = dest
      self.reader = csv.DictReader(self.infile)

  def __enter__(self):
    if self.infilename:
      if ".gz" in self.infilename.suffixes:
        self.infile = gzip.open(self.infilename, "rt")
      else:
        self.infile = open(self.infilename, "r")
      self.reader = csv.DictReader(self.infile)
    return self

  def __exit__(self, *args):
    if self.infilename:
      self.infile.close()

  def read_record(self) -> TM_Record:
    try:
      row = next(self.reader)
      tm_str = row["machine_with_halt_transition"]
      if not tm_str:
        tm_str = row["machine"]
      tm = parse_tm(tm_str)
      tm_enum = TM_Enum.TM_Enum(tm, allow_no_halt = False)
      tm_record = TM_Record.TM_Record(tm_enum = tm_enum)
      match row["status"]:
        case "halt":
          Halting_Lib.set_halting(tm_record.proto.status,
                                  int(row["steps"]), int(row["sigma"]),
                                  None, None)
        case "nonhalt":
          Halting_Lib.set_not_halting(tm_record.proto.status)
      return tm_record
    except StopIteration:
      return None

  def skip_record(self) -> bool:
    try:
      next(self.reader)
      return True
    except StopIteration:
      return False

  def __iter__(self):
    tm_record = self.read_record()
    while tm_record:
      yield tm_record
      tm_record = self.read_record()


def load_record(filename : Path, record_num : int) -> TM_Record:
  """Load one record from a filename."""
  with Reader(filename) as reader:
    for _ in range(record_num):
      reader.skip_record()
    rec = reader.read_record()
    if rec:
      return rec
    else:
      raise RecordLocateError(f"File {filename} does not contain record # {record_num}")
