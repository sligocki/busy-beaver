#! /usr/bin/env python3

import argparse
import math
from pathlib import Path

import CPS
import IO
from Macro import Turing_Machine

import io_pb2


def filter(tm_record, block_size : int, window_size : int,
           max_steps : int, max_iters : int, max_configs : int, max_edges : int) -> None:
  CPS.filter(tm_record.tm(), block_size, window_size,
             max_steps, max_iters, max_configs, max_edges,
             tm_record.proto.filter.closed_graph.result,
             tm_record.proto.status)

def filter_all(tm_record, args) -> None:
  tm_record.clear_proto()
  info = tm_record.proto.filter.closed_graph
  with IO.Timer(info.result):
    if args.max_block_size:
      info.parameters.min_block_size = args.min_block_size
      info.parameters.max_block_size = args.max_block_size
    info.parameters.search_all_windows = bool(args.max_window_size)
    info.parameters.max_steps = args.max_steps
    info.parameters.max_iters = args.max_iters
    info.parameters.max_configs = args.max_configs
    info.parameters.max_edges = args.max_edges

    if not args.max_window_size:
      # Use "standard" 3*block_size window.
      for block_size in range(args.min_block_size, args.max_block_size + 1):
        window_size = 3 * block_size
        filter(tm_record, block_size, window_size,
               args.max_steps, args.max_iters, args.max_configs, args.max_edges)
        if info.result.success:
          return

    else:
      # Use "vertical scan" starting with smallest windows
      for window_size in range(2, args.max_window_size + 1):
        max_block_size = window_size // 2
        for block_size in range(1, max_block_size + 1):
          filter(tm_record, block_size, window_size,
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
  parser.add_argument("--max-window-size", type=int)

  # The vast majority of TMs are decided within 1/10 of these parameters.
  # A few TMs are not decided (even with inf maxes) but take a looong time to
  # fail (30min+). So we restrict these to keep max time down.
  parser.add_argument("--max-steps", type=int, default=1_000_000)
  parser.add_argument("--max-iters", type=int, default=500)
  parser.add_argument("--max-configs", type=int, default=10_000)
  parser.add_argument("--max-edges", type=int, default=10_000)
  args = parser.parse_args()

  if args.block_size:
    assert not args.max_window_size
    args.min_block_size = args.block_size
    args.max_block_size = args.block_size
  assert args.max_block_size or args.max_window_size, "Must specify either --block-size or --max-block-size or --max-window-size"

  with IO.Writer(args.outfile) as writer:
    with IO.Reader(args.infile) as reader:
      for tm_record in reader:
        filter_all(tm_record, args)
        writer.write_record(tm_record)

if __name__ == "__main__":
  main()
