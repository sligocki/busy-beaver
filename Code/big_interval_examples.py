#!/usr/bin/env python3
"""
Examples of computing BigInterval bounds for extremely large TM scores and steps.
User runnable script to easily add and evaluate new TMs.
"""

from optparse import OptionParser

import Halting_Lib
import IO
import Macro_Simulator
import NatExpr
import TM_Enum
from IO import TM_Record


def evaluate_tm(name: str, tm_str: str, force_block_size: int = None):
  print(f"{name}: {tm_str}")

  # 1. Setup machine and simulator options
  tm = IO.parse_tm(tm_str)
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

  # 3. Extract scores and steps
  score = NatExpr.NatExpr.wrap(Halting_Lib.get_big_int(status.halt_score))

  # 4. Print Exact Formulas
  print(f"Sigma Score Formula: {score.formula_str if hasattr(score, 'formula_str') else score}")
  if hasattr(score, "approx_str"):
    print(f"Sigma Score Approx : {score.approx_str()}")
  score_interval = score.to_BigInterval()
  print(f"Sigma Score Bound  : {score_interval}")
  print(f"Sigma Score Approx : {score_interval.approx_str()}")

  print()


def main():
  examples = [
    {"name": "6x2 t5", "tm_str": "1RB0LA_1LC1LF_0LD0LC_0LE0LB_1RE0RA_1RZ1LD"},
    {"name": "6x2 t15", "tm_str": "1RB0LD_1RC0RF_1LC1LA_0LE1RZ_1LF0RB_0RC0RE"},
    {"name": "2x6 t70", "tm_str": "1RB2LA1RA4LA5RA0LB_1LA3RA2RB1RZ3RB4LA", "force_block_size": 2},
  ]

  for ex in examples:
    evaluate_tm(**ex)


if __name__ == "__main__":
  main()
