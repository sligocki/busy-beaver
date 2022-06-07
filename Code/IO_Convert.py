#! /usr/bin/env python3
"""
Convert a data file from text format to protobuf or vice-versa.
"""

import argparse
from pathlib import Path

import IO


def Detect_Format(path):
  # Currently, this detection is very primative ... perhaps improve over time?
  if path.suffix == ".pb":
    return "proto"
  else:
    return "text"


FORMATS = {
  "auto": None,
  "proto": IO.Proto,
  "text": IO.Text,
  "bbc": IO.BBC,
}

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("infile", type=Path)
  parser.add_argument("outfile", type=Path)
  parser.add_argument("--informat", choices=FORMATS.keys(), default="auto")
  parser.add_argument("--outformat", choices=FORMATS.keys(), default="auto")
  args = parser.parse_args()

  if args.informat == "auto":
    args.informat = Detect_Format(args.infile)
  if args.outformat == "auto":
    args.outformat = Detect_Format(args.outfile)


  print(f"Converting from {args.informat} to {args.outformat}")
  num_records = 0
  with FORMATS[args.outformat].Writer(args.outfile) as writer:
    with FORMATS[args.informat].Reader(args.infile) as reader:
      for tm_record in reader:
        num_records += 1
        writer.write_record(tm_record)

  print(f"Done: Converted {num_records:_} records")

if __name__ == "__main__":
  main()
