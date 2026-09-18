#!/usr/bin/env python3
"""
Examples of computing BigInterval bounds for extremely large TM scores and steps.
User runnable script to easily add and evaluate new TMs.
"""

from optparse import OptionParser

import Macro_Simulator
from IO import TM_Record
import TM_Enum
import IO
import Halting_Lib
import NatExpr


def evaluate_tm(name: str, tm_str: str = None, filename: str = None, force_block_size: int = None):
  print("========================================")
  print(f"TM Name: {name}")
  if tm_str:
    print(f"TM Code: {tm_str}")
  elif filename:
    print(f"TM File: {filename}")
  print("========================================")

  # 1. Setup machine and simulator options
  if tm_str:
    tm = IO.parse_tm(tm_str)
  elif filename:
    tm = IO.load_tm(filename, 0)
  else:
    raise ValueError("Must provide tm_str or filename")

  tm_enum = TM_Enum.TM_Enum(tm, allow_no_halt=False)
  tm_record = TM_Record.TM_Record(tm_enum=tm_enum)

  parser = OptionParser()
  Macro_Simulator.add_option_group(parser)
  options, args = parser.parse_args([])
  options.time = 0
  options.recursive = True
  options.exp_linear_rules = True
  options.compute_steps = True
  options.max_loops = 1_000_000
  if force_block_size:
    options.block_size = force_block_size
  else:
    options.max_block_size = 100

  # 2. Run simulation
  Macro_Simulator.run_options(tm_record, options)

  status = tm_record.proto.status.halt_status
  if not status.is_halting:
    print("TM did not halt within limits.")
    print()
    return

  score = NatExpr.NatExpr.wrap(Halting_Lib.get_big_int(status.halt_score))

  # 4. Print Exact Formulas
  print("\n--- Exact Formulas (ExpInt) ---")
  print(f"Sigma Score Formula: {score.formula_str if hasattr(score, 'formula_str') else score}")
  if hasattr(score, "approx_str"):
    print(f"Sigma Score Approx : {score.approx_str()}")

  # 5. Compute and print BigInterval bounds
  print("\n--- BigInterval Bounds ---")

  score_interval = score.to_BigInterval()
  print(f"Sigma Score Bound  : {score_interval}")

  print("\n\n")


def main():
  examples = [
    {"name": "Pavel's 2022 BB(6) champion (t15)", "tm_str": "1RB0LD_1RC0RF_1LC1LA_0LE1RZ_1LF0RB_0RC0RE"},
    {"name": "Shawn's 2022 BB(6) t5", "filename": "../Machines/6x2-t5"},
    {"name": "t70 (requires block size 2)", "filename": "../Machines/2x6-t70", "force_block_size": 2},
  ]

  for ex in examples:
    evaluate_tm(**ex)


if __name__ == "__main__":
  main()
