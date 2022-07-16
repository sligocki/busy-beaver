#! /usr/bin/env python3
"""
Run one of the CTL algorithms - CTL1, CTL2, CTL3, CTL4.
"""

import argparse
from optparse import OptionParser
from pathlib import Path

from Common import GenContainer
import IO
import CTL1
import CTL2
import CTL3
import CTL4
import Halting_Lib
from Macro import Simulator, Turing_Machine

import io_pb2


def get_module(type):
  if type == "CTL1":
    return CTL1
  if type == "CTL2":
    return CTL2
  if type == "CTL3":
    return CTL3
  if type == "CTL4":
    return CTL4
  raise Exception(type)

def get_proto(type, tm_record):
  if type == "CTL1":
    return tm_record.proto.filter.ctl.ctl_as
  if type == "CTL2":
    return tm_record.proto.filter.ctl.ctl_as_b
  if type == "CTL3":
    return tm_record.proto.filter.ctl.ctl_a_bs
  if type == "CTL4":
    return tm_record.proto.filter.ctl.ctl_as_b_c
  raise Exception(type)


def filter(tm_record, type, block_size, offset, cutoff, use_backsymbol):
  info = get_proto(type, tm_record)
  with IO.Timer(info.result):
    module = get_module(type)
    success, num_iters = module.test_CTL(
      tm_record.tm(), cutoff=cutoff, block_size=block_size, offset=offset,
      use_backsymbol=use_backsymbol)
    if success:
      info.parameters.block_size = block_size
      info.parameters.offset = offset
      info.parameters.cutoff = cutoff
      info.result.success = True
      info.result.num_iters = num_iters
      Halting_Lib.set_not_halting(tm_record.proto.status, io_pb2.INF_CTL)
      # Note: quasihalting result is not computed when using CTL filters.
      tm_record.proto.status.quasihalt_status.is_decided = False
      return True
  return False

def filter_block_size(tm_record, block_size, args):
  if args.all_offsets:
    for offset in range(block_size):
      if filter(tm_record, args.type,
                block_size=block_size, offset=offset, cutoff=args.cutoff,
                use_backsymbol=(not args.no_backsymbol)):
        return True
    return False

  else:
    return filter(tm_record, args.type, block_size, args.offset, args.cutoff,
                  use_backsymbol=(not args.no_backsymbol))

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

  parser.add_argument("--type", choices=["CTL1", "CTL2", "CTL3", "CTL4"], required=True)
  parser.add_argument("--block-size", type=int)
  parser.add_argument("--offset", type=int, default=0)
  parser.add_argument("--no-backsymbol", action="store_true")
  parser.add_argument("--cutoff", type=int, default=200,
                      help="Number of loops to run before starting CTL algorithm.")

  parser.add_argument("--min-block-size", type=int, default=1)
  parser.add_argument("--max-block-size", type=int)
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
