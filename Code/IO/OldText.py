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
DIRS_DISPLAY = "LR"
STATES_DISPLAY = string.ascii_uppercase[:-1]  # Don't allow Z
def display_ttable(tm):
  """Pretty print the TM transition table."""
  s = ""
  for state_in in range(tm.num_states):
    for symbol_in in range(tm.num_symbols):
      trans = tm.get_trans_object(symbol_in, state_in)
      if trans.condition == Turing_Machine.UNDEFINED:
        s += "--- "
      else:
        symbol = SYMBOLS_DISPLAY[trans.symbol_out]
        dir = DIRS_DISPLAY[trans.dir_out]
        state = STATES_DISPLAY[trans.state_out] if trans.state_out >= 0 else "Z"
        s += "%c%c%c " % (symbol, dir, state)
    s += " "
  return s.strip()

class Record(object):
  """Structuring of information in a Turing machine result line."""
  def __init__(self):
    self.tm = None
    self.log_number = None      # an int or None
    self.category = None        # Halt, Infinite, Unknown, Undecided
    self.category_reason = []   # a generic list of attributes
    self.extended = None        # Halt, Infinite, Unknown, Undecided (extended)
    self.extended_reason = []   # a generic list of attributes (extended)

  def __str__(self):
    return "[IO.Record: %s ]" % str(self.__dict__)

  def write(self, out):
    """Write out a Record object result."""
    out.write(display_ttable(self.tm))
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
    io_record.tm = TM_Record.unpack_tm(tm_record.proto.tm.ttable_packed)

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


class Writer:
  def __init__(self, outfilename : str):
    self.outfilename = outfilename
    self.outfile = None

  def __enter__(self):
    self.outfile = open(self.outfilename, "w")
    self.rw = ReaderWriter(input_file = None, output_file = self.outfile)
    return self.rw

  def __exit__(self, *args):
    self.outfile.close()
