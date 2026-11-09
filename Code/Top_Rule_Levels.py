#!/usr/bin/env python3
"""List TMs with high-level proven rules, sorted with highest rule level first."""

import argparse
import sys
from pathlib import Path

import IO


def status_str(tm_record) -> str:
  status = tm_record.proto.status.halt_status
  if not status.is_decided:
    reason = tm_record.proto.filter.simulator.result.unknown_info.WhichOneof("reason")
    return f"undecided ({reason})" if reason else "undecided"
  elif status.is_halting:
    return "halt"
  else:
    return "inf"


def main():
  parser = argparse.ArgumentParser(description="List all TMs with proven rules at or above a minimum level")
  parser.add_argument("infiles", type=Path, nargs="+", help="Input protobuf file(s).")
  parser.add_argument(
    "-l",
    "--min-level",
    type=int,
    default=3,
    help="Minimum rule level to include (default: 3).",
  )
  parser.add_argument(
    "--undecided-only",
    action="store_true",
    help="Only include undecided TMs.",
  )
  parser.add_argument(
    "-n",
    "--top",
    type=int,
    default=0,
    help="Maximum number of TMs to print (0 for all, default: 0).",
  )
  args = parser.parse_args()

  matches = []
  for infile in args.infiles:
    with IO.Reader(infile) as reader:
      try:
        for tm_record in reader:
          if args.undecided_only and tm_record.proto.status.halt_status.is_decided:
            continue
          sim_res = tm_record.proto.filter.simulator.result
          levels = list(sim_res.num_rules_by_level)
          max_level = len(levels)
          if max_level >= args.min_level:
            matches.append(
              (
                max_level,
                levels[::-1],
                sim_res.num_rules_proven,
                tm_record.ttable_str(),
                levels,
                status_str(tm_record),
              )
            )
      except IO.Proto.IO_Error as e:
        print(
          f"WARNING: Stopped reading {infile} early due to partial file / unexpected EOF: {e}",
          file=sys.stderr,
        )

  matches.sort(reverse=True)
  if args.top > 0:
    matches = matches[: args.top]

  for max_level, _, total_rules, ttable, levels, status in matches:
    levels_str = ", ".join(f"L{lvl}:{cnt}" for lvl, cnt in enumerate(levels, start=1))
    print(f"{ttable}  max_level={max_level}  total={total_rules:3d}  [{levels_str}]  ({status})")


if __name__ == "__main__":
  main()
