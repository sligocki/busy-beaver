# Merge halt annotations (step counts, sigma scores, etc.) into bb5_verified_enumeration.csv.gz.

import argparse
import datetime
import sys

import pandas as pd

def log(*messages):
  print(f"{datetime.datetime.now().isoformat()} ", *messages, file=sys.stderr)
  sys.stderr.flush()


def merge(verified_enum_filename, halt_results_filename, outfilename):
  log("Starting")

  halt = pd.read_csv(halt_results_filename, sep=" ",
    names=["machine_with_halt_transition", "status2", "steps", "sigma", "space"],
    usecols=["machine_with_halt_transition", "steps", "sigma", "space"],
    dtype={"steps": "Int64", "sigma": "Int64", "space": "Int64"})
  log(f"Loaded halt annotations: {len(halt):_} rows")

  enum = pd.read_csv(verified_enum_filename)
  log(f"Loaded verified enum: {len(enum):_} rows")

  # Convert machines with explicit halt transitions back into unresolved
  # versions used in enum file.
  halt["machine"] = halt["machine_with_halt_transition"].str.replace("1RZ", "---")

  # Merge halting TM annotations
  enum = enum.merge(halt, how="left", on="machine", validate="1:1")
  log(f"Merged halt annot into enum: {len(enum):_} rows")

  # Check all halting TMs are annotated
  assert not enum[enum["status"] == "halt"].isnull().values.any()

  enum.to_csv(outfilename,
              columns=["machine", "status", "decider",
                       "sigma", "space", "steps", "machine_with_halt_transition"],
              index=False, lineterminator="\n")
  log(f"Wrote {len(enum):_} rows")

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("verified_enum")
  parser.add_argument("halt_results")
  parser.add_argument("out_csv")
  args = parser.parse_args()

  merge(args.verified_enum, args.halt_results, args.out_csv)

main()