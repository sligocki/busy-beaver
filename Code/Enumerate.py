#! /usr/bin/env python3
"""
This is a Busy Beaver Turing machine enumerator.

It enumerates all Busy Beavers for given # of states and symbols, runs the
Macro Machine simulator, gathers statistics, and outputs all of the machines
like Generate does.
"""

import collections
import copy
import pickle as pickle
import math
from optparse import OptionParser, OptionGroup
import os
from pprint import pprint
import random
import shutil
import sys
import time

import Halting_Lib
import IO
from IO.TM_Record import TM_Record
from Macro import Block_Finder, Turing_Machine
import Macro_Simulator
import TM_Enum
import Work_Queue

import io_pb2


def long_to_eng_str(number, left, right):
  if number != 0:
    expo = int(math.log(abs(number), 10))
    number_str = str(int(number / 10**(expo - right)))

    if number < 0:
      return "-%s.%se+%d" % (number_str[1     :1+left      ],
                             number_str[1+left:1+left+right],
                             expo)
    else:
      return "%s.%se+%d" % (number_str[0     :0+left      ],
                            number_str[0+left:0+left+right],
                            expo)
  else:
    return "0.%se+00" % ("0" * right)

class Enumerator(object):
  def __init__(self, options, stack, writer, pout):
    self.options = options

    # Main TM attributes
    # I/O info
    self.writer = writer
    self.pout = pout
    self.save_freq = options.save_freq

    # Stack of TM descriptions to simulate
    assert isinstance(stack, Work_Queue.Work_Queue)
    self.stack = stack

    # If we are randomizing the stack order
    self.randomize = options.randomize
    if self.randomize:
      self.random = random.Random()
      self.random.seed(options.seed)

    # Statistics
    self.tm_num = 0
    self.num_halt = 0
    self.num_inf_quasi_unknown = 0
    self.num_quasihalt = 0
    self.num_infinite = 0
    self.num_unknown = 0
    self.max_sim_time_s = 0.0
    self.start_time = time.time()

  def continue_enum(self):
    """
    Pull one machine off of the stack and simulate it, perhaps creating more
    machines to push back onto the stack.
    """
    while True:
      if self.options.num_enum and self.tm_num >= self.options.num_enum:
        self.pout.write("Ran requested number of TMs...\n");
        break

      # While we have machines to run, pop one off the stack ...
      tm_record = self.stack.pop_job()

      if not tm_record:
        break

      if self.options.debug_print_current:
        print("----- Debug - Current TM:", tm_record.ttable_str())
        sys.stdout.flush()

      # Periodically save state
      if (self.tm_num % self.save_freq) == 0:
        self.save()

      # ... and run it.
      start_time = time.time()
      self.run(tm_record)
      sim_time = time.time() - start_time
      self.max_sim_time_s = max(sim_time, self.max_sim_time_s)

      self.add_result(tm_record)

    # Save any remaining machines on the stack.
    if self.options.num_enum:
      tm_record = self.stack.pop_job()
      while tm_record:
        # Empty tm_record (no filter results) indicates that the TM hasn't been run.
        self.add_result(tm_record)
        tm_record = self.stack.pop_job()

  def save(self):
    """Write stats."""
    # Actually write to disk.
    self.writer.flush()

    if self.pout:
      # Print out statistical data
      self.pout.write(f"{self.tm_num:_} - "
                      f"halt {self.num_halt:_} (qhalt {self.num_quasihalt:_}) "
                      f"inf {self.num_infinite:_} (qunk {self.num_inf_quasi_unknown:_}) "
                      f"unk {self.num_unknown:_} - "
                      f"max {self.max_sim_time_s * 1000:_.0f}ms / "
                      f"total {time.time() - self.start_time:_.2f}s\n")
      self.pout.flush()

    # Restart timer and time stats.
    self.start_time = time.time()
    self.max_sim_time_s = 0.0

  def run(self, tm_record : TM_Record) -> TM_Record:
    """Simulate TM"""
    try:
      if self.options.time > 0:
        Macro_Simulator.run_timer(tm_record, self.options,
                                  self.options.time)
      else:
        Macro_Simulator.run_options(tm_record, self.options)
    except Exception as e:
      print("ERROR: Exception raised while simulating TM:",
            tm_record.ttable_str(), file=sys.stderr)
      print(e)
      tm_record.proto.filter.simulator.result.unknown_info.threw_exception = True
      # raise
    return tm_record

  def expand_undefined_transition(self, old_tm_record : TM_Record) -> None:
    """Push Turing Machines with each possible transition at this state and symbol"""
    assert old_tm_record.is_halting()
    state_in = old_tm_record.proto.status.halt_status.from_state
    symbol_in = old_tm_record.proto.status.halt_status.from_symbol
    new_tms = [TM_Record(tm_enum = tm_enum) for tm_enum in
               old_tm_record.tm_enum().enum_children(state_in, symbol_in)]

    if new_tms:
      if self.randomize:
        self.random.shuffle(new_tms)

      self.stack.push_jobs(new_tms)

  def add_result(self, tm_record : TM_Record) -> None:
    # Update stats
    self.tm_num += 1
    if tm_record.is_unknown_halting():
      self.num_unknown += 1

    elif tm_record.is_halting():
      self.num_halt += 1
      # All halting machines (during enumeration) are actually reaching
      # undefined cells.
      # Push all the possible non-halting transitions onto the stack.
      self.expand_undefined_transition(tm_record)
      # Modify this TM to explicitly halt on this transition so that when we
      # save it as halting below the ttable reflects that.
      tm_record.standardize_halt_trans()

    elif tm_record.is_unknown_quasihalting():
      self.num_inf_quasi_unknown += 1

    elif tm_record.is_quasihalting():
      self.num_quasihalt += 1

    else:
      self.num_infinite += 1

    self.writer.write_record(tm_record)

