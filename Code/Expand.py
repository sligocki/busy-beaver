#! /usr/bin/env python3
"""
Expand TMs listed in input files into all of their Tree Normal Form (TNF)
children along the transition specified on each line.

Input line format:
  TM halt_steps halt_on_state halt_on_symbol
"""

import argparse
from collections.abc import Iterable
from pathlib import Path
import time

import Halting_Lib
import IO
from IO import TM_Record
from Macro import Turing_Machine
import TM_Enum


def parse_and_expand_line(
  line: str,
  *,
  allow_no_halt: bool = False,
  source_info: str = "",
) -> list[TM_Record.TM_Record]:
  """Parse a line 'TM halt_steps halt_on_state halt_on_symbol' and return TNF child TM_Records."""
  parts = line.split()
  if len(parts) < 4:
    loc = f" at {source_info}" if source_info else ""
    raise ValueError(f"Expected format 'TM halt_steps halt_on_state halt_on_symbol'{loc}, got: {line!r}")

  tm_str, steps_str, state_str, symbol_str = parts[:4]
  tm = TM_Record.parse_tm(tm_str)
  halt_steps = int(steps_str)
  state_in = Turing_Machine.str_to_state(state_str)
  symbol_in = int(symbol_str)

  if not (0 <= state_in < tm.num_states):
    loc = f" at {source_info}" if source_info else ""
    raise ValueError(f"State {state_str!r} (index {state_in}) out of range for {tm.num_states}-state TM {tm_str}{loc}")
  if not (0 <= symbol_in < tm.num_symbols):
    loc = f" at {source_info}" if source_info else ""
    raise ValueError(
      f"Symbol {symbol_str!r} (index {symbol_in}) out of range for {tm.num_symbols}-symbol TM {tm_str}{loc}"
    )

  trans = tm.get_trans_object(symbol_in=symbol_in, state_in=state_in)
  if trans.condition != Turing_Machine.UNDEFINED:
    loc = f" at {source_info}" if source_info else ""
    raise ValueError(f"Transition ({state_str}, {symbol_in}) in TM {tm_str} is not undefined{loc}")

  tme = TM_Enum.TM_Enum(tm, allow_no_halt=allow_no_halt)
  children = [
    TM_Record.TM_Record(tm_enum=child_tme) for child_tme in tme.enum_children(state_in=state_in, symbol_in=symbol_in)
  ]
  # Include the halting child (where this transition becomes 1RZ) with Halt status and steps.
  tme.set_halt_trans(state_in=state_in, symbol_in=symbol_in)
  halt_rec = TM_Record.TM_Record(tm_enum=tme)
  Halting_Lib.set_halting(
    halt_rec.proto.status,
    halt_steps=halt_steps,
    halt_score=None,
    from_state=state_in,
    from_symbol=symbol_in,
  )
  children.append(halt_rec)
  return children


def expand_files(
  infiles: Iterable[Path | str],
  outfile: Path | str,
  *,
  allow_no_halt: bool = False,
  quiet: bool = False,
) -> tuple[int, int]:
  """Expand all TMs from infiles and write their TNF children to outfile.
  Returns (num_parents, num_children).
  """
  start_time = time.time()
  num_parents = 0
  num_children = 0

  with IO.Writer(outfile) as writer:
    for infile in infiles:
      infile = Path(infile)
      with IO.open_file(infile, "rt") as f:
        for line_num, raw_line in enumerate(f, 1):
          line = raw_line.strip()
          if not line or line.startswith("#"):
            continue
          children = parse_and_expand_line(
            line,
            allow_no_halt=allow_no_halt,
            source_info=f"{infile}:{line_num}",
          )
          num_parents += 1
          for child_rec in children:
            writer.write_record(child_rec)
            num_children += 1

  if not quiet:
    elapsed = time.time() - start_time
    print(f"Expanded {num_parents:_} TMs into {num_children:_} TNF children -> {outfile} ({elapsed:.2f}s)")

  return num_parents, num_children


def main():
  parser = argparse.ArgumentParser(description="Expand TMs listed in input files into all of their TNF children.")
  parser.add_argument(
    "infiles",
    nargs="+",
    type=Path,
    help="Input files with lines 'TM halt_steps halt_on_state halt_on_symbol'.",
  )
  parser.add_argument(
    "--outfile",
    "-o",
    type=Path,
    required=True,
    help="Output file to write expanded TNF children.",
  )
  parser.add_argument(
    "--allow-no-halt",
    action="store_true",
    help="Allow enumerating machines without halt states.",
  )
  parser.add_argument(
    "--quiet",
    "-q",
    action="store_true",
    help="Suppress summary output.",
  )
  args = parser.parse_args()

  expand_files(
    args.infiles,
    args.outfile,
    allow_no_halt=args.allow_no_halt,
    quiet=args.quiet,
  )


if __name__ == "__main__":
  main()
