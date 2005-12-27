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
  def __init__(self, input_file, output_file):
    """
    Save file information.
    """
    self.input_file  = input_file
    self.output_file = output_file

  def write_result(self, machine_num, tape_length, max_steps, results, machine):
    """
    Writes a result.
    """
    if self.output_file:
      self.output_file.write("%d " % machine_num)

      self.output_file.write("%d " % machine.num_states)
      self.output_file.write("%d " % machine.num_symbols)

      self.output_file.write("%d " % tape_length)
      self.output_file.write("%.0f " % max_steps)

      for item in results:
        if type(item) == int:
          self.output_file.write("%d " % item)
        elif type(item) == float:
          self.output_file.write("%.0f " % item)
        else:
          self.output_file.write("%s " % item)

      self.output_file.write("%s " % machine.get_TTable());
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
        max_steps   = float(parts[4])

        results = [int(parts[5]),]
        index = 6
        for item in parts[6:]:
          if item[0] == "[":
            break
          else:
            results.append(item)
            index += 1

        results = tuple(results)

        machine_TTable = eval(string.join(parts[index:]))

        return_value = (machine_num, num_states, num_symbols,
                        tape_length, max_steps, results, machine_TTable)

    return return_value
