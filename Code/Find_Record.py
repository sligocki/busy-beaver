#! /usr/bin/env python3

import argparse
from pathlib import Path
import time

import IO
from IO.TM_Record import pack_tm


def find(tm_std, in_filename):
  tm = IO.parse_tm(tm_std)
  ttable_bytes = pack_tm(tm)
  with IO.Reader(in_filename) as reader:
    for record_num, tm_record in enumerate(reader):
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
