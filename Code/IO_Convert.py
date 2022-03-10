#! /usr/bin/env python3
"""
Convert a data file from text format to protobuf or vice-versa.
"""

import argparse
from pathlib import Path

from Common import Exit_Condition
import Halting_Lib
import Input_Machine
import IO
import IO_proto


parser = argparse.ArgumentParser()
parser.add_argument("infile", type=Path)
parser.add_argument("outfile", type=Path)
args = parser.parse_args()

if args.infile.suffix == ".pb":
  print("Converting from protobuf to text")
  with open(args.infile, "rb") as infile, open(args.outfile, "w") as outfile:
    reader = IO_proto.Reader(infile)
    writer = IO.IO(None, outfile)
    for tm_record in reader:
      writer.write_protobuf(tm_record)

else:
  print("Converting from text to protobuf")
  with open(args.infile, "r") as infile, open(args.outfile, "wb") as outfile:
    reader = IO.IO(infile, None)
    writer = IO_proto.Writer(outfile)
    for io_record in reader:
      tm_record = IO_proto.create_record(io_record.ttable)

      # Set basic status
      if io_record.category == Exit_Condition.HALT:
        score, num_steps = io_record.category_reason
        Halting_Lib.set_halting(tm_record.status,
                                halt_steps = int(num_steps),
                                halt_score = int(score))

      elif io_record.category == Exit_Condition.INFINITE:
        inf_reason, qhalt_state, qhalt_steps = io_record.category_reason
        Halting_Lib.set_not_halting(tm_record.status,
                                    reason = IO.str2inf_reason[inf_reason])
        if qhalt_state == "No_Quasihalt":
          Halting_Lib.set_not_quasihalting(tm_record.status)
        elif qhalt_state not in ("Quasihalt_Not_Computed", "N/A"):
          tm_record.status.quasihalt_status.is_decided = True
          tm_record.status.quasihalt_status.is_quasihalting = True
          Halting_Lib.set_big_int(tm_record.status.quasihalt_status.quasihalt_steps,
                                  int(qhalt_steps))
          tm_record.status.quasihalt_status.quasihalt_state = qhalt_state

      elif io_record.category == Exit_Condition.UNKNOWN:
        unk_reason = Exit_Condition.condition_from_name[io_record.category_reason[0]]
        params = io_record.category_reason[1:]

        unknown_info = tm_record.filter.simulator.result.unknown_info
        if unk_reason == Exit_Condition.NOT_RUN:
          pass
        elif unk_reason == Exit_Condition.MAX_STEPS:
          try:
            unknown_info.over_loops.num_loops = int(params[0])
          except ValueError:
            pass
        elif unk_reason == Exit_Condition.OVER_TAPE:
          unknown_info.over_tape.compressed_tape_size = int(params[0])
        elif unk_reason == Exit_Condition.TIME_OUT:
          unknown_info.over_time.elapsed_time_sec = float(params[0])
        elif unk_reason == Exit_Condition.OVER_STEPS_IN_MACRO:
          (unknown_info.over_steps_in_macro.macro_symbol,
           unknown_info.over_steps_in_macro.macro_state,
           unknown_info.over_steps_in_macro.macro_dir_is_right) = params
        elif unk_reason == Exit_Condition.UNKNOWN and params[0] == "Gave_Up":
          # Set a dummy value so that we know which failure mode we hit.
          unknown_info.over_steps_in_macro.macro_symbol = "?"
          unknown_info.over_steps_in_macro.macro_state = "?"
        else:
          raise Exception(f"Unexpected Unknown reason: {io_record.category_reason[0]}")

      else:
        raise Exception(f"Unexpected exit condition: {io_record.category}")

      writer.write_record(tm_record)
