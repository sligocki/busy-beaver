#! /usr/bin/env python3

import argparse
from pathlib import Path
import time

import Halting_Lib
import IO


def matches(tm_record):
  return tm_record.filter.simulator.result.num_finite_linear_rules_proven > 0

def filter(in_filenames, out_filename):
  start_time = time.time()
  num_records_read = 0
  num_records_written = 0
  with IO.Proto.Writer(out_filename) as writer:
    for in_filename in in_filenames:
      try:
        with IO.Reader(in_filename) as reader:
          for tm_record in reader:
            num_records_read += 1
            # try:
            #   score = Halting_Lib.get_big_int(tm_record.proto.status.halt_status.halt_score)
            # except:
            #   score = None
            if matches(tm_record.proto):
              writer.write_record(tm_record)
              num_records_written += 1
            if num_records_read % 1_000_000 == 0:
              print(f" ... {num_records_read:_d} -> {num_records_written:_d} ({time.time() - start_time:_.2f}s)")
              writer.flush()
      except IO.Proto.IO_Error:
        print(f"ERROR: {in_filename} has unexpected EOF. Moving on.")

  print(f"Filtered {num_records_read:_d} -> {num_records_written:_d} ({time.time() - start_time:_.2f}s)")

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("in_files", type=Path, nargs="+")
  parser.add_argument("out_file", type=Path)
  args = parser.parse_args()

  filter(args.in_files, args.out_file)

if __name__ == "__main__":
  main()
