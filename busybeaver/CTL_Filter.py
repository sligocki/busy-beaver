#! /usr/bin/env python
#
# Run one of the CTL algorithms - CTL1, CTL2, CTL3, CTL4
#

import sys
import IO
import CTL1
import CTL2
import CTL3
import CTL4
from Option_Parser import Filter_Option_Parser

#
# Return Conditions
#
ERROR = -1
HALT = 0
OVER_TAPE = 1
MAX_STEPS = 2
UNKNOWN = (OVER_TAPE, MAX_STEPS)
UNDEF_CELL = 3
INFINITE = 4

#
# Get command line options.
#                                     Form: (opt, type, def_val, req?, has_val?)
opts, args = Filter_Option_Parser(sys.argv, [("size"  , int, 1   , False, True),
                                             ("offset", int, 0   , False, True),
                                             ("cutoff", int, 200 , False, True),
                                             ("type"  , str, None, True , True)])

log_number = opts["log_number"]

block_size = opts["size"]   # Block size for macro machine
offset     = opts["offset"] # Offset for block size to resolve parity errors

cutoff     = opts["cutoff"] # Steps to run to get advanced config before trying CTL

type       = opts["type"]   # CTL algorithm to run

if type == "CTL1":
  type_num  = 6
  type_str  = "CTL_A*"
  type_func = CTL1
elif type == "CTL2":
  type_num  = 7
  type_str  = "CTL_A*_B"
  type_func = CTL2
elif type == "CTL3":
  type_num  = 8
  type_str  = "CTL_A_B*"
  type_func = CTL3
elif type == "CTL4":
  type_num  = 9
  type_str  = "CTL_A*_B_C"
  type_func = CTL4
else:
  print "Unknown CTL: %s" % (type,)
  sys.exit(1)

results = (INFINITE, type_num, cutoff, block_size, offset, type_str)

io   = IO.IO(opts["infile"], opts["outfile"], log_number)
next = io.read_result()

while next:
  ttable = next[6]
  # Run the simulator/filter on this machine
  success = type_func.test_CTL(ttable, cutoff, block_size, offset)

  # If we could not decide anything, leave the old result alone.
  if not success:
    io.write_result_raw(*next)
  # Otherwise classify it as beeing decided in some way.
  else:
    old_results = next[5]
    io.write_result_raw(*(next[0:5]+(results, ttable, log_number, old_results)))

  next = io.read_result()
