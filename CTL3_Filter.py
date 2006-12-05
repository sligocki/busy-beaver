#! /usr/bin/env python
#

from CTL3 import test_CTL
import IO
import sys
from Option_Parser import Filter_Option_Parser

# Return Conditions
ERROR = -1
HALT = 0
OVER_TAPE = 1
MAX_STEPS = 2
UNKNOWN = (OVER_TAPE, MAX_STEPS)
UNDEF_CELL = 3
INFINITE = 4

# Get command line options.
#                                     Form: (opt, type, def_val, req?, has_val?)
opts, args = Filter_Option_Parser(sys.argv, [("size"  , int, 1  , False, True),
                                             ("offset", int, 0  , False, True),
                                             ("cutoff", int, 200, False, True)])

log_number = opts["log_number"]
cutoff = opts["cutoff"]   # Steps to run to get advanced config before trying CTL
block_size = opts["size"] # Block size for macro machine
offset = opts["offset"]   # Offset for block size to resolve parity errors
io = IO.IO(opts["infile"], opts["outfile"], log_number)
next = io.read_result()

results = (INFINITE, 8, cutoff, block_size, offset, "CTL_A_B*")

while next:
  ttable = next[6]
  # Run the simulator/filter on this machine
  success = test_CTL(ttable, cutoff, block_size, offset)

  # If we could not decide anything, leave the old result alone.
  if not success:
    io.write_result_raw(*next)
  # Otherwise classify it as beeing decided in some way.
  else:
    old_results = next[5]
    io.write_result_raw(*(next[0:5]+(results, ttable, log_number, old_results)))

  next = io.read_result()
