"""
IO (via protobuf) for Busy Beaver results.

Manages writing and reading TMs and simulation/filter results based upon
protobuffers defined in io.proto.

Protobuffers are written using custom length-delimed sequential format. See ex:
  https://seb-nyberg.medium.com/length-delimited-protobuf-streams-a39ebc4a4565
"""

import io
import struct

from IO.TM_Record import TM_Record

import io_pb2


class IO_Error(Exception): pass


class Writer:
  """Class to manage writing TMRecords to a file."""
  def __init__(self, outfilename : str):
    self.outfilename = outfilename
    self.outfile = None

  def __enter__(self):
    self.outfile = open(self.outfilename, "wb")
    return self

  def __exit__(self, *args):
    self.outfile.close()


  def write_record(self, tm_record : TM_Record) -> None:
    """Write TMRecord protobuf using length-delimited format."""
    # Serialize the protobuf into a bytes object
    pb_bytes = tm_record.proto.SerializeToString()

    # Serialize length of pb_bytes.
    #   Use fixed 4 byte (L), little endian (<) encoding for this length.
    #   Note: 4 bytes limits us to 4GB for a single tm_record, which is
    #         twice the maximum possible Protobuf size.
    #   Note: We could consider using varint which would allow us to only use
    #         1 byte for pbs < 128 bytes, and 2 for < 16KB. But, unless
    #         protobufs are really small, this might not make a huge difference.
    len_bytes = struct.pack("<L", len(pb_bytes))

    # Write size followed by message
    self.outfile.write(len_bytes)
    self.outfile.write(pb_bytes)

  def flush(self):
    self.outfile.flush()


class Reader:
  """Class to manage reading TMRecords from a file."""
  def __init__(self, infilename : str):
    self.infilename = infilename
    self.infile = None

  def __enter__(self):
    self.infile = open(self.infilename, "rb")
    return self

  def __exit__(self, *args):
    self.infile.close()


  def _read_message_len(self):
    len_bytes = self.infile.read(4)
    if len(len_bytes) > 0:
      if len(len_bytes) != 4:
        raise IO_Error("Unexpected EOF while reading length block "
                       f"(expected 4 bytes, got {len(len_bytes)}).")
      return struct.unpack("<L", len_bytes)[0]


  def read_record(self) -> TM_Record:
    """Read TMRecord protobuf using length-delimited format (written by `Writer`)."""
    pb_len = self._read_message_len()
    if pb_len != None:
      # Read protobuf bytes
      pb_bytes = self.infile.read(pb_len)
      if len(pb_bytes) != pb_len:
        raise IO_Error("Unexpected EOF while reading data block "
                       f"(expected {pb_len}, got {len(pb_bytes)})")

      # Parse protobuf
      tm_proto = io_pb2.TMRecord()
      tm_proto.ParseFromString(pb_bytes)
      tm_record = TM_Record(proto = tm_proto)
      return tm_record

  def skip_record(self) -> bool:
    """Skip ahead 1 record. Return False if no records left in file."""
    pb_len = self._read_message_len()
    if pb_len != None:
      # Skip ahead pb_len bytes.
      pb_bytes = self.infile.seek(pb_len, 1)
      return True
    return False

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
