"""
New IO for Busy Beaver results.

It should be both shorter and more readable than the old format in IO_old.py.

Format looks like:
1RB ---  1LB 0LB | 1 Infinite CTL2 3 5
1RB 1RZ  1LB 1RA | 0 Halt 2 4

<transition table> | <log num> <category> <category specific attributes> ... [| <extended attributes>]
"""

import string
import sys

from Common import Exit_Condition
import Input_Machine
import Output_Machine

class IO_Error(Exception): pass

class Result(object):
  """Structuring of information in a result line."""
  def __init__(self):
    self.ttable = None          # a list of lists
    self.log_number = None      # an int or None
    self.category = None        # Halt, Infinite, Unknown, Undecided
    self.category_results = []  # a generic list of attributes
    self.extended_results = []  # a generic list of extended information

  def __str__(self):
    return "[IO.Result: %s ]" % str(self.__dict__)

  def write(self, out):
    """Write out a Result object result."""
    out.write(Output_Machine.display_ttable(self.ttable))
    out.write(" | %r %s" % (self.log_number, Exit_Condition.name(self.category)))
    self.write_list(self.category_results, out)
    if self.extended_results:
      out.write(" |")
      self.write_list(self.extended_results, out)
    out.write("\n")

  def write_list(self, objs, out):
    for obj in objs:
      out.write(" %s" % self.str_generic(obj))

  def read(self, line):
    """Read a result off of a line from a file."""
    parts = line.split("|", 2)
    self.ttable = Input_Machine.read_ttable(parts[0])
    if len(parts) >= 2:
      subparts = parts[1].split()  # Split by whitespace
      try:
        self.log_number = int(subparts[0])
      except ValueError:
        self.log_number = None
      # TODO(shawn): There probably need to be evaluated.
      self.category = subparts[1]
      self.category_results = self.read_list(subparts[2:])
    if len(parts) >= 3:
      self.extended_results = self.read_list(parts[2].split())

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
      assert isinstance(obj, (int, long, float))
      return str(obj)

  def read_generic(self, s):
    """Read generic structure from string."""
    if s[0] in string.digits:
      return int(s)
    else:
      return s

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
    self.input_file  = input_file
    self.output_file = output_file
    self.log_number  = log_number
    self.flush_each  = not compressed

  def write_Result(self, result):
    """New interface for writing a Result object."""
    result.write(self.output_file)

    if self.flush_each:
      # Flushing every machine is expensive
      self.output_file.flush()

  def read_Result(self):
    """"New interface for reading a Result object."""
    line = self.input_file.readline()
    if line.strip():
      result = Result()
      result.read(line)
      return result

  # Allow iteration through input_file machines.
  def __iter__(self):
    return self
  def next(self):
    result = self.read_Result()
    if result:
      return result
    else:
      raise StopIteration


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
      result = Result()
      result.ttable = machine_TTable
      result.log_number = log_number
      result.category = results[0]
      result.category_results = results[1:]
      result.extended_results = old_results

      self.write_Result(result)

  def read_result(self):
    """Legacy interface used by IO_old to read a single result."""
    if self.input_file:
      result = self.read_Result()
      if result:
        return (0, len(result.ttable[0]), len(result.ttable), -1, -1,
                [result.category] + result.category_results,
                result.ttable, result.log_number, result.extended_results)


def load_TTable_filename(filename, line_num = 1):
  """Load a transition table from a filename w/ optional line number."""
  infile = open(filename, "r")
  TTable = load_TTable(infile, line_num)
  infile.close()
  return TTable

def load_TTable(infile, line_num = 1):
  """Load a transition table from a file w/ optional line number."""
  if line_num < 1:
    raise Exception, "load_TTable: line_num must be >= 1"
  while line_num > 1:
    if not infile.readline():
      raise Exception, "Not enough lines in file"
    line_num -= 1
  line = infile.readline()
  result = Result()
  result.read(line)
  return result.ttable

def test():
  from StringIO import StringIO
  global s
  s = StringIO()
  io = IO(s, s)
  io.write_result_raw(8, 2, 2, -1, -1, [Exit_Condition.HALT, 3, 6],
                      [[(1, 1, 1), (1, 1, -1)], [(1, 0, 1), (1, 1, 0)]],
                      13, ["Time_Out", 2, 2])
  print s.getvalue()
  s.seek(0)
  print io.read_result()
