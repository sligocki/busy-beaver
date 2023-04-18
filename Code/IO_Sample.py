#! /usr/bin/env python3
# Randomly sample TMs from input files.
# Uses a streaming algorithm that does not need to know the number of TMs total.


import argparse
from pathlib import Path
import random

import IO


def sample(in_filenames, out_filename, sample_size):
  num_records = 1
  num_read = 0
  sample = []
  for in_filename in in_filenames:
    try:
      with IO.Reader(in_filename) as reader:
        while True:
          if len(sample) < sample_size:
            if not (tm_record := reader.read_record()):
              break
            num_read += 1
            sample.append(tm_record)
          elif random.random() < sample_size / num_records:
            # Replace one of the existing sampled TMs with decreasing chance.
            if not (tm_record := reader.read_record()):
              break
            num_read += 1
            i = random.randrange(sample_size)
            sample[i] = tm_record
          else:
            # If this record is not part of the sample, skip.
            if not reader.skip_record():
              break
          num_records += 1
    except IO.Proto.IO_Error:
      print(f"ERROR: {in_filename} has unexpected EOF. Moving on.")
    print(f"Finished reading {in_filename}: {num_records:_} total records / {num_read:_} ({num_read / num_records:.1%} records read)")

  random.shuffle(sample)
  with IO.Proto.Writer(out_filename) as writer:
    for tm_record in sample:
      writer.write_record(tm_record)
  print("Done")


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("in_files", nargs="+", type=Path)
  parser.add_argument("--out-file", type=Path, required=True)
  parser.add_argument("--sample-size", "-n", type=int, default=1000)
  args = parser.parse_args()

  sample(args.in_files, args.out_file, args.sample_size)

if __name__ == "__main__":
  main()
