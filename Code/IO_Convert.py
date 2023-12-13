#! /usr/bin/env python3
"""
Convert a data file from text format to protobuf or vice-versa.
"""

import argparse
from pathlib import Path

import IO


FORMATS = ["auto", "text", "proto", "morphett", "text_old",
           "bbc_db", "bbc_index", "bbc_index_text"]

def Detect_Format(path):
  # Currently, this detection is very primative ... perhaps improve over time?
  if ".pb" in path.suffixes:
    # My custom Protobuf based format.
    return "proto"

  elif ".morphett" in path.suffixes:
    # My custom Protobuf based format.
    return "morphett"

  # Variety of BBC formats
  elif ".db" in path.suffixes:
    return "bbc_db"
  elif ".index" in path.suffixes:
    if ".txt" in path.suffixes:
      # Mateon's version of index w/ on ID per line.
      return "bbc_index_text"
    else:
      # Official BBC binary index file.
      return "bbc_index"
  elif ".old" in path.suffixes:
    return "text_old"

  # Default to standard text format.
  else:
    return "text"


def get_reader(format, filename, args):
  if format == "text":
    return IO.StdText.Reader(filename)
  elif format == "proto":
    return IO.Proto.Reader(filename)
  elif format == "morphett":
    return IO.Morphett.Reader(filename)

  elif format == "bbc_db":
    return IO.BBC.Reader(filename)
  elif format == "bbc_index":
    return IO.BBC.IndexReader(args.bbc_seed_db, filename)
  elif format == "bbc_index_text":
    return IO.BBC.TextIndexReader(args.bbc_seed_db, filename)

  else:
    raise Exception(f"Unexpected format {format}")

def get_writer(format, filename, args):
  if format == "text":
    return IO.StdText.Writer(filename)
  elif format == "proto":
    return IO.Proto.Writer(filename)
  elif format == "morphett":
    return IO.Morphett.Writer(filename)
  elif format == "text_old":
    return IO.OldText.Writer(filename)

  elif format == "bbc_db":
    return IO.BBC.Writer(filename)
  elif format == "bbc_index":
    return NotImplementedError(f"We do not support writing BBC index files.")
  elif format == "bbc_index_text":
    return NotImplementedError(f"We do not support writing BBC index files.")

  else:
    raise Exception(f"Unexpected format {format}")


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("infile", type=Path)
  parser.add_argument("outfile", type=Path)
  parser.add_argument("--informat", choices=FORMATS, default="auto",
                      help="Manually set format of input file. "
                      "Default is to auto detect based on filename extension.")
  parser.add_argument("--outformat", choices=FORMATS, default="auto",
                      help="Manually set format of output file. "
                      "Default is to auto detect based on filename extension.")

  parser.add_argument("--bbc-seed-db", type=Path, default=Path("bbc/seed.db.zip"),
                      help="Location of BBC seed DB (only needed to read BBC "
                      "index files).")
  args = parser.parse_args()

  if args.informat == "auto":
    args.informat = Detect_Format(args.infile)
  if args.outformat == "auto":
    args.outformat = Detect_Format(args.outfile)


  print(f"Converting from {args.informat} to {args.outformat}")
  num_records = 0
  with get_writer(args.outformat, args.outfile, args) as writer:
    with get_reader(args.informat, args.infile, args) as reader:
      for tm_record in reader:
        num_records += 1
        writer.write_record(tm_record)

  print(f"Done: Converted {num_records:_} records")

if __name__ == "__main__":
  main()
