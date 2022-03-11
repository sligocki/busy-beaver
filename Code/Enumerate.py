#! /usr/bin/env python3
#
# Enumerate.py
#
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

from Common import Exit_Condition, GenContainer
import Halting_Lib
import IO
from Macro import Block_Finder, Turing_Machine
import Macro_Simulator
import Output_Machine
import Turing_Machine as old_tm_mod
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
  """Holds enumeration state information for checkpointing."""
  def __init__(self, options, stack, writer, pout):
    self.options = options

    # Main TM attributes
    # I/O info
    self.writer = writer
    self.pout = pout
    self.save_freq = options.save_freq
    self.checkpoint_filename = options.checkpoint
    self.backup_checkpoint_filename = self.checkpoint_filename + ".bak"

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
    self.num_quasihalt = 0
    self.num_infinite = 0
    self.num_unknown = 0
    self.max_sim_time_s = 0.0

  def __getstate__(self):
    """Gets state of TM for checkpoint file."""
    d = self.__dict__.copy()
    del d["pout"]
    del d["writer"]
    if self.randomize:
      del d["random"]
      d["random_state"] = self.random.getstate()
    return d

  def __setstate__(self, d):
    """Resets state of TM from checkpoint file."""
    if d["randomize"]:
      d["random"] = random.Random()
      d["random"].setstate(d["random_state"])
      del d["random_state"]
    self.__dict__ = d

  def continue_enum(self):
    """
    Pull one machine off of the stack and simulate it, perhaps creating more
    machines to push back onto the stack.
    """
    self.start_time = time.time()
    last_time = self.start_time

    while True:
      cur_time = time.time()

      if cur_time - last_time > 120:
        self.stack.print_stats()
        last_time = cur_time

      if self.options.num_enum and self.tm_num >= self.options.num_enum:
        self.pout.write("Ran requested number of TMs...\n");
        break

      # While we have machines to run, pop one off the stack ...
      tm = self.stack.pop_job()

      if not tm:
        # tm == None is the indication that we have no more machines to run.
        self.pout.write("Ran out of TMs...\n");
        break

      if self.options.debug:
        print("----- Debug - Current TM:",Output_Machine.display_ttable(tm.get_TTable()))
        sys.stdout.flush()

      # Periodically save state
      if (self.tm_num % self.save_freq) == 0:
        self.save()

      # ... and run it.
      start_time = time.time()
      tm_record = self.run(tm)
      sim_time = time.time() - start_time
      self.max_sim_time_s = max(sim_time, self.max_sim_time_s)

      self.add_result(tm, tm_record)

    # Save any remaining machines on the stack.
    if self.options.num_enum:
      tm = self.stack.pop_job()
      while tm:
        tm_record = IO.create_record(tm.get_TTable())
        # Empty tm_record (no filter results) indicates that the TM hasn't been run.
        self.add_result(tm, tm_record)
        tm = self.stack.pop_job()

    # Done
    self.save()

  def save(self):
    """Save a checkpoint file so that computation can be restarted if it fails."""
    self.end_time = time.time()

    if self.pout:
      # Print out statistical data
      self.pout.write("%s -" % self.tm_num)
      self.pout.write(" %s %s %s %s -" % (
        self.num_halt, self.num_quasihalt, self.num_infinite, self.num_unknown))
      self.pout.write(" %.0fms " % (self.max_sim_time_s * 1000,))
      self.pout.write(" (%.2fs)\n" % (self.end_time - self.start_time,))
      self.pout.flush()

      # Note: We are overloading self.pout = None to mean don't write any output
      # files.
      if not self.options.no_checkpoint:
        # Backup old checkpoint file (in case the new checkpoint is interrupted
        # in mid-write)
        if os.path.exists(self.checkpoint_filename):
          shutil.move(self.checkpoint_filename, self.backup_checkpoint_filename)
        # Save checkpoint file
        f = open(self.checkpoint_filename, "wb")
        pickle.dump(self, f)
        f.close()

    # Restart timer and time stats.
    self.start_time = time.time()
    self.max_sim_time_s = 0.0

  def run(self, tm) -> io_pb2.TMRecord:
    """Simulate TM"""
    tm_record = IO.create_record(tm.get_TTable())
    try:
      if self.options.time > 0:
        Macro_Simulator.run_timer(tm.get_TTable(), self.options, tm_record,
                                  self.options.time)
      else:
        Macro_Simulator.run_options(tm.get_TTable(), self.options, tm_record)
    except:
      print("ERROR: Exception raised while simulating TM:",
            Output_Machine.display_ttable(tm.get_TTable()), file=sys.stderr)
      raise
    return tm_record

  def add_transitions(self, old_tm, state_in, symbol_in):
    """Push Turing Machines with each possible transition at this state and symbol"""
    # 'max_state' and 'max_symbol' are the state and symbol numbers for the
    # smallest state/symbol not yet written (i.e. available to add to TTable).
    max_state  = old_tm.get_num_states_available()
    max_symbol = old_tm.get_num_symbols_available()
    num_dirs = old_tm.num_dirs_available

    # If this is the last undefined cell, then it must be a halt, so only try
    # other values for cell if this is not the last undefined cell.
    # (Or if we are explicitly enumerating machines without halt states.
    # For example, while searching for Beeping Busy Beavers.)
    if self.options.allow_no_halt or old_tm.num_empty_cells > 1:
      # 'state_out' in [0, 1, ... max_state] == xrange(max_state + 1)
      new_tms = []
      for state_out in range(max_state + 1):
        for symbol_out in range(max_symbol + 1):
          for direction_out in range(2 - num_dirs, 2):  # If only one dir available, default to R.
            new_tm = copy.deepcopy(old_tm)
            new_tm.add_cell(state_in , symbol_in ,
                            state_out, symbol_out, direction_out)
            new_tms.append(new_tm)

      # If we are randomizing TM order, do so
      if self.randomize:
        self.random.shuffle(new_tms)

      # Push the list of TMs onto the stack
      self.stack.push_jobs(new_tms)

  def add_result(self, tm, tm_record : io_pb2.TMRecord):
    # Update stats
    self.tm_num += 1
    if not tm_record.status.halt_status.is_decided:
      self.num_unknown += 1

    elif tm_record.status.halt_status.is_halting:
      self.num_halt += 1
      # All halting machines (during enumeration) are actually reaching
      # undefined cells.
      # Push all the possible non-halting transitions onto the stack.
      self.add_transitions(tm,
                           state_in  = tm_record.status.halt_status.from_state,
                           symbol_in = tm_record.status.halt_status.from_symbol)
      # Modify this TM to explicitly halt on this transition so that when we
      # save it as halting below the ttable reflects that.
      tm.set_halt(state_in  = tm_record.status.halt_status.from_state,
                  symbol_in = tm_record.status.halt_status.from_symbol)
      tm_record.tm.ttable_packed = IO.Proto.pack_ttable(tm.get_TTable())

    elif tm_record.status.quasihalt_status.is_quasihalting:
      self.num_quasihalt += 1

    else:
      self.num_infinite += 1

    self.writer.write_record(tm_record)

