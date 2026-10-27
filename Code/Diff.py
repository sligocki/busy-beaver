#! /usr/bin/env python3
"""
Find differences between two sets of TM files, respecting TM expansion in TNF.

If a TM with undefined transitions in file A is expanded to many TMs in file B
and all expansion cases are covered, this is not treated as a difference.
"""

import argparse
from collections.abc import Iterable
from pathlib import Path
import sys
import time

import IO
from IO import TM_Record
import Macro.Turing_Machine
import TM_Enum


def load_tms(files: Iterable[Path | str]) -> set[str]:
  """Load TM transition table strings from a list of files."""
  tm_set: set[str] = set()
  for filename in files:
    filename = Path(filename)
    mod = IO.General.guess_module(filename)
    if mod in (IO.Proto, IO.CSV):
      with mod.Reader(filename) as reader:
        for rec in reader:
          tm_set.add(rec.tm().ttable_str())
    else:
      with IO.open_file(filename, "rt") as f:
        for line in f:
          line = line.strip()
          if line:
            tm_set.add(line.split()[0])
  return tm_set


def is_descendant(
  child_tm: Macro.Turing_Machine.Simple_Machine,
  parent_tm: Macro.Turing_Machine.Simple_Machine,
) -> bool:
  """Check if child_tm is a valid specialization (descendant) of parent_tm."""
  if child_tm.num_states < parent_tm.num_states or child_tm.num_symbols < parent_tm.num_symbols:
    return False
  for s in range(parent_tm.num_states):
    for c in range(parent_tm.num_symbols):
      p_trans = parent_tm.get_trans_object(symbol_in=c, state_in=s)
      if p_trans.condition != Macro.Turing_Machine.UNDEFINED:
        c_trans = child_tm.get_trans_object(symbol_in=c, state_in=s)
        if (
          c_trans.condition != p_trans.condition
          or c_trans.symbol_out != p_trans.symbol_out
          or c_trans.dir_out != p_trans.dir_out
          or c_trans.state_out != p_trans.state_out
        ):
          return False
  return True


def diff_sets(
  set_a: set[str],
  set_b: set[str],
  allow_no_halt: bool = False,
) -> tuple[set[str], set[str]]:
  """
  Compute set difference between set_a and set_b modulo TM expansion.
  Returns (in_a_not_b, in_b_not_a).
  """
  common = set_a & set_b
  cur_a = set(set_a - common)
  cur_b = set(set_b - common)

  parsed_a = {s: TM_Record.parse_tm(s) for s in cur_a}
  parsed_b = {s: TM_Record.parse_tm(s) for s in cur_b}

  def expand_side(side_from, side_to, parsed_from, parsed_to):
    changed = False
    new_from = set()
    for tm_str in side_from:
      if tm_str in side_to:
        side_to.remove(tm_str)
        del parsed_to[tm_str]
        changed = True
        continue

      tm = parsed_from[tm_str]
      tme = TM_Enum.TM_Enum(tm, allow_no_halt=allow_no_halt)
      undefs = []
      for s in range(tm.num_states):
        for c in range(tm.num_symbols):
          if tm.get_trans_object(symbol_in=c, state_in=s).condition == Macro.Turing_Machine.UNDEFINED:
            undefs.append((s, c))

      best_s_c = None
      for s, c in undefs:
        for to_tm in parsed_to.values():
          if to_tm.get_trans_object(symbol_in=c, state_in=s).condition != Macro.Turing_Machine.UNDEFINED:
            if is_descendant(to_tm, tm):
              best_s_c = (s, c)
              break
        if best_s_c is not None:
          break

      if best_s_c is not None:
        changed = True
        for ch in tme.enum_children(best_s_c[0], best_s_c[1]):
          ch_str = ch.tm.ttable_str()
          if ch_str in side_to:
            side_to.remove(ch_str)
            del parsed_to[ch_str]
          else:
            new_from.add(ch_str)
            parsed_from[ch_str] = ch.tm
      else:
        new_from.add(tm_str)

    return new_from, changed

  while True:
    cur_a, ch_a = expand_side(cur_a, cur_b, parsed_a, parsed_b)
    cur_b, ch_b = expand_side(cur_b, cur_a, parsed_b, parsed_a)
    if not ch_a and not ch_b:
      break

  return cur_a, cur_b


