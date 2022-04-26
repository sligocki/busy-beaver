#! /usr/bin/env python3
"""
Convert a data file from text format to protobuf or vice-versa.
"""

import argparse
from pathlib import Path

import IO


parser = argparse.ArgumentParser()
parser.add_argument("infile", type=Path)
parser.add_argument("outfile", type=Path)
args = parser.parse_args()

num_records = 0
if args.infile.suffix == ".pb":
  print("Converting from protobuf to text")
  with open(args.infile, "rb") as infile, open(args.outfile, "w") as outfile:
    reader = IO.Proto.Reader(infile)
    writer = IO.Text.ReaderWriter(None, outfile)
    for tm_record in reader:
      num_records += 1
      writer.write_record(tm_record)

else:
  print("Converting from text to protobuf")
  with open(args.infile, "r") as infile, open(args.outfile, "wb") as outfile:
    reader = IO.Text.Reader(infile)
    writer = IO.Proto.Writer(outfile)
    for tm_record in reader:
      num_records += 1
      writer.write_record(tm_record)

print(f"Done: Converted {num_records:_} records")