def initialize_stack(options, stack):
  if options.infilename:
    # Initialize with all machines from infile.
    if options.informat == "protobuf":
      with open(options.infilename, "rb") as infile:
        for tm_record in IO.Proto.Reader(infile):
          tm = old_tm_mod.Turing_Machine(
            IO.Proto.unpack_ttable(tm_record.tm.ttable_packed))
          stack.push_job(tm)
    elif options.informat == "text":
      with open(options.infilename, "r") as infile:
        for io_record in IO.Text.ReaderWriter(infile, None):
          tm = old_tm_mod.Turing_Machine(io_record.ttable)
          stack.push_job(tm)
  else:
    # If no infile is specified, then default to the NxM blank TM.
    blank_tm = old_tm_mod.Turing_Machine(options.states, options.symbols, options.first_1rb)
    stack.push_job(blank_tm)

def main(args):
  start_time = time.time()

  ## Parse command line options.
  usage = "usage: %prog --states= --symbols= [options]"
  parser = OptionParser(usage=usage)
  req_parser = OptionGroup(parser, "Required Parameters")  # Oxymoron?
  req_parser.add_option("--states",  type=int, help="Number of states")
  req_parser.add_option("--symbols", type=int, help="Number of symbols")
  parser.add_option_group(req_parser)

  enum_parser = OptionGroup(parser, "Enumeration Options")
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
  enum_parser.add_option("-d","--debug", action="store_true", default=False)
  parser.add_option_group(enum_parser)

  Macro_Simulator.add_option_group(parser)

  out_parser = OptionGroup(parser, "Output Options")
  enum_parser.add_option("--no-output", action="store_true", default=False,
                         help="Don't generate any output.")
  out_parser.add_option("--outfile", dest="outfilename", metavar="OUTFILE",
                        help="Output file name "
                        "[Default: Enum.STATES.SYMBOLS.STEPS.out.txt/pb]")
  out_parser.add_option("--infile", dest="infilename",
                        help="If specified, enumeration is started from "
                        "these input machines instead of the single empty "
                        "Turing Machine.")
  out_parser.add_option("--outformat",
                        choices = ["text", "protobuf"], default="text",
                        help="Format to write --outfile.")
  out_parser.add_option("--informat",
                        choices = ["text", "protobuf"], default="text",
                        help="Format to read --infile.")

  out_parser.add_option("--force", action="store_true", default=False,
                        help="Force overwriting outfile (don't ask).")
  out_parser.add_option("--no-checkpoint", action="store_true", default=False,
                        help="Don't save a checkpoint file.")
  out_parser.add_option("--checkpoint", metavar="FILE",
                        help="Checkpoint file name [Default: OUTFILE.check]")
  out_parser.add_option("--save-freq", type=int, default=100000, metavar="FREQ",
                        help="Freq to save checkpoints [Default: %default]")
  parser.add_option_group(out_parser)

  (options, args) = parser.parse_args(args)

  ## Enforce required parameters
  if not options.states or not options.symbols:
    parser.error("--states= and --symbols= are required parameters")

  ## Set complex defaults
  if options.randomize and not options.seed:
    options.seed = int(1000*time.time())

  if not options.outfilename:
    if options.outformat == "protobuf":
      suffix = "pb"
    elif options.outformat == "text":
      suffix = "txt"
    options.outfilename = "Enum.%d.%d.%s.out.%s" % (
      options.states, options.symbols, options.max_loops, suffix)

  if not options.checkpoint:
    options.checkpoint = options.outfilename + ".check"

  pout = None
  if not options.no_output:
    pout = sys.stdout

  ## Print command line
  if pout:
    pout.write("Enumerate.py --states=%d --symbols=%d --max-loops=%s --time=%f" \
      % (options.states, options.symbols, options.max_loops, options.time))
    if options.randomize:
      pout.write(" --randomize --seed=%d" % options.seed)

    pout.write(" --outfile=%s" % options.outfilename)
    pout.write(" --checkpoint=%s --save-freq=%d" % (options.checkpoint, options.save_freq))
    pout.write("\n")

  # Set up work queue and populate with blank machine.
  if options.breadth_first:
    stack = Work_Queue.Basic_FIFO_Work_Queue()
  else:
    stack = Work_Queue.Basic_LIFO_Work_Queue()
  initialize_stack(options, stack)

  # Set up output
  if os.path.exists(options.outfilename) and not options.force:
    parser.error("Output file already exits. Delete or use --force")

  if options.outformat == "protobuf":
    outfile = open(options.outfilename, "wb")
    writer = IO.Proto.Writer(outfile)

  elif options.outformat == "text":
    outfile = open(options.outfilename, "w")
    writer = IO.Text.ReaderWriter(None, outfile)

  ## Enumerate machines
  enumerator = Enumerator(options, stack, writer, pout)
  enumerator.continue_enum()

  outfile.close()
  os.remove(enumerator.checkpoint_filename)
  os.remove(enumerator.backup_checkpoint_filename)

if __name__ == "__main__":
  main(sys.argv[1:])
