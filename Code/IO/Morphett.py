"""
TM format used on http://morphett.info/turing/turing.html and commonly used in Googology posts. Convenient when >26 states or >10 symbols so StdText doesn't work.
"""

import gzip
from pathlib import Path

from IO import TM_Record
from Macro import Turing_Machine
import TM_Enum


DIRS = "lr"


class Writer:
  """Class to manage writing TMRecords to a file."""
  def __init__(self, outfilename : Path):
    self.outfilename = Path(outfilename)
    self.outfile = None

  def __enter__(self):
    if ".gz" in self.outfilename.suffixes:
      self.outfile = gzip.open(self.outfilename, "w")
    else:
      self.outfile = open(self.outfilename, "w")
    return self

  def __exit__(self, *args):
    self.outfile.close()


  def write_record(self, tm_record : TM_Record) -> None:
    tm = tm_record.tm()
    # Morphett uses _ for blank symbol.
    tm.symbols[0] = "_"
    for state_in in range(tm.num_states):
      for symbol_in in range(tm.num_symbols):
        trans = tm.get_trans_object(symbol_in, state_in)
        if trans.condition != Turing_Machine.UNDEFINED:
          if trans.condition == Turing_Machine.HALT:
            state_out = "halt"
          else:
            state_out = tm.states[trans.state_out]
          # Write out one quintuple per line.
          print(tm.states[state_in], tm.symbols[symbol_in],
                tm.symbols[trans.symbol_out], DIRS[trans.dir_out], state_out,
                file=self.outfile)

  def flush(self):
    self.outfile.flush()


class Reader:
  """Class to manage reading TMRecords from a file."""
  def __init__(self, infilename : Path):
    self.infilename = Path(infilename)
    self.infile = None

  def __enter__(self):
    if ".gz" in self.infilename.suffixes:
      self.infile = gzip.open(self.infilename, "r")
    else:
      self.infile = open(self.infilename, "r")
    return self

  def __exit__(self, *args):
    self.infile.close()

  def read_record(self) -> TM_Record:
    quints = []
    states = []
    symbols = ["_"]
    for line in self.infile:
      # Strip comments
      line = line.split(";")[0]
      # Ignore breakpoints
      line = line.replace("!", "")
      line = line.strip()
      if line:
        (state_in, symbol_in, symbol_out, dir_out, state_out) = line.split()
        if state_out.lower().startswith("halt"):
          state_out = -1
        dir_out = DIRS.find(dir_out)
        quints.append((state_in, symbol_in, symbol_out, dir_out, state_out))
        if state_in not in states:
          states.append(state_in)
        if symbol_in not in symbols:
          symbols.append(symbol_in)
    tm = Turing_Machine.tm_from_quintuples(quints, states, symbols)
    tm_enum = TM_Enum.TM_Enum(tm, allow_no_halt = False)
    tm_record = TM_Record.TM_Record(tm_enum = tm_enum)
    return tm_record

  def __iter__(self):
    yield self.read_record()


def load_record(filename : str, record_num : int) -> TM_Record:
  assert record_num == 0
  with Reader(filename) as reader:
    return reader.read_record()
