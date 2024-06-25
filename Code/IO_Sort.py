#! /usr/bin/env python3

import argparse
from pathlib import Path
import time

import Halting_Lib
import IO


def sorting_func(tm_record):
  val = Halting_Lib.get_big_int(tm_record.proto.status.halt_status.halt_score)
  if not val:
    return 0
  else:
    return val

def sort(in_filename, out_filename):
  start_time = time.time()
  tm_records = []
  try:
    with IO.Reader(in_filename) as reader:
      for tm_record in reader:
        tm_records.append(tm_record)
  except IO.Proto.IO_Error:
    print(f"ERROR: {in_filename} has unexpected EOF. Moving on.")
  print(f"Read {len(tm_records):_} records ({time.time() - start_time:_.2f}s)")

  start_time = time.time()
  tm_records.sort(key = sorting_func, reverse = True)
  print(f"Sorted records ({time.time() - start_time:_.2f}s)")

  start_time = time.time()
  with IO.Proto.Writer(out_filename) as writer:
    for tm_record in tm_records:
      writer.write_record(tm_record)
  print(f"Wrote records ({time.time() - start_time:_.2f}s)")

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("in_file", type=Path)
  parser.add_argument("out_file", type=Path)
  args = parser.parse_args()

  sort(args.in_file, args.out_file)

if __name__ == "__main__":
  main()
