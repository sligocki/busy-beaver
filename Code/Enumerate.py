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

try:
  import MPI_Work_Queue
  num_proc = MPI_Work_Queue.num_proc
except ImportError:
  # Allow this to work even if mpi4py is not installed.
  num_proc = 1

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
  def __init__(self, options, stack, io, pout):
    self.options = options

    # Main TM attributes
    # I/O info
    self.io = io
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
    self.num_halt = self.num_infinite = self.num_unresolved = 0
    self.best_steps = self.best_score = 0
    self.num_over_time = self.num_over_steps = self.num_over_tape = 0
    self.max_sim_time_s = 0.0

  def __getstate__(self):
    """Gets state of TM for checkpoint file."""
    d = self.__dict__.copy()
    del d["pout"]
    del d["io"]
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
        # TODO: Fix this
        self.add_unresolved(tm, Exit_Condition.NOT_RUN)
        tm = self.stack.pop_job()

    # Done
    self.save()

  def save(self):
    """Save a checkpoint file so that computation can be restarted if it fails."""
    self.end_time = time.time()

    if self.pout:
      # Print out statistical data
      self.pout.write("%s -" % self.tm_num)
      self.pout.write(" %s %s %s -" % (self.num_halt, self.num_infinite,
                                       self.num_unresolved))
      self.pout.write(" %s" % (long_to_eng_str(self.best_steps,1,3),))
      self.pout.write(" %s" % (long_to_eng_str(self.best_score,1,3),))
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

    # Restart timer
    self.start_time = time.time()

  def run(self, tm) -> io_pb2.IORecord:
    """Simulate TM"""
    tm_record = io_pb2.IORecord()
    tm_record.tm.ttable = Output_Machine.display_ttable(tm.get_TTable())
    try:
      if self.options.time > 0:
        Macro_Simulator.run_timer(tm.get_TTable(), self.options, tm_record,
                                  self.options.time)
      else:
        Macro_Simulator.run_options(tm.get_TTable(), self.options, tm_record)
    except:
      print("ERROR: Exception raised while simulating TM:",
            tm_record.tm.ttable, file=sys.stderr)
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

  def add_result(self, tm, tm_record : io_pb2.IORecord):
    sim_result = tm_record.simulator_info.result
    if sim_result.undefined_cell_info.reached_undefined_cell:
      # Push all the possible non-halting transitions onto the stack.
      self.add_transitions(tm,
                           state_in = sim_result.undefined_cell_info.state,
                           symbol_in = sim_result.undefined_cell_info.symbol)
      # Modify this TM to halt on this transition so that when we save it as
      # halting below the ttable reflects that.
      tm.set_halt(state_in = sim_result.undefined_cell_info.state,
                  symbol_in = sim_result.undefined_cell_info.symbol)

    if tm_record.status.halt_status.is_decided:
      if tm_record.status.halt_status.is_halting:
        self.add_halt(tm, tm_record.status.halt_status)
      else:
        self.add_infinite(tm, tm_record.status.halt_status.reason,
                          tm_record.status.quasihalt_status)
    else:
      self.add_unknown(tm, sim_result.unknown_info)

  def add_halt(self, tm,
               halt_info : io_pb2.HaltInfo):
    """Note a halting TM. Add statistics and output it with score/steps."""
    self.num_halt += 1
    self.tm_num += 1

    steps = Halting_Lib.get_big_int(halt_info.halt_steps)
    score = Halting_Lib.get_big_int(halt_info.halt_score)
    self.best_steps = max(self.best_steps, steps)
    self.best_score = max(self.best_score, score)

    if self.pout:
      io_record = IO.Record()
      io_record.ttable = tm.get_TTable()
      io_record.category = Exit_Condition.HALT
      io_record.category_reason = (score, steps)
      self.io.write_record(io_record)

  def add_infinite(self, tm, reason, quasihalt_status):
    """Note an infinite TM. Add statistics and output it with reason."""
    self.num_infinite += 1
    self.tm_num += 1

    if not quasihalt_status.is_decided:
      # Quasihalt unknown
      if reason in ("Reverse_Engineer", "CTL_A*", "CTL_A*_B"):
        # Temporary work-around to get rid of gold diffs.
        quasihalt_info = ("N/A", "N/A")
      else:
        quasihalt_info = ("Quasihalt_Not_Computed", "N/A")
    elif quasihalt_status.is_quasihalting:
      quasihalt_info = (quasihalt_status.quasihalt_state,
                        Halting_Lib.get_big_int(quasihalt_status.quasihalt_steps))
    else:
      # Not quasihalting
      quasihalt_info = ("No_Quasihalt", "N/A")

    if self.pout:
      io_record = IO.Record()
      io_record.ttable = tm.get_TTable()
      io_record.category = Exit_Condition.INFINITE
      io_record.category_reason = (reason,) + quasihalt_info
      self.io.write_record(io_record)

  def add_unknown(self, tm,
                  unknown_info : io_pb2.UnknownInfo):
    """Note an unresolved TM. Add statistics and output it with reason."""
    self.num_unresolved += 1
    self.tm_num += 1

    unk_reason = unknown_info.WhichOneof("reason")
    if unk_reason == "over_loops_info":
      reason_old = Exit_Condition.MAX_STEPS
      args = (unknown_info.over_loops_info.num_loops,)
    elif unk_reason == "over_tape_info":
      reason_old = Exit_Condition.OVER_TAPE
      args = (unknown_info.over_tape_info.compressed_tape_size,)
    elif unk_reason == "over_time_info":
      reason_old = Exit_Condition.TIME_OUT
      args = (unknown_info.over_time_info.elapsed_time_sec,)
      print("WARNING: TIMEOUT",
            Output_Machine.display_ttable(tm.get_TTable()), file=sys.stderr)
    elif unk_reason == "over_steps_in_macro_info":
      reason_old = Exit_Condition.OVER_STEPS_IN_MACRO
      args = (unknown_info.over_steps_in_macro_info.macro_symbol,
              unknown_info.over_steps_in_macro_info.macro_state,
              unknown_info.over_steps_in_macro_info.macro_dir_is_right)
      print("WARNING: OVER_STEPS_IN_MACRO",
            Output_Machine.display_ttable(tm.get_TTable()), file=sys.stderr)
    else:
      raise Exception(unknown_info)


    if self.pout:
      io_record = IO.Record()
      io_record.ttable = tm.get_TTable()
      io_record.category = Exit_Condition.UNKNOWN
      io_record.category_reason = (Exit_Condition.name(reason_old),) + args
      self.io.write_record(io_record)

