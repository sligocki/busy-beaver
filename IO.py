"""
Does IO of Busy Beaver results (IO class).
"""

import sys
import string

from Turing_Machine import Turing_Machine 

class IO:
  """
  Reads and writes Busy Beaver results:
    input_file  - file to read*
    output_file - text file to write*

    * if this is 'None' then the user doesn't intend to do this type of
      operation.
  """
  def __init__(self, input_file, output_file, log_number = None):
    """
    Save file information.
    """
    self.input_file  = input_file
    self.output_file = output_file
    self.log_number = log_number

  def write_result(self, machine_num, tape_length, max_steps, results,
                   machine, log_number = None, old_results = []):
    """
    Writes a result.
    """
    if log_number is None:
      log_number = self.log_number

    if self.output_file:
      self.output_file.write("%d " % machine_num)

      self.output_file.write("%d " % machine.num_states)
      self.output_file.write("%d " % machine.num_symbols)

      self.output_file.write("%d " % tape_length)
      self.output_file.write("%d " % max_steps)

      for item in results:
        if type(item) in [int, long]:
          self.output_file.write("%d " % item)
        elif type(item) == float:
          self.output_file.write("%.0f " % item)
        else:
          self.output_file.write("%s " % item)

      self.output_file.write("%s " % machine.get_TTable())

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
      self.output_file.flush()

  def read_result(self):
    """
    Reads a result.
    """

    return_value = None

    if self.input_file:
      cur_line = self.input_file.readline()

      if cur_line:
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
  while line_num > 1:
    infile.readline()
    line_num -= 1
  line = infile.readline()
  start = line.find("[[")
  end = line.find("]]", start) + len("]]")
  if start != -1 and end != -1:
    return eval(line[start:end])
  else:
    raise Exception, "Turing Machine not found in input file\n"