def run_diff(
  files_a: list[Path],
  files_b: list[Path],
  allow_no_halt: bool = False,
  max_print: int = 20,
  print_all: bool = False,
  quiet: bool = False,
  outfile_a: Path | None = None,
  outfile_b: Path | None = None,
) -> int:
  """Run TM diff and display / save results. Returns exit code (0 if identical, 1 if diff)."""
  start_time = time.time()
  if not quiet:
    print(f"Loading {len(files_a)} file(s) for Set A...")
  set_a = load_tms(files_a)

  if not quiet:
    print(f"Loading {len(files_b)} file(s) for Set B...")
  set_b = load_tms(files_b)

  load_time = time.time() - start_time
  common_count = len(set_a & set_b)
  only_a_raw = len(set_a) - common_count
  only_b_raw = len(set_b) - common_count

  if not quiet:
    print(f"\nLoaded in {load_time:.2f}s:")
    print(f"  Set A: {len(set_a):_} distinct TMs")
    print(f"  Set B: {len(set_b):_} distinct TMs")
    print(f"  Exact matches: {common_count:_}")
    print(f"  Differences before expansion: {only_a_raw:_} in A, {only_b_raw:_} in B")
    print("\nResolving TM expansions...")

  diff_start = time.time()
  a_only, b_only = diff_sets(set_a, set_b, allow_no_halt=allow_no_halt)
  diff_time = time.time() - diff_start

  sorted_a = sorted(a_only)
  sorted_b = sorted(b_only)

  if outfile_a:
    with IO.open_file(outfile_a, "wt") as f:
      for tm in sorted_a:
        f.write(f"{tm}\n")
    if not quiet:
      print(f"Wrote {len(sorted_a):_} TMs to {outfile_a}")

  if outfile_b:
    with IO.open_file(outfile_b, "wt") as f:
      for tm in sorted_b:
        f.write(f"{tm}\n")
    if not quiet:
      print(f"Wrote {len(sorted_b):_} TMs to {outfile_b}")

  print(f"\nDiff results respecting TM expansion ({diff_time:.2f}s):")
  print(f"  In A but not B: {len(sorted_a):_}")
  print(f"  In B but not A: {len(sorted_b):_}")

  if not quiet:
    if sorted_a:
      print(f"\nTMs in A but not B ({len(sorted_a):_} total):")
      limit = len(sorted_a) if print_all else min(len(sorted_a), max_print)
      for tm in sorted_a[:limit]:
        print(f"  {tm}")
      if not print_all and len(sorted_a) > limit:
        print(f"  ... ({len(sorted_a) - limit:_} more omitted; use --print-all to see all)")

    if sorted_b:
      print(f"\nTMs in B but not A ({len(sorted_b):_} total):")
      limit = len(sorted_b) if print_all else min(len(sorted_b), max_print)
      for tm in sorted_b[:limit]:
        print(f"  {tm}")
      if not print_all and len(sorted_b) > limit:
        print(f"  ... ({len(sorted_b) - limit:_} more omitted; use --print-all to see all)")

  if not sorted_a and not sorted_b:
    print("\nNo differences found (sets are equivalent modulo TM expansion).")
    return 0
  else:
    return 1


def main():
  parser = argparse.ArgumentParser(description="Find differences between two sets of TM files respecting TM expansion.")
  parser.add_argument("file_a", nargs="+", type=Path, help="Files in Set A")
  parser.add_argument(
    "--file-b",
    "--diff",
    nargs="+",
    type=Path,
    required=True,
    dest="file_b",
    help="Files in Set B",
  )
  parser.add_argument(
    "--allow-no-halt",
    action="store_true",
    help="Allow enumerating machines without halt states.",
  )
  parser.add_argument(
    "--max-print",
    type=int,
    default=20,
    help="Maximum number of differing TMs to display (default: 20).",
  )
  parser.add_argument(
    "--print-all",
    action="store_true",
    help="Print all differing TMs without truncation.",
  )
  parser.add_argument(
    "--quiet",
    "-q",
    action="store_true",
    help="Only print summary counts.",
  )
  parser.add_argument(
    "--outfile-a",
    type=Path,
    help="File to write TMs that are in A but not B.",
  )
  parser.add_argument(
    "--outfile-b",
    type=Path,
    help="File to write TMs that are in B but not A.",
  )

  args = parser.parse_args()
  exit_code = run_diff(
    files_a=args.file_a,
    files_b=args.file_b,
    allow_no_halt=args.allow_no_halt,
    max_print=args.max_print,
    print_all=args.print_all,
    quiet=args.quiet,
    outfile_a=args.outfile_a,
    outfile_b=args.outfile_b,
  )
  sys.exit(exit_code)


if __name__ == "__main__":
  main()
