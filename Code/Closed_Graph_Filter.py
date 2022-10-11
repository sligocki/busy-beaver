#! /usr/bin/env python3

import argparse
import math
from pathlib import Path

import Closed_Graph
import IO
from Macro import Turing_Machine

import io_pb2


def filter(tm_record, block_size : int, subtape_size : int,
           max_steps : int, max_iters : int, max_configs : int, max_edges : int) -> None:
  Closed_Graph.filter(tm_record.tm(), block_size, subtape_size,
                      max_steps, max_iters, max_configs, max_edges,
                      tm_record.proto.filter.closed_graph.result,
                      tm_record.proto.status)

def filter_all(tm_record, args) -> None:
  tm_record.clear_proto()
  info = tm_record.proto.filter.closed_graph
  with IO.Timer(info.result):
    info.parameters.min_block_size = args.min_block_size
    info.parameters.max_block_size = args.max_block_size
    info.parameters.searched_all_subtapes = False
    info.parameters.max_steps = args.max_steps
    info.parameters.max_iters = args.max_iters
    info.parameters.max_configs = args.max_configs
    info.parameters.max_edges = args.max_edges
    for block_size in range(args.min_block_size, args.max_block_size + 1):
      subtape_size = 3 * block_size
      filter(tm_record, block_size, subtape_size,
             args.max_steps, args.max_iters, args.max_configs, args.max_edges)
      if info.result.success:
        return


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--infile", type=Path, required=True)
  parser.add_argument("--outfile", type=Path, required=True)

  parser.add_argument("--block-size", type=int)
  parser.add_argument("--min-block-size", type=int, default=1)
  parser.add_argument("--max-block-size", type=int,
                      help="If set, try all block sizes between "
                      "--min-block-size and --max-block-size (inclusive).")

  # The vast majority of TMs are decided within 1/10 of these parameters.
  # A few TMs are not decided (even with inf maxes) but take a looong time to
  # fail (30min+). So we restrict these to keep max time down.
  parser.add_argument("--max-steps", type=int, default=1_000_000)
  parser.add_argument("--max-iters", type=int, default=500)
  parser.add_argument("--max-configs", type=int, default=10_000)
  parser.add_argument("--max-edges", type=int, default=10_000)
  args = parser.parse_args()

  if args.block_size:
    args.min_block_size = args.block_size
    args.max_block_size = args.block_size
  assert args.max_block_size, "Must specify either --block-size or --max-block-size"

  with IO.Proto.Writer(args.outfile) as writer:
    with IO.Reader(args.infile) as reader:
      for tm_record in reader:
        filter_all(tm_record, args)
        writer.write_record(tm_record)

if __name__ == "__main__":
  main()
