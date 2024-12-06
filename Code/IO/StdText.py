"""
Standard one-line TM format.

See http://discuss.bbchallenge.org/t/standard-tm-text-format/60/28

Format looks like:
1RB---_1LB0LB
1RB1LC_1RC1RB_1RD0LE_1LA1LD_1RZ0LA
1RB2LA1RA1RA_1LB1LA3RB1RZ
"""

import gzip
from pathlib import Path
from typing import TextIO

import Halting_Lib
from IO import TM_Record
from IO.Common import RecordLocateError
from Macro import Turing_Machine
import TM_Enum

import io_pb2


inf_reason2str = {
  io_pb2.INF_UNSPECIFIED: "",
  io_pb2.INF_MACRO_STEP: "Repeat_in_Place",
  io_pb2.INF_CHAIN_STEP: "Chain_Move",
  io_pb2.INF_PROOF_SYSTEM: "Proof_System",
  io_pb2.INF_REVERSE_ENGINEER: "Reverse_Engineer",
  io_pb2.INF_LIN_RECUR: "Lin_Recur",
  io_pb2.INF_CTL: "CTL",
  io_pb2.INF_BACKTRACK: "Backtracking",
  io_pb2.INF_CPS: "CPS",
}


parse_tm = TM_Record.parse_tm

class Writer:
  def __init__(self, source : Path | str | TextIO):
    self.outfilename : Path | None
    self.outfile : TextIO | None
    if isinstance(source, (Path, str)):
      self.outfilename = Path(source)
      self.outfile = None
    else:
      self.outfile = source
      self.outfilename = None

  def __enter__(self):
    if self.outfilename:
      if ".gz" in self.outfilename.suffixes:
        self.outfile = gzip.open(self.outfilename, "w")
      else:
        self.outfile = open(self.outfilename, "w")
    return self

  def __exit__(self, *args):
    if self.outfilename:
      self.outfile.close()

  def write_record(self, tm_record : TM_Record) -> None:
    self.outfile.write(tm_record.tm().ttable_str())
    halt_status = tm_record.proto.status.halt_status
    if halt_status.is_halting:
      # Remove _ from int strings so that we can sort them with `sort`.
      steps_str = Halting_Lib.big_int_approx_str(
        Halting_Lib.get_big_int(halt_status.halt_steps)).replace("_", "")
      score_str = Halting_Lib.big_int_approx_str(
        Halting_Lib.get_big_int(halt_status.halt_score)).replace("_", "")
      self.outfile.write(f" Halt {steps_str} {score_str}")
    elif Halting_Lib.is_infinite(halt_status):
      self.outfile.write(f" Inf {inf_reason2str[halt_status.inf_reason]}")
    self.outfile.write("\n")

  def write_tm(self, tm : Turing_Machine.Simple_Machine) -> None:
    """Convenience method to just write a TM directly without wrapping it in a record."""
    self.outfile.write(tm.ttable_str())
    self.outfile.write("\n")

  def flush(self):
    self.outfile.flush()


class Reader:
  def __init__(self, dest : Path | str | TextIO):
    self.infilename : Path | None
    self.infile : TextIO | None
    if isinstance(dest, (Path, str)):
      self.infilename = Path(dest)
      self.infile = None
    else:
      self.infile = dest
      self.infilename = None

  def __enter__(self):
    if self.infilename:
      if ".gz" in self.infilename.suffixes:
        self.infile = gzip.open(self.infilename, "r")
      else:
        self.infile = open(self.infilename, "r")
    return self

  def __exit__(self, *args):
    if self.infilename:
      self.infile.close()

  def read_record(self) -> TM_Record:
    line = self.infile.readline()
    line = line.strip()
    if line:
      tm = parse_tm(line.split()[0])
      tm_enum = TM_Enum.TM_Enum(tm, allow_no_halt = False)
      tm_record = TM_Record.TM_Record(tm_enum = tm_enum)
      return tm_record

  def skip_record(self) -> bool:
    line = self.infile.readline()
    return line != ""

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
