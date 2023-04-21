#! /usr/bin/env python3
"""
Re-simulate TM using Macro Simulator with same block size and num loops in input data.
Useful for updating format, using new techniques, adding step computation, etc.
"""

import argparse
from pathlib import Path

import IO
from Macro import Simulator, Turing_Machine
import Macro_Simulator


def re_sim(tm_record):
  sim_params = tm_record.proto.filter.simulator.parameters
  sim_result = tm_record.proto.filter.simulator.result

  tm = tm_record.tm()
  if sim_params.block_size > 1:
    tm = Turing_Machine.Block_Macro_Machine(tm, sim_params.block_size)
  if sim_params.has_blocksymbol_macro:
    tm = Turing_Machine.Backsymbol_Macro_Machine(tm)

  # TODO: Replace this all with a function that just takes sim_params and produces sim_results?
  options = Simulator.create_default_options()
  options.max_loops = sim_params.max_loops
  options.tape_limit = sim_params.max_tape_blocks
  # Time is non-deterministic ... also this is not actually used by simulate_machine
  options.time = 0.0
  options.recursive = True
  options.compute_steps = True
  # Only use experimental Linear Rule code if we actually proved a Linear Rule :)
  if sim_result.num_linear_rules_proven > 0:
    options.recursive = True
    options.exp_linear_rules = True
    options.compute_steps = False
  sim_result.Clear()
  tm_record.proto.status.Clear()
  Macro_Simulator.simulate_machine(tm, options,
                                   tm_record.proto.filter.simulator,
                                   tm_record.proto.status)
  return tm_record


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("infile", type=Path)
  parser.add_argument("outfile", type=Path)
  args = parser.parse_args()

  with IO.Proto.Writer(args.outfile) as writer:
    with IO.Reader(args.infile) as reader:
      for tm_record in reader:
        tm_record = re_sim(tm_record)
        writer.write_record(tm_record)

main()
