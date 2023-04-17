#! /usr/bin/env python3
"""Print one record from a TM output file."""

import argparse

import Halting_Lib
import IO


parser = argparse.ArgumentParser()
parser.add_argument("infile")
parser.add_argument("record_num", nargs="?", type=int, default=0,
                    help="Which record to read (first record is record_num=0).")
args = parser.parse_args()

tm_record = IO.Proto.load_record(args.infile, args.record_num)
print(tm_record.proto)
print("ttable:", tm_record.ttable_str())
if tm_record.proto.status.halt_status.is_halting:
  score_str = Halting_Lib.big_int_approx_and_full_str(
    Halting_Lib.get_big_int(tm_record.proto.status.halt_status.halt_score))
  print("Halt Score:", score_str)
print("Serialized sizes:", tm_record.proto.ByteSize(),
      tm_record.proto.tm.ByteSize(), tm_record.proto.status.ByteSize(),
      tm_record.proto.filter.ByteSize())