def enum_initial_tms(options):
  if options.infilename:
    # Initialize with all machines from infile.
    with IO.Reader(options.infilename) as reader:
      for tm_record in reader:
        # Clear previous results, so that we only see the results from this run.
        tm_record.proto.ClearField("status")
        tm_record.proto.ClearField("filter")
        yield tm_record
  else:
    assert options.states and options.symbols, (options.states, options.symbols)
    # If no infile is specified, then default to the NxM blank TM.
    blank_tm = TM_Enum.blank_tm_enum(options.states, options.symbols,
                                     first_1rb = options.first_1rb,
                                     allow_no_halt = options.allow_no_halt)
    tm_record = TM_Record(tm_enum = blank_tm)
    yield tm_record

def main(args):
  start_time = time.time()

  ## Parse command line options.
  usage = "usage: %prog [options]"
  parser = OptionParser(usage=usage)
  enum_parser = OptionGroup(parser, "Enumeration Options")
  enum_parser.add_option("--states",  type=int, help="Number of states")
  enum_parser.add_option("--symbols", type=int, help="Number of symbols")
  enum_parser.add_option("--breadth-first", action="store_true", default=False,
                         help="Run search breadth first (only works in single "
                         "process mode).")
  enum_parser.add_option("--num-enum", type=int, metavar="NUM",
                         help="Number of machines to enumerate all unfinished "
                         "machines from queue are also output so that you can "
                         "continue with --infile.")
  enum_parser.add_option("--randomize", action="store_true", default=False,
                         help="Randomize the order of enumeration.")
  enum_parser.add_option("--seed", type=int, help="Seed to randomize with.")
  enum_parser.add_option("--allow-no-halt", action="store_true", default=False,
                         help="Search for Beep Busy Beaver (allow enumerating machines without halt states).")
  enum_parser.add_option("--no-first-1rb", dest="first_1rb",
                         action="store_false", default=True,
                         help="Allow first transition to be anything (not just restricted to A1->1RB).")
  enum_parser.add_option("--debug-print-current", dest="debug_print_current", action="store_true", default=False)
  parser.add_option_group(enum_parser)

  Macro_Simulator.add_option_group(parser)

  out_parser = OptionGroup(parser, "Output Options")
  enum_parser.add_option("--no-output", action="store_true", default=False,
                         help="Don't generate any output.")
  out_parser.add_option("--outfile", dest="outfilename", metavar="OUTFILE",
                        help="Output file name (required)")
  out_parser.add_option("--infile", dest="infilename",
                        help="If specified, enumeration is started from "
                        "these input machines instead of the single empty "
                        "Turing Machine.")

  out_parser.add_option("--force", action="store_true", default=False,
                        help="Force overwriting outfile (don't ask).")
  out_parser.add_option("--save-freq", type=int, default=100_000, metavar="FREQ",
                        help="Freq to save output and write stats [Default: %default]")
  parser.add_option_group(out_parser)

  (options, args) = parser.parse_args(args)

  ## Set complex defaults
  if options.randomize and not options.seed:
    options.seed = int(1000*time.time())

  if not options.outfilename:
    parser.error("--outfile is required")

  pout = None
  if not options.no_output:
    pout = sys.stdout

  if not options.max_block_size:
    options.max_block_size = 5

  # Set up work queue and populate with blank machine.
  if options.breadth_first:
    stack = Work_Queue.Basic_FIFO_Work_Queue()
  else:
    stack = Work_Queue.Basic_LIFO_Work_Queue()

  # Set up output
  if os.path.exists(options.outfilename) and not options.force:
    parser.error("Output file already exits. Delete or use --force")

  with IO.Proto.Writer(options.outfilename) as writer:
    ## Enumerate machines
    enumerator = Enumerator(options, stack, writer, pout)

    # Push input TMs one at a time so we don't blow up memory if there are a
    # lot of input machines.
    for tm_record in enum_initial_tms(options):
      stack.push_job(tm_record)
      enumerator.continue_enum()

    # Done
    enumerator.save()

if __name__ == "__main__":
  main(sys.argv[1:])
