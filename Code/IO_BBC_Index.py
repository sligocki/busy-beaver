#!/usr/bin/env python3

import argparse
from pathlib import Path

import IO


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("db_file", type=Path)
  parser.add_argument("index_file", nargs="?", type=Path)
  parser.add_argument("--outfile", type=Path, required=True)
  args = parser.parse_args()

  if args.index_file:
    reader = IO.BBC.IndexReader(args.db_file, args.index_file)
  else:
    reader = IO.BBC.Reader(args.db_file)

  with IO.Proto.Writer(args.outfile) as writer:
    with reader:
      for tm_record in reader:
        writer.write_record(tm_record)


if __name__ == "__main__":
  main()
