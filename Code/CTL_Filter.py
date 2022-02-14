#! /usr/bin/env python
#
# CTL_Filter.py
#
"""
Run one of the CTL algorithms - CTL1, CTL2, CTL3, CTL4.
"""

import sys

from Common import Exit_Condition
import IO
import CTL1
import CTL2
import CTL3
import CTL4
from Option_Parser import Filter_Option_Parser
from Alarm import ALARM, AlarmException

#
# Get command line options.
#                                     Form: (opt, type, def_val, req?, has_val?)
opts, args = Filter_Option_Parser(sys.argv,
  [("block-size", int, 1 , False, True),
   ("offset", int  , 0   , False, True),
   ("cutoff", int  , 200 , False, True),
   ("type"  , str  , None, True , True),
   ("time"  , float, None, False, True)]
)

log_number = opts["log_number"]

block_size = opts["block-size"]   # Block size for macro machine
offset     = opts["offset"] # Offset for block size to resolve parity errors

cutoff     = opts["cutoff"] # Steps to run to get advanced config before trying CTL

type       = opts["type"]   # CTL algorithm to run

runtime    = opts["time"]   # Timer value

if type == "CTL1":
  type_str  = "CTL1_A*"
  type_func = CTL1
elif type == "CTL2":
  type_str  = "CTL2_A*_B"
  type_func = CTL2
elif type == "CTL3":
  type_str  = "CTL3_A_B*"
  type_func = CTL3
elif type == "CTL4":
  type_str  = "CTL4_A*_B_C"
  type_func = CTL4
else:
  print("Unknown CTL: %s" % (type,))
  sys.exit(1)

inf_reasons = (type_str, cutoff, block_size, offset)

io = IO.IO(opts["infile"], opts["outfile"], log_number)

for io_record in io:
  # Run the simulator/filter on this machine (with an optional timer)
  try:
    if runtime:
      ALARM.set_alarm(runtime)

    success = type_func.test_CTL(io_record.ttable, cutoff, block_size, offset)

    ALARM.cancel_alarm()

  except AlarmException:
    ALARM.cancel_alarm()

    success = False

  if not success:
    # If we could not decide anything, leave the old result alone.
    io.write_record(io_record)
  else:
    # Otherwise classify it as being decided in some way.
    io_record.log_number = log_number

    io_record.extended        = io_record.category
    io_record.extended_reason = io_record.category_reason

    io_record.category        = Exit_Condition.INFINITE
    io_record.category_reason = inf_reasons

    io.write_record(io_record)
