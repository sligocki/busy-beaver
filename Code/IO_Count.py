#! /usr/bin/env python3
"""Simple tool to count # of TM records in a protobuf file."""

import argparse
from pathlib import Path
import time

import IO


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm_file", type=Path, nargs="+")
  parser.add_argument("--print-freq", type=int, default=1_000_000)
  args = parser.parse_args()

  count = 0
  start_time = time.time()
  for filename in args.tm_file:
    file_count = 0
    try:
      with IO.Proto.Reader(filename) as reader:
        while reader.skip_record():
          file_count += 1
          if args.print_freq and (file_count % args.print_freq == 0):
            print(f" ... {file_count:_} ({time.time() - start_time:_.2f}s)")
    except IO.Proto.IO_Error:
      print(f"ERROR: {filename} has unexpected EOF. Moving on.")
    print(f"# TMs {filename}: {file_count:_} ({time.time() - start_time:_.2f}s)")
    count += file_count

  print(f"Total # TMs: {count:_} ({time.time() - start_time:_.2f}s)")

if __name__ == "__main__":
  main()