def initialize_stack(options, stack):
  if options.infilename:
    # Initialize with all machines from infile.
    infile = open(options.infilename, "r")
    for record in IO.IO(infile, None, None):
      # TODO(shawn): Allow these TMs to be expanded from read size to
      # options size. Ex: if record.ttable is 2x2, but options are 2x3.
      # Currently that will be treated like a normal 2x2 machine here.
      tm = old_tm_mod.Turing_Machine(record.ttable)
      stack.push_job(tm)
    infile.close()
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
  parser.add_option_group(enum_parser)

  Macro_Simulator.add_option_group(parser)

  out_parser = OptionGroup(parser, "Output Options")
  enum_parser.add_option("--no-output", action="store_true", default=False,
                         help="Don't generate any output.")
  out_parser.add_option("--outfile", dest="outfilename", metavar="OUTFILE",
                        help="Output file name "
                        "[Default: Enum.STATES.SYMBOLS.STEPS.out]")
  out_parser.add_option("--infile", dest="infilename",
                        help="If specified, enumeration is started from "
                        "these input machines instead of the single empty "
                        "Turing Machine.")
  out_parser.add_option("--force", action="store_true", default=False,
                        help="Force overwriting outfile (don't ask).")
  out_parser.add_option("--log_number", type=int, metavar="NUM",
                        help="Log number to use in output file")
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
    options.outfilename = "Enum.%d.%d.%s.out" % (options.states, options.symbols, options.max_loops)

  if num_proc > 1:
    field_size = len(str(num_proc - 1))
    field_format = ".%0" + str(field_size) + "d"
    options.outfilename += field_format % MPI_Work_Queue.rank

  if not options.checkpoint:
    options.checkpoint = options.outfilename + ".check"

  pout = None

  if not options.no_output:
    if num_proc == 1:
      pout = sys.stdout
    else:
      pout = open("pout.%03d" % MPI_Work_Queue.rank,"w")

  ## Set up I/O
  if pout:
    if os.path.exists(options.outfilename) and not options.force:
      if num_proc > 1:
        # TODO(shawn): MPI abort here and other failure places.
        parser.error("Output file %r already exists" % options.outfilename)
      reply = input("File '%s' exists, overwrite it? " % options.outfilename)
      if reply.lower() not in ("y", "yes"):
        parser.error("Choose different outfilename")
    outfile = open(options.outfilename, "w")
  else:
    outfile = sys.stdout

  io = IO.IO(None, outfile, options.log_number)

  ## Print command line
  if pout:
    pout.write("Enumerate.py --states=%d --symbols=%d --max-loops=%s --time=%f" \
      % (options.states, options.symbols, options.max_loops, options.time))
    if options.randomize:
      pout.write(" --randomize --seed=%d" % options.seed)

    pout.write(" --outfile=%s" % options.outfilename)
    if options.log_number:
      pout.write(" --log_number=%d" % options.log_number)
    pout.write(" --checkpoint=%s --save-freq=%d" % (options.checkpoint, options.save_freq))
    pout.write("\n")

  # Set up work queue and populate with blank machine.
  if num_proc == 1:
    if options.breadth_first:
      stack = Work_Queue.Basic_FIFO_Work_Queue()
    else:
      stack = Work_Queue.Basic_LIFO_Work_Queue()
    initialize_stack(options, stack)
  else:
    if options.num_enum:
      parser.error("--num-enum cannot be used in parallel runs.")
    if MPI_Work_Queue.rank == 0:
      master = MPI_Work_Queue.Master(pout=pout)
      initialize_stack(options, master)

      if master.run_master():
        end_time = time.time()
        if pout:
          pout.write("\nTotal time %.2f\n" % (end_time - start_time,))
          pout.close()
        else:
          print("\nTotal time %.2f\n" % (end_time - start_time,))
        sys.exit(0)
      else:
        end_time = time.time()
        if pout:
          pout.write("\nTotal time %.2f\n" % (end_time - start_time,))
          pout.close()
        else:
          print("\nTotal time %.2f\n" % (end_time - start_time,))
        sys.exit(1)
    else:
      stack = MPI_Work_Queue.MPI_Worker_Work_Queue(master_proc_num=0, pout=pout)

  ## Enumerate machines
  enumerator = Enumerator(options, stack, io, pout)
  enumerator.continue_enum()

  outfile.close()

if __name__ == "__main__":
  main(sys.argv[1:])
