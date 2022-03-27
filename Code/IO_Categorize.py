#! /usr/bin/env python3

import argparse
import collections
import math
from pathlib import Path

import Halting_Lib
import IO

import io_pb2


class OutputFiles:
  def __init__(self, dir):
    self.dir = dir
    self.file = {}
    self.writer = {}
    self.num_written = 0

  def __enter__(self):
    for type in ["halt.small", "halt.large",
                 "qhalt.small", "qhalt.large",
                 "infinite", "unknown"]:
      self.file[type] = open(Path(self.dir, f"{type}.pb"), "wb")
      self.writer[type] = IO.Proto.Writer(self.file[type])
    return self

  def __exit__(self, *args):
    """Close all files"""
    for type in self.file:
      self.file[type].close()

  def categorize_record(self, tm_record):
    if not tm_record.status.halt_status.is_decided:
      return "unknown"
    elif tm_record.status.halt_status.is_halting:
      # Halting
      if Halting_Lib.get_big_int(
        tm_record.status.halt_status.halt_steps) < 1000:
        return "halt.small"
      else:
        return "halt.large"
    elif tm_record.status.quasihalt_status.is_quasihalting:
      # Quasihalting (non halting)
      if Halting_Lib.get_big_int(
        tm_record.status.quasihalt_status.quasihalt_steps) < 1000:
        return "qhalt.small"
      else:
        return "qhalt.large"
    else:
      # Infinite (non quasihalting)
      return "infinite"

  def write_record(self, tm_record):
    type = self.categorize_record(tm_record)
    self.writer[type].write_record(tm_record)
    self.num_written += 1


def filter(in_filenames, out_dir):
  with OutputFiles(out_dir) as out:
    for in_filename in in_filenames:
      with open(in_filename, "rb") as infile:
        reader = IO.Proto.Reader(infile)
        for tm_record in reader:
          out.write_record(tm_record)

          if out.num_written % 1_000_000 == 0:
            print(f" ... categorized {out.num_written:_} records ...")
  print(f"Done: Categorized {out.num_written:_} records total.")

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("in_files", nargs="*", type=Path)
  parser.add_argument("--out-dir", type=Path, required=True)
  args = parser.parse_args()

  filter(args.in_files, args.out_dir)

if __name__ == "__main__":
  main()
