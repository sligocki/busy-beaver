#! /usr/bin/env python3

import argparse
from pathlib import Path

import IO
from IO.TM_Record import _pack_tm


def find(tm_std, in_filename):
  tm = IO.parse_tm(tm_std)
  ttable_bytes = _pack_tm(tm)
  with IO.Reader(in_filename) as reader:
    for record_num, tm_record in enumerate(reader):
      assert tm_record.proto.tm.WhichOneof("ttable") == "ttable_packed", f"Find_Record.py has not implemented finding records of this type: {tm_record.proto.tm}"
      if tm_record.proto.tm.ttable_packed == ttable_bytes:
        print(record_num)
        print(tm_record.proto)
        print("ttable:", tm_record.ttable_str())
        return

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm_std", help="TM in std text format")
  parser.add_argument("in_file", type=Path)
  args = parser.parse_args()

  find(args.tm_std, args.in_file)

if __name__ == "__main__":
  main()
