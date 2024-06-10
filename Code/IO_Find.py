#! /usr/bin/env python3
"""Find record for specific TM."""

import argparse
from pathlib import Path

import Halting_Lib
from IO.Proto import Reader


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm", type=str)
  parser.add_argument("infiles", nargs="+", type=Path)
  args = parser.parse_args()

  for infile in args.infiles:
    with Reader(infile) as reader:
      for tm_record in reader:
        if tm_record.tm().ttable_str() == args.tm:
          print(tm_record.proto)
          print("ttable:", tm_record.ttable_str())
          if tm_record.proto.status.halt_status.is_halting:
            score_str = Halting_Lib.big_int_approx_and_full_str(
              Halting_Lib.get_big_int(tm_record.proto.status.halt_status.halt_score))
            print("Halt Score:", score_str)
          return

  print(f"TM {args.tm} not found in {args.infiles}")

if __name__ == "__main__":
  main()