#! /usr/bin/env python3

import argparse
from pathlib import Path

import Halting_Lib
import IO


class OutputFiles:
  def __init__(self, dir):
    self.dir = dir
    self.writer = {}
    self.num_written = 0
    self.num_unknown = 0
    self.num_halt = 0
    self.num_qhalt = 0
    self.num_infinite = 0

  def __enter__(self):
    for type in ["halt", "qhalt", "infinite", "unknown"]:
      self.writer[type] = IO.Proto.Writer(Path(self.dir, f"{type}.pb"))
      self.writer[type].__enter__()
    return self

  def __exit__(self, *args):
    """Close all files"""
    for type in self.writer:
      self.writer[type].__exit__(*args)

  def categorize_record(self, tm_record):
    if not tm_record.status.halt_status.is_decided:
      self.num_unknown += 1
      return "unknown"
    elif tm_record.status.halt_status.is_halting:
      # Halting
      self.num_halt += 1
      return "halt"
    elif tm_record.status.quasihalt_status.is_quasihalting:
      # Quasihalting (non halting)
      self.num_qhalt += 1
      return "qhalt"
    else:
      # Infinite (non quasihalting)
      self.num_infinite += 1
      return "infinite"

  def write_record(self, tm_record):
    type = self.categorize_record(tm_record.proto)
    self.writer[type].write_record(tm_record)
    self.num_written += 1


def categorize(in_filenames, out_dir):
  with OutputFiles(out_dir) as out:
    for in_filename in in_filenames:
      with IO.Proto.Reader(in_filename) as reader:
        for tm_record in reader:
          out.write_record(tm_record)

          if out.num_written % 1_000_000 == 0:
            print(f" ... categorized {out.num_written:_} records ...")

  print(f"Done:")
  print(f"      Categorized {out.num_unknown:_} unknown records.")
  print(f"      Categorized {out.num_halt:_} halt records.")
  print(f"      Categorized {out.num_qhalt:_} qhalt records.")
  print(f"      Categorized {out.num_infinite:_} infinite records.")
  print(f"      Categorized {out.num_written:_} records total.")

def split_unknown(in_filenames: list[Path], out_dir: Path) -> None:
  out = {
    "over_loops": IO.Proto.Writer(out_dir / "unknown_over_loops.pb"),
    "over_tape": IO.Proto.Writer(out_dir / "unknown_over_tape.pb"),
    "over_time": IO.Proto.Writer(out_dir / "unknown_over_time.pb"),
    "over_steps_in_macro": IO.Proto.Writer(out_dir / "unknown_over_steps_in_macro.pb"),
    "threw_exception": IO.Proto.Writer(out_dir / "unknown_threw_exception.pb"),
  }
  for writer in out.values():
    writer.__enter__()
  num_written = 0
  for in_filename in in_filenames:
    with IO.Proto.Reader(in_filename) as reader:
      for tm_record in reader:
        reason = tm_record.proto.filter.simulator.result.unknown_info.WhichOneof("reason")
        if reason:
          out[reason].write_record(tm_record)
          num_written += 1
          if num_written % 1_000_000 == 0:
            print(f" ... categorized {num_written:_} records ...")
    print(f"Categorized {num_written:_} records total")

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("in_files", nargs="*", type=Path)
  parser.add_argument("--out-dir", type=Path, required=True)

  parser.add_argument("--split-unknown", action="store_true",
                      help="Split unknown TMs by reason (over tape, over time, etc.)")
  args = parser.parse_args()

  if args.split_unknown:
    split_unknown(args.in_files, args.out_dir)
  else:
    categorize(args.in_files, args.out_dir)

if __name__ == "__main__":
  main()
