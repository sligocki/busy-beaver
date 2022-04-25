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


def build_tm(base_tm, block_size, offset):
  tm = base_tm
  if block_size > 1:
    tm = Turing_Machine.Block_Macro_Machine(tm, block_size, offset)
  tm = Turing_Machine.Backsymbol_Macro_Machine(tm)
  return tm

def build_config(tm, cutoff):
  # Default options
  parser = OptionParser()
  Simulator.add_option_group(parser)
  options, args = parser.parse_args([])
  options.prover = False

  sim = Simulator.Simulator(tm, options)
  sim.seek(cutoff)

  if sim.op_state != Turing_Machine.RUNNING:
    return False

  tape = [None, None]

  for d in range(2):
    tape[d] = [block.symbol for block in reversed(sim.tape.tape[d])
               if block.num != "Inf"]

  config = GenContainer(state=sim.state, dir=sim.dir, tape=tape)
  return config

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


def filter(tm_record, type, block_size, offset, cutoff):
  info = get_proto(type, tm_record)
  with IO.Timer(info.result):
    tm = build_tm(tm_record.tm(), block_size, offset)
    config = build_config(tm, cutoff)
    if config:
      module = get_module(type)
      if module.CTL(tm, config):
        info.parameters.block_size = block_size
        info.parameters.offset = offset
        info.result.success = True
        Halting_Lib.set_not_halting(tm_record.proto.status, io_pb2.INF_CTL)
        # Note: quasihalting result is not computed when using CTL filters.
        tm_record.proto.status.quasihalt_status.is_decided = False
        return True
  return False


def filter_all(tm_record, args):
  if args.max_block_size:
    for block_size in range(1, args.max_block_size + 1):
      for offset in range(block_size):
        # TODO: non-0 offsets are broken.
        if offset == 0:
          if filter(tm_record, args.type, block_size, offset, args.cutoff):
            return

  else:
    filter(tm_record, args.type, args.block_size, args.offset, args.cutoff)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--infile", type=Path, required=True)
  parser.add_argument("--outfile", type=Path, required=True)

  parser.add_argument("--type", choices=["CTL1", "CTL2", "CTL3", "CTL4"], required=True)
  parser.add_argument("--block-size", type=int)
  parser.add_argument("--offset", type=int, default=0)
  parser.add_argument("--cutoff", type=int, default=200,
                      help="Number of loops to run before starting CTL algorithm.")

  parser.add_argument("--max-block-size", type=int)
  args = parser.parse_args()

  with open(args.outfile, "wb") as outfile:
    writer = IO.Proto.Writer(outfile)
    with IO.Reader(args.infile) as reader:
      for tm_record in reader:
        filter_all(tm_record, args)
        writer.write_record(tm_record)

if __name__ == "__main__":
  main()
