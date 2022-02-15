#! /usr/bin/env python3
#
# rewind.py
#
"""
Go back to an earlier point in the analysis of a set of TMs using the current
output files and the log of events.
"""

import sys, os

from IO import IO
from Turing_Machine import Turing_Machine

usage = "rewind.py command_number save_halt_filename halt_filename save_infinite_filename infinite_filename save_undecided_filename undecided_filename unknown_filename"

command_number = int(sys.argv[1])

save_halt_filename = sys.argv[2]
save_halt_file = file(save_halt_filename, "r")

halt_filename = sys.argv[3]
halt_file = file(halt_filename, "w")

save_infinite_filename = sys.argv[4]
save_infinite_file = file(save_infinite_filename, "r")

infinite_filename = sys.argv[5]
infinite_file = file(infinite_filename, "w")

save_undecided_filename = sys.argv[6]
save_undecided_file = file(save_undecided_filename, "r")

undecided_filename = sys.argv[7]
undecided_file = file(undecided_filename, "w")

unknown_filename = sys.argv[8]
unknown_file = file(unknown_filename, "a")

unknownIO = IO(None,unknown_file)

haltIO = IO(save_halt_file,halt_file)

cur_result = haltIO.read_result()
while cur_result:
  machine = Turing_Machine(cur_result[1],cur_result[2])
  machine.set_TTable(cur_result[6])

  if cur_result[7] is None or cur_result[7] <= command_number:
    haltIO.write_result(cur_result[0],cur_result[3],
                        cur_result[4],cur_result[5],
                        machine,
                        cur_result[7],cur_result[8])
  else:
    unknownIO.write_result(cur_result[0],cur_result[3],
                           cur_result[4],cur_result[8],
                           machine)

  cur_result = haltIO.read_result()

infiniteIO = IO(save_infinite_file,infinite_file)

cur_result = infiniteIO.read_result()
while cur_result:
  machine = Turing_Machine(cur_result[1],cur_result[2])
  machine.set_TTable(cur_result[6])

  if cur_result[7] is None or cur_result[7] <= command_number:
    infiniteIO.write_result(cur_result[0],cur_result[3],
                            cur_result[4],cur_result[5],
                            machine,
                            cur_result[7],cur_result[8])
  else:
    unknownIO.write_result(cur_result[0],cur_result[3],
                           cur_result[4],cur_result[8],
                           machine)

  cur_result = infiniteIO.read_result()

undecidedIO = IO(save_undecided_file,undecided_file)

cur_result = undecidedIO.read_result()
while cur_result:
  machine = Turing_Machine(cur_result[1],cur_result[2])
  machine.set_TTable(cur_result[6])

  if cur_result[7] is None or cur_result[7] <= command_number:
    undecidedIO.write_result(cur_result[0],cur_result[3],
                            cur_result[4],cur_result[5],
                            machine,
                            cur_result[7],cur_result[8])
  else:
    unknownIO.write_result(cur_result[0],cur_result[3],
                           cur_result[4],cur_result[8],
                           machine)

  cur_result = undecidedIO.read_result()
