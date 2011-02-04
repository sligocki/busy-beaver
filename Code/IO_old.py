"""
Old IO for Busy Beaver results.

Format looks like:
6 2 2 -1 -1 4 Infinite [[(1, 1, 1), (-1, 0, -1)], [(1, 0, 1), (0, 0, 1)]] 
7 2 2 -1 -1 0 2 4 [[(1, 1, 1), (1, 1, -1)], [(1, 0, 1), (1, 1, 0)]] 
"""

import sys
import string

from Common import Exit_Condition
from Turing_Machine import Turing_Machine 

class IO_Error(Exception): pass

class IO:
  """
  Reads and writes Busy Beaver results:
    input_file  - file to read*
    output_file - text file to write*

    * if this is 'None' then the user doesn't intend to do this type of
      operation.
  """
  def __init__(self, input_file, output_file, log_number = None, compressed = True):
    """
    Save file information.
    """
    self.input_file  = input_file
    self.output_file = output_file
    self.log_number  = log_number
    self.compressed  = compressed

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
    """
    Writes a result.
    """
    if self.output_file:
      self.output_file.write("%d " % machine_num)
      self.output_file.write("%d " % num_states)
      self.output_file.write("%d " % num_symbols)
      self.output_file.write("%d " % tape_length)
      self.output_file.write("%d " % max_steps)

      for item in results:
        if type(item) in [int, long]:
          self.output_file.write("%d " % item)
        elif type(item) == float:
          self.output_file.write("%.0f " % item)
        else:
          self.output_file.write("%s " % item)

      self.output_file.write("%s " % machine_TTable)

      if log_number is not None and old_results:
        self.output_file.write("%d " % log_number)
      
        for item in old_results:
          if type(item) in [int, long]:
            self.output_file.write("%d " % item)
          elif type(item) == float:
            self.output_file.write("%.0f " % item)
          else:
            self.output_file.write("%s " % item)

      self.output_file.write("\n")
      if not self.compressed:
        # Flushing every machine is expensive
        self.output_file.flush()

  def read_result(self):
    """
    Reads a result.
    """

    return_value = None

    if self.input_file:
      cur_line = self.input_file.readline()

      cur_line = string.strip(cur_line)

      if cur_line:
        try:
          parts = cur_line.split()

          machine_num = int(parts[0])

          num_states  = int(parts[1])
          num_symbols = int(parts[2])

          tape_length = int(parts[3])
          max_steps   = int(parts[4])

          results = [int(parts[5])]

          index = 6
          for item in parts[6:]:
            if item[0] == "[":
              break
            else:
              results.append(item)
              index += 1
          results = tuple(results)

          machine_TTable = []
          for item in parts[index:]:
            machine_TTable.append(item)
            index += 1
            if len(item) >= 2 and item[-2:] == "]]":
              break
          machine_TTable = eval(string.join(machine_TTable))

          try:
            log_number = int(parts[index])
          except:
            log_number = None
          index += 1

          old_results = list(parts[index:])
        except:
          # Try to read a line that's just a ttable.
          machine_num = -1
          print repr(cur_line)
          machine_TTable = eval(cur_line)
          num_states = len(machine_TTable[0])
          num_symbols = len(machine_TTable)
          tape_length = -1
          max_steps = -1
          results = []
          log_number = -1
          old_results = []

        return_value = (machine_num, num_states, num_symbols, tape_length,
                        max_steps, results, machine_TTable, log_number,
                        old_results)

    return return_value

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
  return get_TTable_line(line)

def get_TTable_line(line):
  start = line.find("[[")
  end = line.find("]]", start) + len("]]")
  if start != -1 and end != -1:
    return eval(line[start:end])
  else:
    raise Exception, "Turing Machine not found in input file."
