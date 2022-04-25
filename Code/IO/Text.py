"""
Text IO for Busy Beaver results.

Format looks like:
1RB ---  1LB 0LB | 1 Infinite CTL2 3 5
1RB 1RZ  1LB 1RA | 0 Halt 2 4

<transition table> | <log num> <category> <category specific attributes> ... [| <extended attributes>]
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

import io_pb2


inf_reason2str = {
  io_pb2.INF_UNSPECIFIED: "",
  io_pb2.INF_MACRO_STEP: "Repeat_in_Place",
  io_pb2.INF_CHAIN_STEP: "Chain_Move",
  io_pb2.INF_PROOF_SYSTEM: "Proof_System",
  io_pb2.INF_REVERSE_ENGINEER: "Reverse_Engineer",
  io_pb2.INF_LIN_RECUR: "Lin_Recur",
  io_pb2.INF_CTL: "CTL",
}
str2inf_reason = {s: inf_reason for (inf_reason, s) in inf_reason2str.items()}


SYMBOLS_DISPLAY = string.digits
DIRS_DISPLAY = "LRS"
STATES_DISPLAY = string.ascii_uppercase[:7]
def display_ttable(table):
  """Pretty print the ttable."""
  s = ""
  for row in table:
    for cell in row:
      if cell[0] == -1:
        s += "--- "
      else:
        symbol = SYMBOLS_DISPLAY[cell[0]]
        dir = DIRS_DISPLAY[cell[1]]
        state = STATES_DISPLAY[cell[2]] if cell[2] >= 0 else "Z"
        s += "%c%c%c " % (symbol, dir, state)
    s += " "
  return s.strip()

def read_ttable(line):
  """Read transition table given a string representation."""
  ttable = []
  rows = line.strip().split("  ")
  for row in rows:
    cells = row.split()
    ttable_row = []
    for cell in cells:
      assert len(cell) == 3, (cell, row, rows, line)
      if cell == "---":
        ttable_row.append((-1, 0, -1))
      else:
        symb_out = SYMBOLS_DISPLAY.find(cell[0])
        dir_out = DIRS_DISPLAY.find(cell[1])
        state_out = STATES_DISPLAY.find(cell[2])
        assert symb_out >= 0
        assert dir_out in [0, 1]
        assert state_out >= -1
        ttable_row.append((symb_out, dir_out, state_out))
    ttable.append(ttable_row)
  return ttable

class Record(object):
  """Structuring of information in a Turing machine result line."""
  def __init__(self):
    self.ttable = None          # a list of lists
    self.log_number = None      # an int or None
    self.category = None        # Halt, Infinite, Unknown, Undecided
    self.category_reason = []   # a generic list of attributes
    self.extended = None        # Halt, Infinite, Unknown, Undecided (extended)
    self.extended_reason = []   # a generic list of attributes (extended)

  def __str__(self):
    return "[IO.Record: %s ]" % str(self.__dict__)

  def write(self, out):
    """Write out a Record object result."""
    out.write(display_ttable(self.ttable))
    if self.category != None:
      out.write(" | %r %s" % (self.log_number, Exit_Condition.name(self.category)))
      self.write_list(self.category_reason, out)
      if self.extended != None:
        out.write(" | %s" % Exit_Condition.name(self.extended))
        self.write_list(self.extended_reason, out)
    out.write("\n")

  def write_list(self, objs, out):
    for obj in objs:
      out.write(" %s" % self.str_generic(obj))

  def read(self, line):
    """Read a result off of a line from a file."""
    line = line.split("#")[0]  # Cleave off comment.

    parts = line.split("|", 2)
    self.ttable = read_ttable(parts[0])
    if len(parts) >= 2:
      subparts = parts[1].split()  # Split by whitespace
      try:
        self.log_number = int(subparts[0])
      except ValueError:
        self.log_number = None
      self.category = Exit_Condition.read(subparts[1])
      self.category_reason = self.read_list(subparts[2:])
    if len(parts) >= 3:
      subparts = parts[2].split()  # Split by whitespace
      self.extended = Exit_Condition.read(subparts[0])
      self.extended_reason = self.read_list(subparts[1:])

  def read_list(self, strs):
    res = []
    for s in strs:
      res.append(self.read_generic(s))
    return res

  def str_generic(self, obj):
    """Convert generic object to string."""
    # Note: Don't pass in strings which begin with digits or have spaces
    # TODO(shawn): Perhaps the asserts are expensive?
    if isinstance(obj, str):
      assert ' ' not in obj
      # Note: Turned this off so that IO_Convert works. Old format reads
      # everything as strings.
      #assert obj[0] not in string.digits
      return obj
    else:
      assert isinstance(obj, (int, float)), \
          "Object %r is invalid type %s" % (obj, type(obj))
      return str(obj)

  def read_generic(self, s):
    """Read generic structure from string."""
    if s[0] in string.digits:
      if "." in s:
        return float(s)
      else:
        return int(s)
    else:
      return s


class ReaderWriter(object):
  """
  Reads and writes Busy Beaver results:
    input_file  - file to read*
    output_file - file to write*
    log_number - optional log_number to mark results with when they have been
                 categorized as halting or infinite.
  """
  def __init__(self, input_file, output_file, log_number=None):
    assert input_file == None or isinstance(input_file, io.TextIOBase), type(input_file)
    assert output_file == None or isinstance(output_file, io.TextIOBase), type(output_file)
    self.input_file  = input_file
    self.output_file = output_file
    self.log_number = log_number

  def write_record(self, tm_record : TM_Record.TM_Record):
    assert isinstance(tm_record, TM_Record.TM_Record), tm_record

    io_record = Record()
    if self.log_number is not None:
      io_record.log_number = self.log_number
    io_record.ttable = TM_Record.unpack_ttable(tm_record.proto.tm.ttable_packed)

    if tm_record.is_unknown_halting():
      io_record.category = Exit_Condition.UNKNOWN

      unknown_info = tm_record.proto.filter.simulator.result.unknown_info
      unk_reason = unknown_info.WhichOneof("reason")
      if unk_reason is None:
        # If we haven't run this TM, there will not exist any unknown_info at all.
        reason = Exit_Condition.NOT_RUN
        args = ()
      elif unk_reason == "over_loops":
        reason = Exit_Condition.MAX_STEPS
        args = (unknown_info.over_loops.num_loops,)
      elif unk_reason == "over_tape":
        reason = Exit_Condition.OVER_TAPE
        args = (unknown_info.over_tape.compressed_tape_size,)
      elif unk_reason == "over_time":
        reason = Exit_Condition.TIME_OUT
        args = (unknown_info.over_time.elapsed_time_sec,)
      elif unk_reason == "over_steps_in_macro":
        reason = Exit_Condition.OVER_STEPS_IN_MACRO
        args = ()
      else:
        raise Exception(unknown_info)

      io_record.category_reason = (Exit_Condition.name(reason),) + args

    elif tm_record.is_halting():
      io_record.category = Exit_Condition.HALT
      io_record.category_reason = (
        Halting_Lib.get_big_int(tm_record.proto.status.halt_status.halt_score),
        Halting_Lib.get_big_int(tm_record.proto.status.halt_status.halt_steps))

    else:
      io_record.category = Exit_Condition.INFINITE
      reason_str = inf_reason2str[tm_record.proto.status.halt_status.inf_reason]

      if tm_record.is_unknown_quasihalting():
        quasihalt_info = ("Quasihalt_Not_Computed", "N/A")

      elif tm_record.is_quasihalting():
        quasihalt_info = (
          tm_record.proto.status.quasihalt_status.quasihalt_state,
          Halting_Lib.get_big_int(tm_record.proto.status.quasihalt_status.quasihalt_steps))

      else:
        quasihalt_info = ("No_Quasihalt", "N/A")

      io_record.category_reason = (reason_str,) + quasihalt_info

    io_record.write(self.output_file)

  def flush(self):
    self.output_file.flush()

  def read_record(self):
    """
    New interface for reading an IO.Record object.

    Returns the next result in input_file unless it reaches end of file or
    incorrectly formatted line, which returns None.
    """
    line = self.input_file.readline()
    if line.strip():
      result = Record()
      result.read(line)
      return result

  def __iter__(self):
    """
    Iterate through all records in input_file.

    Allows:
    >>> io = IO(infile, outfile)
    >>> for io_record in io:
    ...   # do something with io_record
    """
    for line in self.input_file:
      try:
        result = Record()
        result.read(line)
        yield result
      except:
        print(f"ERROR: While parsing line: {line}", file=sys.stderr)
        raise

  def write_result(self, machine_num, tape_length, max_steps, results,
                   machine, log_number = None, old_results = []):
    if log_number is None:
      log_number = self.log_number
    self.write_result_raw(machine_num, machine.num_states, machine.num_symbols,
                          tape_length, max_steps, results, machine.get_TTable(),
                          log_number, old_results)

  def write_result_raw(self, machine_num, num_states, num_symbols, tape_length,
                       max_steps, results, machine_TTable, log_number = None,
                       old_results = []):
    """Legacy interface used by IO_old to write a single result."""
    if self.output_file:
      result = Record()

      result.ttable = machine_TTable

      result.log_number = log_number
      try:
        result.category = results[0]
      except:
        result.category = None
      result.category_reason = results[1:]

      try:
        result.extended = old_results[0]
      except:
        result.extended = None
      result.extended_reason = old_results[1:]

      result.write(self.output_file)

  def read_result(self):
    """Legacy interface used by IO_old to read a single result."""
    if self.input_file:
      result = self.read_record()
      if result:
        return (0, len(result.ttable), len(result.ttable[0]), -1, -1,
                [result.category] + result.category_reason,
                result.ttable, result.log_number,
                [result.extended] + result.extended_reason)

class Reader:
  def __init__(self, infile, *, allow_no_halt = False):
    self.rw = ReaderWriter(input_file = infile, output_file = None)
    self.allow_no_halt = allow_no_halt

  def __iter__(self):
    for io_record in self.rw:
      tm = Turing_Machine.Simple_Machine(io_record.ttable)
      tm_enum = TM_Enum.TM_Enum(tm, allow_no_halt = self.allow_no_halt)
      tm_record = TM_Record.TM_Record(tm_enum = tm_enum)
      yield tm_record


def load_TTable_filename(filename, line_num = 1):
  """Load a transition table from a filename w/ optional line number."""
  with open(filename, "r") as infile:
    TTable = load_TTable(infile, line_num)
  return TTable

def load_TTable(infile, line_num = 1):
  """Load a transition table from a file w/ optional line number."""
  if line_num < 1:
    raise Exception("load_TTable: line_num must be >= 1")
  while line_num > 1:
    if not infile.readline():
      raise Exception("Not enough lines in file")
    line_num -= 1
  line = infile.readline()
  return parse_ttable(line)

def parse_ttable(ttable_str):
  result = Record()
  result.read(ttable_str)
  return result.ttable

def parse_tm(ttable_str):
  return Turing_Machine.Simple_Machine(parse_ttable(ttable_str))
