#! /usr/bin/env python
#
# Categorizes each entree in the output of a filter into 1 of 3 files
# associated with this run:
#   1) Halt_file for machines proven to halt.
#   2) Infinite_file for machines proven to run infinitely.
#   3) Unknown_file for machines still uncategorized and of unknown type.
#   4) Error_file for machines with unexpected (weird) return conditions.
# Should be called automatically by 'update'.
#

from Format import FIELD, TEST

import sys, os

usage = "Integrate_Data.py input_filename halt_filename infinite_filename unknown_filename error_filename undecided_filename"

input_filename     = sys.argv[1];   input_file     = file(input_filename, "r")
halt_filename      = sys.argv[2];   halt_file      = file(halt_filename, "a")
infinite_filename  = sys.argv[3];   infinite_file  = file(infinite_filename, "a")
unknown_filename   = sys.argv[4];   unknown_file   = file(unknown_filename, "w")
error_filename     = sys.argv[5];   error_file     = file(error_filename, "a")
undecided_filename = sys.argv[6];   undecided_file = file(undecided_filename, "a")

# Error flag:
#   False means no unexpected (weird) entries.
#   True means at least one unexpected (weird) entry.
was_error = False

# Count output to each file type
num_halt      = 0
num_undecided = 0
num_infinite  = 0
num_unknown   = 0
num_error     = 0

for line in input_file:
  # Split each line by white charactor separation into fields.
  fields = line.split()
  # The condition field describes whether the program halts, is provably
  # infinite, unknown or error
  condition = FIELD.CONDITION.type(fields[FIELD.CONDITION.num])
  # 'line' halts.
  if TEST.IS_HALT(condition):
    halt_file.write(line)
    num_halt += 1
  # 'line' is proven infinite.
  elif TEST.IS_INFINITE(condition):
    infinite_file.write(line)
    num_infinite += 1
  # 'line' hits an undefined cell
  elif TEST.IS_UNDEFINED(condition):
    undecided_file.write(line)
    num_undecided += 1
  # 'line' is uncategorized.
  elif TEST.IS_UNKNOWN(condition):
    unknown_file.write(line)
    num_unknown += 1
  # 'line' is unexpected (weird).
  else:
    error_file.write(line)
    num_error += 1
    was_error = True
    print "There was an unexpected value (%s) found in file (%s)" % (repr(condition), input_filename)
    print line

input_file.close()
halt_file.close()
infinite_file.close()
unknown_file.close()
error_file.close()
undecided_file.close()

# Remove input file so that it is not accidentally re-integrated
os.remove(input_filename)

# Print counts
print num_halt,num_infinite,num_undecided,num_unknown

# If error file is empty remove it.
if not was_error:
  os.remove(error_filename)
  sys.exit(0)
else:
  sys.exit(1)
