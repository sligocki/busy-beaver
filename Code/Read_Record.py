#! /usr/bin/env python3
"""Print one record from a TM output file."""

import argparse

import IO
import Output_Machine


parser = argparse.ArgumentParser()
parser.add_argument("infile")
parser.add_argument("record_num", nargs="?", type=int, default=0,
                    help="Which record to read (first record is record_num=0).")
args = parser.parse_args()

tm_record = IO.Proto.load_record(args.infile, args.record_num)
print(tm_record)
print("ttable:", Output_Machine.display_ttable(
  IO.Proto.unpack_ttable(tm_record.tm.ttable_packed)))
print("Serialized sizes:", tm_record.ByteSize(),
      tm_record.tm.ByteSize(), tm_record.status.ByteSize(),
      tm_record.filter.ByteSize())
