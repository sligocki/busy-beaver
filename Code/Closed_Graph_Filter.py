#! /usr/bin/env python3

import argparse
import math
from pathlib import Path

import Closed_Graph
import IO
import Halting_Lib
from Macro import Turing_Machine

import io_pb2


def filter(tm_record, block_size : int, offset : int,
           max_configs : int, max_steps_per_rule : int) -> bool:
  info = tm_record.proto.filter.closed_graph
  with IO.Timer(info.result):
    success, num_iters, num_configs = Closed_Graph.test_closed_graph(
      tm_record.tm(), block_size=block_size, offset=offset,
      max_configs=max_configs, max_steps_per_rule=max_steps_per_rule)
    if success:
      info.parameters.block_size = block_size
      info.parameters.offset = offset
      info.parameters.max_num_configs = max_configs
      info.parameters.max_steps_per_rule = max_steps_per_rule
      info.result.success = True
      info.result.num_iters = num_iters
      info.result.num_configs = num_configs
      Halting_Lib.set_not_halting(tm_record.proto.status, io_pb2.INF_CLOSED_GRAPH)
      # Note: quasihalting result is not computed when using Closed Graph filters.
      tm_record.proto.status.quasihalt_status.is_decided = False
      return True
  return False

def filter_block_size(tm_record, block_size, args):
  if args.all_offsets:
    for offset in range(block_size):
      if filter(tm_record, block_size, offset,
                args.max_configs, args.max_steps_per_rule):
        return True
    return False

  else:
    return filter(tm_record, block_size, args.offset,
                  args.max_configs, args.max_steps_per_rule)

def filter_all(tm_record, args):
  if args.max_block_size:
    for block_size in range(args.min_block_size, args.max_block_size + 1):
      if filter_block_size(tm_record, block_size, args):
        return True
    return False

  else:
    return filter_block_size(tm_record, args.block_size, args)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--infile", type=Path, required=True)
  parser.add_argument("--outfile", type=Path, required=True)

  parser.add_argument("--max-configs", type=int, required=True)
  parser.add_argument("--block-size", type=int)
  parser.add_argument("--offset", type=int, default=0)
  parser.add_argument("--max-steps-per-rule", type=int, default=100_000)

  parser.add_argument("--min-block-size", type=int, default=1)
  parser.add_argument("--max-block-size", type=int,
                      help="If set, try all block sizes between "
                      "min_block_size and max_block_size.")
  parser.add_argument("--all-offsets", action="store_true",
                      help="Try all offsets for a given block size.")
  args = parser.parse_args()

  with IO.Proto.Writer(args.outfile) as writer:
    with IO.Reader(args.infile) as reader:
      for tm_record in reader:
        filter_all(tm_record, args)
        writer.write_record(tm_record)

if __name__ == "__main__":
  main()
