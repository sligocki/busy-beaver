"""
Reader for converting from bbchallenge.org zip'd binary format into our format.

See: https://bbchallenge.org/method#format
"""

import struct
import zipfile

from IO.TM_Record import TM_Record
from Macro import Turing_Machine
import TM_Enum


class IO_Error(Exception): pass

# Global constants for this format.
_BYTES_HEADER = 30
_BYTES_PER_RECORD = 30


def unpack_trans_ints(trans_bytes : bytes):
  assert len(trans_bytes) == 3

  symbol = int(trans_bytes[0])
  dir_int = int(trans_bytes[1])
  # BBC uses state 0 for Halt. We use state -1 for Halt.
  state = int(trans_bytes[2]) - 1

  # BBC uses R = 0, L = 1
  if dir_int == 0:
    dir = Turing_Machine.RIGHT
  else:
    assert dir_int == 1, dir
    dir = Turing_Machine.LEFT

  if state == -1 and symbol == 0:
    # Undefined transition.
    return (None, None, None)

  return (symbol, dir, state)

def unpack_tm(tm_bytes : bytes) -> Turing_Machine.Simple_Machine:
  quints = []
  start = 0
  # Note: BBC TMs are hardcoded to be 5x2.
  for state_in in range(5):
    for symbol_in in range(2):
      (symbol_out, dir_out, state_out) = unpack_trans_ints(tm_bytes[start:start+3])
      quints.append((state_in, symbol_in, symbol_out, dir_out, state_out))
      start += 3
  return Turing_Machine.tm_from_quintuples(ttable)


class Writer:
  """Class to manage writing TMRecords to a file."""
  def __init__(self, outfilename : str):
    self.outfilename = outfilename
    self.outfile = None
    raise NotImplementedError

  def write_record(self, tm_record : TM_Record) -> None:
    raise NotImplementedError

  def flush(self):
    self.outfile.flush()


class Reader:
  """Class to manage reading TMRecords from a file."""
  def __init__(self, infilename : str):
    self.infilename = infilename
    self.infile = None

  def __enter__(self):
    self.zipfile = zipfile.ZipFile(self.infilename, "r")
    names = self.zipfile.namelist()
    assert len(names) == 1, names
    self.infile = self.zipfile.open(names[0])

    self._read_header()
    return self

  def __exit__(self, *args):
    self.infile.close()
    self.zipfile.close()


  def _read_header(self) -> None:
    # TODO: Actually read header? For now we just ignore it.
    # whence = 0 means (from the start).
    self.infile.seek(_BYTES_HEADER, 0)

  def read_record(self) -> TM_Record:
    tm_bytes = self.infile.read(_BYTES_PER_RECORD)
    if not tm_bytes:
      return None
    elif len(tm_bytes) != _BYTES_PER_RECORD:
      raise IO_Error("Unexpected EOF while reading data block "
                     f"(expected {_BYTES_PER_RECORD}, got {len(tm_bytes)})")

    tm = unpack_tm(tm_bytes)
    tm_enum = TM_Enum.TM_Enum(tm, allow_no_halt = False)
    return TM_Record(tm_enum = tm_enum)

  def skip_record(self) -> bool:
    """Skip ahead 1 record. Return False if no records left in file."""
    # whence = 1 means (from current position).
    pb_bytes = self.infile.seek(_BYTES_PER_RECORD, 1)
    return pb_bytes == _BYTES_PER_RECORD

  def get_tm(self, tm_num) -> TM_Record:
    # whence = 0 means (from the start).
    self.infile.seek(_BYTES_HEADER + tm_num * _BYTES_PER_RECORD, 0)
    return self.read_record()

  def __iter__(self):
    """
    Iterate through all records in input_file.

    Allows:
    >>> reader = Reader(infile)
    >>> for tm_record in reader:
    ...   # do something with tm_record
    """
    tm_record = self.read_record()
    while tm_record != None:
      yield tm_record
      tm_record = self.read_record()


def load_record(filename : str, record_num : int) -> TM_Record:
  """Load one record from a filename."""
  with Reader(filename) as reader:
    for _ in range(record_num):
      reader.skip_record()
    return reader.read_record()


class IndexReader:
  def __init__(self, db_filename, index_filename):
    self.db_reader = Reader(db_filename)
    self.index_filename = index_filename

  def __enter__(self):
    self.db_reader.__enter__()
    self.index_file = open(self.index_filename, "rb")

  def __exit__(self, *args):
    self.db_reader.__exit__(args)
    self.index_file.close()


  def __iter__(self):
    for index in self.indexes():
      yield self.db_reader.get_tm(index)

  def indexes(self):
    while True:
      n_bytes = self.index_file.read(4)
      if not n_bytes:
        return
      elif len(n_bytes) != 4:
        raise IO_Error("Unexpected EOF while reading block "
                       f"(expected 4 bytes, got {len(len_bytes)}).")
      # Big Endian (>), 4 bytes (L).
      yield struct.unpack(">L", n_bytes)[0]


class TextIndexReader:
  """Reader for Mateon's text index format."""
  def __init__(self, db_filename, index_filename):
    self.db_reader = Reader(db_filename)
    self.index_filename = index_filename

  def __enter__(self):
    self.db_reader.__enter__()
    self.index_file = open(self.index_filename, "r")

  def __exit__(self, *args):
    self.db_reader.__exit__(args)
    self.index_file.close()


  def __iter__(self):
    for line in self.index_file:
      index = int(line)
      yield self.db_reader.get_tm(index)
