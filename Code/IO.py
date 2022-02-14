#
# IO.py
#
"""
New IO for Busy Beaver results.

It should be both shorter and more readable than the old format in IO_old.py.

Format looks like:
1RB ---  1LB 0LB | 1 Infinite CTL2 3 5
1RB 1RZ  1LB 1RA | 0 Halt 2 4

<transition table> | <log num> <category> <category specific attributes> ... [| <extended attributes>]
"""

import io
import string
import sys
import time

from Common import Exit_Condition
import Input_Machine
import Output_Machine

class IO_Error(Exception): pass

class Record(object):
  """Structuring of information in a Turing machine result line."""
  def __init__(self):
    self.ttable = None          # a list of lists
    self.log_number = None      # an int or None
    self.category = None        # Halt, Infinite, Unknown, Undecided
    self.category_reason = []   # a generic list of attributes
    self.extended = None        # Halt, Infinite, Unknown, Undecided (extended)
    self.extended_reason = []   # a generic list of attributes (extended)
    self.io_time = 0.0

  def __str__(self):
    return "[IO.Record: %s ]" % str(self.__dict__)

  def write(self, out):
    """Write out a Record object result."""
    start_time = time.time()

    out.write(Output_Machine.display_ttable(self.ttable))
    if self.category != None:
      out.write(" | %r %s" % (self.log_number, Exit_Condition.name(self.category)))
      self.write_list(self.category_reason, out)
      if self.extended != None:
        out.write(" | %s" % Exit_Condition.name(self.extended))
        self.write_list(self.extended_reason, out)
    out.write("\n")

    end_time = time.time()
    self.io_time += (end_time - start_time)

  def write_list(self, objs, out):
    start_time = time.time()

    for obj in objs:
      out.write(" %s" % self.str_generic(obj))

    end_time = time.time()
    self.io_time += (end_time - start_time)

  def read(self, line):
    """Read a result off of a line from a file."""
    start_time = time.time()

    line = line.split("#")[0]  # Cleave off comment.

    parts = line.split("|", 2)
    self.ttable = Input_Machine.read_ttable(parts[0])
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

    end_time = time.time()
    self.io_time += (end_time - start_time)

  def read_list(self, strs):
    start_time = time.time()

    res = []
    for s in strs:
      res.append(self.read_generic(s))

    end_time = time.time()
    self.io_time += (end_time - start_time)

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
      return eval(s)
    else:
      return s

  def get_stats(self):
    return (self.io_time,)


class IO(object):
  """
  Reads and writes Busy Beaver results:
    input_file  - file to read*
    output_file - file to write*
    log_number - optional log_number to mark results with when they have been
                 categorized as halting or infinite.
    flush_each - should we flush output_file after each machine [Legacy]

    * if this is 'None' then the user doesn't intend to do this type of
      operation.
  """
  def __init__(self, input_file, output_file, log_number = None,
               compressed = True):
    assert input_file == None or isinstance(input_file, io.TextIOBase), type(input_file)
    assert output_file == None or isinstance(output_file, io.TextIOBase), type(output_file)
    self.input_file  = input_file
    self.output_file = output_file
    self.log_number  = log_number
    self.flush_each  = not compressed
    self.io_time = 0.0

  def write_record(self, result):
    """New interface for writing an IO.Record object."""
    start_time = time.time()

    if result.log_number == None:
      result.log_number = self.log_number
    result.write(self.output_file)

    if self.flush_each:
      # Flushing every machine is expensive
      self.output_file.flush()

    end_time = time.time()
    self.io_time += (end_time - start_time)

  def read_record(self):
    """
    New interface for reading an IO.Record object.

    Returns the next result in input_file unless it reaches end of file or
    incorrectly formatted line, which returns None.
    """
    start_time = time.time()

    line = self.input_file.readline()
    if line.strip():
      result = Record()
      result.read(line)

      end_time = time.time()
      self.io_time += (end_time - start_time)

      return result

    end_time = time.time()
    self.io_time += (end_time - start_time)

  def __iter__(self):
    """
    Iterate through all records in input_file.

    Allows:
    >>> io = IO(infile, outfile)
    >>> for io_record in io:
    ...   # do something with io_record
    """
    for line in self.input_file:
      result = Record()
      result.read(line)
      yield result

  def catch_error_iter(self):
    """
    Iterator that catches and prints exceptions to sys.stderr.

    Use this if you want your iteration to be robust to files with some
    badly formatted/corrupted lines.
    """
    for line in self.input_file:
      try:
        result = Record()
        result.read(line)
        yield result
      except Exception as e:
        print("IO Parsing error", repr(e), "while parsing line:", line,
              file=sys.stderr)
        yield None


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
    start_time = time.time()

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

      self.write_record(result)

    end_time = time.time()
    self.io_time += (end_time - start_time)

  def read_result(self):
    """Legacy interface used by IO_old to read a single result."""
    start_time = time.time()

    if self.input_file:
      result = self.read_record()
      if result:
        return (0, len(result.ttable), len(result.ttable[0]), -1, -1,
                [result.category] + result.category_reason,
                result.ttable, result.log_number,
                [result.extended] + result.extended_reason)

    end_time = time.time()
    self.io_time += (end_time - start_time)

  def get_stats(self):
    return (self.io_time,)

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

def parse_ttable(line):
  result = Record()
  result.read(line)
  return result.ttable

def test():
  from io import StringIO
  global s
  s = StringIO()
  io = IO(s, s)
  io.write_result_raw(8, 2, 2, -1, -1, [Exit_Condition.HALT, 3, 6],
                      [[(1, 1, 1), (1, 1, -1)], [(1, 0, 1), (1, 1, 0)]],
                      13, ["Time_Out", 2, 2])
  print(s.getvalue())
  s.seek(0)
  print(io.read_result())
