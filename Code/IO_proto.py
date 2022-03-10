"""
IO (via protobuf) for Busy Beaver results.

Manages writing and reading TMs and simulation/filter results based upon
protobuffers defined in io.proto.

Protobuffers are written using custom length-delimed sequential format. See ex:
  https://seb-nyberg.medium.com/length-delimited-protobuf-streams-a39ebc4a4565)
"""

import io
import struct

import io_pb2

class IO_Error(Exception): pass


def pack_trans(symbol, dir, state, is_newrow) -> int:
  if dir not in [0, 1]:
    dir = 0
  byte_int =  (symbol + 1) | ((state + 1) << 3) | (dir << 6) | (is_newrow << 7)
  return byte_int

def unpack_trans(byte_int : int):
  symbol = (byte_int & 0b111) - 1
  state = ((byte_int >> 3) & 0b111) - 1
  dir = (byte_int >> 6) & 0b1
  is_newrow = bool((byte_int >> 7) & 0b1)
  return symbol, dir, state, is_newrow


def pack_ttable(ttable) -> bytes:
  num_states = len(ttable)
  num_symbols = len(ttable[0])
  pack = bytearray(num_states * num_symbols)
  i = 0
  for row in ttable:
    is_newrow = True
    for cell in row:
      (symbol, dir, state) = cell
      pack[i] = pack_trans(symbol, dir, state, is_newrow)
      is_newrow = False
      i += 1
  return bytes(pack)

def unpack_ttable(pack : bytes):
  ttable = []
  for byte in pack:
    (symbol, dir, state, is_newrow) = unpack_trans(byte)
    if is_newrow:
      ttable.append([])
    ttable[-1].append((symbol, dir, state))
  return ttable


def create_record(ttable) -> io_pb2.TMRecord:
  """Create TMRecord protobuf based on a machine ttable."""
  tm_record = io_pb2.TMRecord()
  tm_record.tm.ttable_packed = pack_ttable(ttable)
  return tm_record


class Writer:
  """Class to manage writing TMRecords to a file."""
  def __init__(self, output_file : io.BufferedWriter):
    assert isinstance(output_file, io.BufferedWriter), type(input_file)
    self.outfile = output_file

  def write_record(self, tm_record : io_pb2.TMRecord):
    """Write TMRecord protobuf using length-delimited format."""
    # Serialize the protobuf into a bytes object
    pb_bytes = tm_record.SerializeToString()

    # Serialize length of pb_bytes.
    #   Use fixed 4 byte (L), little endian (<) encoding for this length.
    #   Note: 4 bytes limits us to 4GB for a single tm_record, which is
    #         twice the maximum possible Protobuf size.
    #   Note: We could consider using varint which would allow us to only use
    #         1 byte for pbs < 128 bytes, and 2 for < 16KB. But, unless
    #         protobufs are really small, this might not make a huge difference.
    len_bytes = struct.pack('<L', len(pb_bytes))

    # Write size followed by message
    self.outfile.write(len_bytes)
    self.outfile.write(pb_bytes)


class Reader:
  """Class to manage reading TMRecords from a file."""
  def __init__(self, input_file : io.BufferedReader):
    assert isinstance(input_file, io.BufferedReader), type(input_file)
    self.infile = input_file

  def read_record(self):
    """Read TMRecord protobuf using length-delimited format (written by `Writer`)."""
    # Read message length
    len_bytes = self.infile.read(4)
    if len(len_bytes) > 0:
      assert len(len_bytes) == 4
      pb_len = struct.unpack('<L', len_bytes)[0]

      # Read protobuf bytes
      pb_bytes = self.infile.read(pb_len)
      assert len(pb_bytes) == pb_len

      # Parse protobuf
      tm_record = io_pb2.TMRecord()
      tm_record.ParseFromString(pb_bytes)
      return tm_record

  def __iter__(self):
    """
    Iterate through all records in input_file.

    Allows:
    >>> reader = Reader(infile)
    >>> for tm_record in reader:
    ...   # do something with tm_record
    """
    while (tm_record := self.read_record()) != None:
      yield tm_record


def load_record(filename, record_num):
  """Load one record from a filename."""
  with open(filename, "rb") as infile:
    reader = Reader(infile)
    for index, tm_record in enumerate(reader):
      if index == record_num:
        return tm_record
  raise IO_Error("Not enough lines in file")

def load_TTable(filename, record_num):
  tm_record = load_record(filename, record_num)
  return unpack_ttable(tm_record.tm.ttable_packed)


if __name__ == "__main__":
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument("infile")
  parser.add_argument("record_num", nargs="?", type=int, default=0)
  args = parser.parse_args()

  tm_record = load_record(args.infile, args.record_num)
  print(tm_record)
