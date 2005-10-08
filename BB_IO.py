"""
Does IO on Busy Beaver results (BB_IO class).
"""

import sys
import cPickle as pickle
import string

from BB_Machine import BB_Machine 

class BB_IO:
  """
  Reads and writes Busy Beaver results:
    input_file       - file to read*
    text_output_file - text file to write*
    data_output_file - data file to write*

    * if this is 'None' then the user doesn't intend to do this type of
      operation.
  """
  def __init__(self, input_file, text_output_file, data_output_file):
    """
    Save file information.
    """
    self.input_file       = input_file
    self.text_output_file = text_output_file
    self.data_output_file = data_output_file

  def writeResult(self, machine_num, tape_length, max_steps, results, machine):
    """
    Writes a result.
    """
    if self.text_output_file:
      self.text_output_file.write("%d " % machine_num)

      self.text_output_file.write("%d " % machine.num_states)
      self.text_output_file.write("%d " % machine.num_symbols)

      self.text_output_file.write("%d " % tape_length)
      self.text_output_file.write("%.0f " % max_steps)

      for item in results:
        if type(item) == int:
          self.text_output_file.write("%d " % item)
        elif type(item) == float:
          self.text_output_file.write("%.0f " % item)
        else:
          self.text_output_file.write("%s " % item)

      self.text_output_file.write("%s " % machine.getTTable());
      self.text_output_file.write("\n")
      self.text_output_file.flush()
      
    if self.data_output_file:
      pickle.dump(machine_num,
                  machine.num_states,
                  machine.num_symbols,
                  tape_length,
                  max_steps,
                  results,
                  machine,
                  self.data_output_file)

  def readResult(self):
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
