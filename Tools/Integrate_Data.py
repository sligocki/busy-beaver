#! /usr/bin/env python
from Format import FIELD, TEST


import sys

usage = "Integrate_Data.py input_filename halt_filename infinite_filename unknown_filename error_filename"

input_file    = file(sys.argv[1], "r")
halt_file     = file(sys.argv[2], "a")
infinite_file = file(sys.argv[3], "a")
unknown_file  = file(sys.argv[4], "w")
error_file    = file(sys.argv[5], "a")

for line in input_file:
  # Split each line by white charactor separation into fields
  fields = line.split()
  # The condition field describes whether the program halts, is provably infinite, unknown or error
  condition = FIELD.CONDITION.type(fields)
  if TEST.IS_HALT(condition):
    halt_file.write(line)
  elif TEST.IS_INFINITE(condition):
    infinite_file.write(line)
  elif TEST.IS_UNKNOWN(condition):
    unknown_file.write(line)
  else:
    error_file.write(line)

input_file.close()
halt_file.close()
infinite_file.close()
unknown_file.close()

if error_file.tell() == 0:
  error_file.close()
  rm(error_file)

rm(input_file)
