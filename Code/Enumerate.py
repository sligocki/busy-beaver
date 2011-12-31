#! /usr/bin/env python
#
# Enumerate.py
#
"""
This is a Busy Beaver Turing machine enumerator.

It enumerates all Busy Beavers for given # of states and symbols, runs the
Macro Machine simulator, gathers statistics, and outputs all of the machines
like Generate does.
"""

import copy
import cPickle as pickle
import math
from optparse import OptionParser, OptionGroup
import os
from pprint import pprint
import random
import shutil
import sys
import time

from Alarm import AlarmException
from Common import Exit_Condition, GenContainer
import IO
from Macro import Block_Finder
import Macro_Simulator
from Turing_Machine import Turing_Machine
import Work_Queue

try:
  import MPI_Work_Queue
  num_proc = MPI_Work_Queue.num_proc
except ImportError:
  # Allow this to work even if mpy4py is not installed.
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

class DefaultDict(dict):
  """Dictionary that defaults to a value."""
  def __init__(self, default):
    self.default = default
  def __getitem__(self, item):
    return self.get(item, self.default)

class Enumerator(object):
  """Holds enumeration state information for checkpointing."""
  def __init__(self, max_steps, max_time, stack, io,
                     save_freq=100000, checkpoint_filename="checkpoint",
                     randomize=False, seed=None, options=None):
    # Main TM attributes
    self.max_steps = max_steps
    self.max_time = max_time
    # I/O info
    self.io = io
    self.save_freq = save_freq
    self.checkpoint_filename = checkpoint_filename
    self.backup_checkpoint_filename = checkpoint_filename + ".bak"

    self.options = options # Has options for things such as block_finder ...

    # Stack of TM descriptions to simulate
    assert isinstance(stack, Work_Queue.Work_Queue)
    self.stack = stack

    # If we are randomizing the stack order
    self.randomize = randomize
    if randomize:
      self.random = random.Random()
      self.random.seed(seed)

    # Statistics
    self.tm_num = 0
    self.num_halt = self.num_infinite = self.num_unresolved = 0
    self.best_steps = self.best_score = 0
    self.inf_type = DefaultDict(0)
    self.num_over_time = self.num_over_steps = 0
    # Passed into and updated in Macro_Simulator
    self.stats = GenContainer()
    self.stats.num_rules = 0
    self.stats.num_recursive_rules = 0
    self.stats.num_collatz_rules = 0
    self.stats.num_failed_proofs = 0

  def __getstate__(self):
    """Gets state of TM for checkpoint file."""
    d = self.__dict__.copy()
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
    self.start_clock = time.clock()
    while True:
      if self.options.num_enum and self.tm_num >= self.options.num_enum:
        break
      # While we have machines to run, pop one off the stack ...
      tm = self.stack.pop_job()
      if not tm:
        # tm == None is the indication that we have no more machines to run.
        break
      # Periodically save state
      if (self.tm_num % self.save_freq) == 0:
        self.save()
      for do_over in xrange(0,4):
        try:
          # ... and run it.
          cond, info = self.run(tm)

          # If it hits an undefined transition ...
          if cond == Exit_Condition.UNDEF_CELL:
            on_state, on_symbol, steps, score = info
            # ... push all the possible non-halting transitions onto the stack ...
            self.add_transitions(tm, on_state, on_symbol)
            # ... and make this TM the halting one (mutates tm)
            self.add_halt_trans(tm, on_state, on_symbol, steps, score)
          # Otherwise record defined result
          elif cond == Exit_Condition.HALT:
            steps, score = info
            self.add_halt(tm, steps, score)
          elif cond == Exit_Condition.INFINITE:
            reason, = info
            self.add_infinite(tm, reason)
          elif cond == Exit_Condition.MAX_STEPS:
            steps, = info
            self.add_unresolved(tm, Exit_Condition.MAX_STEPS, steps)
          elif cond == Exit_Condition.TIME_OUT:
            runtime, steps = info
            self.add_unresolved(tm, Exit_Condition.TIME_OUT, steps, runtime)
          else:
            raise Exception, "Enumerator.enum() - unexpected condition (%r)" % cond
          break

        except AlarmException:
          sys.stderr.write("Weird2 (%d): %s\n" % (do_over,tm))

    # Save any remaining machines on the stack.
    tm = self.stack.pop_job()
    while tm:
      self.add_unresolved(tm, Exit_Condition.NOT_RUN)
      tm = self.stack.pop_job()
      
    # Done
    self.save()

  def save(self):
    """Save a checkpoint file so that computation can be restarted if it fails."""
    self.end_time = time.time()
    self.end_clock = time.clock()

    # Print out statistical data
    print self.tm_num, "-",
    print self.num_halt, self.num_infinite, self.num_unresolved, "-",
    print long_to_eng_str(self.best_steps,1,3),
    print long_to_eng_str(self.best_score,1,3),
    print "(%.2f - %.2f)" % (self.end_time - self.start_time,
                             self.end_clock - self.start_clock)
    if self.options.print_stats:
      pprint(self.stats.__dict__)
    sys.stdout.flush()

    # Backup old checkpoint file (in case the new checkpoint is interrupted in mid-write)
    if os.path.exists(self.checkpoint_filename):
      shutil.move(self.checkpoint_filename, self.backup_checkpoint_filename)
    # Save checkpoint file
    f = file(self.checkpoint_filename, "wb")
    pickle.dump(self, f)
    f.close()

    # Restart timer
    self.start_time = time.time()
    self.start_clock = time.clock()

  def run(self, tm):
    """Simulate TM"""
    return Macro_Simulator.run(tm.get_TTable(), self.options, self.max_steps, self.max_time,
                               self.options.block_size, self.options.backsymbol,
                               self.options.prover, self.options.recursive,
                               self.stats)

  def add_transitions(self, old_tm, state_in, symbol_in):
    """Push Turing Machines with each possible transition at this state and symbol"""
    # 'max_state' and 'max_symbol' are the state and symbol numbers for the
    # smallest state/symbol not yet written (i.e. available to add to TTable).
    max_state  = old_tm.get_num_states_available()
    max_symbol = old_tm.get_num_symbols_available()
    # If this is the last undefined cell, then it must be a halt, so only try
    # other values for cell if this is not the last undefined cell.
    if old_tm.num_empty_cells > 1:
      # 'state_out' in [0, 1, ... max_state] == xrange(max_state + 1)
      new_tms = []
      for state_out in xrange(max_state + 1):
        for symbol_out in xrange(max_symbol + 1):
          for direction_out in xrange(2):
            new_tm = copy.deepcopy(old_tm)
            new_tm.add_cell(state_in , symbol_in ,
                            state_out, symbol_out, direction_out)
            new_tms.append(new_tm)

      # If we are randomizing TM order, do so
      if self.randomize:
        self.random.shuffle(new_tms)

      # Push the list of TMs onto the stack
      self.stack.push_jobs(new_tms)

  def add_halt_trans(self, tm, on_state, on_symbol, steps, score):
    """Edit the TM to have a halt at on_stat/on_symbol and save the result."""
    #   1) Add the halt state
    tm.add_cell(on_state, on_symbol, -1, 1, 1)
    #   2) Save this machine
    self.add_halt(tm, steps, score)

  def add_halt(self, tm, steps, score):
    """Note a halting TM. Add statistics and output it with score/steps."""
    self.num_halt += 1
    if steps > self.best_steps or score > self.best_score:
      self.best_steps = max(self.best_steps, steps)
      self.best_score = max(self.best_score, score)
    self.tm_num += 1

    io_record = IO.Record()
    io_record.ttable = tm.get_TTable()
    io_record.category = Exit_Condition.HALT
    io_record.category_reason = (score, steps)
    self.io.write_record(io_record)

  def add_infinite(self, tm, reason):
    """Note an infinite TM. Add statistics and output it with reason."""
    self.num_infinite += 1
    self.inf_type[reason] += 1
    self.tm_num += 1

    io_record = IO.Record()
    io_record.ttable = tm.get_TTable()
    io_record.category = Exit_Condition.INFINITE
    io_record.category_reason = (reason,)
    self.io.write_record(io_record)

  def add_unresolved(self, tm, reason, steps=0, runtime=0):
    """Note an unresolved TM. Add statistics and output it with reason."""
    self.num_unresolved += 1
    if reason == Exit_Condition.MAX_STEPS:
      self.num_over_steps += 1
    elif reason == Exit_Condition.TIME_OUT:
      self.num_over_time += 1
    else:
      assert reason == Exit_Condition.NOT_RUN, "Invalid reason (%r)" % reason
    self.tm_num += 1

    io_record = IO.Record()
    io_record.ttable = tm.get_TTable()
    io_record.category = Exit_Condition.UNKNOWN
    io_record.category_reason = (Exit_Condition.name(reason), steps, runtime)
    self.io.write_record(io_record)

def initialize_stack(io, options, stack):
  if io.input_file:
    # Initialize with all machines from infile.
    for record in io:
      # TODO(shawn): Allow these TMs to be expanded from read size to
      # options size. Ex: if record.ttable is 2x2, but options are 2x3.
      # Currently that will be treated like a normal 2x2 machine here.
      tm = Turing_Machine(record.ttable)
      stack.push_job(tm)
  else:
    # If no infile is specified, then default to the NxM blank TM.
    blank_tm = Turing_Machine(options.states, options.symbols)
    stack.push_job(blank_tm)

def main(args):
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
  parser.add_option_group(enum_parser)

  Macro_Simulator.add_option_group(parser)

  out_parser = OptionGroup(parser, "Output Options")
  out_parser.add_option("--outfile", dest="outfilename", metavar="OUTFILE",
                        help="Output file name "
                        "[Default: Enum.STATES.SYMBOLS.STEPS.out]")
  out_parser.add_option("--infile", dest="infilename",
                        help="If specified, enumeration is started from "
                        "these input machines instead of the single empty "
                        "Turing Machine.")
  out_parser.add_option("--log_number", type=int, metavar="NUM",
                        help="Log number to use in output file")
  out_parser.add_option("--checkpoint", metavar="FILE",
                        help="Checkpoint file name [Default: OUTFILE.check]")
  out_parser.add_option("--save_freq", type=int, default=100000, metavar="FREQ",
                        help="Freq to save checkpoints [Default: %default]")
  out_parser.add_option("--print-stats", action="store_true", default=False,
                        help="Print aggregate statistics every time we "
                        "checkpoint.")
  parser.add_option_group(out_parser)

  (options, args) = parser.parse_args(args)

  ## Enforce required parameters
  if not options.states or not options.symbols:
    parser.error("--states= and --symbols= are required parameters")

  ## Set complex defaults
  if options.randomize and not options.seed:
    options.seed = long(1000*time.time())

  if not options.outfilename:
    options.outfilename = "Enum.%d.%d.%s.out" % (options.states, options.symbols, options.steps)

  if num_proc > 1:
    field_size = len(str(num_proc - 1))
    field_format = ".%0" + str(field_size) + "d"
    options.outfilename += field_format % MPI_Work_Queue.rank

  if not options.checkpoint:
    options.checkpoint = options.outfilename + ".check"

  ## Set up I/O
  infile = None
  if options.infilename:
    infile = open(options.infilename, "r")

  if os.path.exists(options.outfilename):
    if num_proc > 1:
      # TODO(shawn): MPI abort here and other failure places.
      parser.error("Output file %r already exists" % options.outfilename)
    reply = raw_input("File '%s' exists, overwrite it? " % options.outfilename)
    if reply.lower() not in ("y", "yes"):
      parser.error("Choose different outfilename")
  outfile = open(options.outfilename, "w")

  io = IO.IO(infile, outfile, options.log_number)

  ## Print command line
  print "Enumerate.py --states=%d --symbols=%d --steps=%s --time=%f" \
    % (options.states, options.symbols, options.steps, options.time),
  if options.randomize:
    print "--randomize --seed=%d" % options.seed,

  print "--outfile=%s" % options.outfilename,
  if options.log_number:
    print "--log_number=%d" % options.log_number,
  print "--checkpoint=%s --save_freq=%d" % (options.checkpoint, options.save_freq),
  print

  if options.steps == 0:
    options.steps = Macro_Simulator.INF

  # Set up work queue and populate with blank machine.
  if num_proc == 1:
    if options.breadth_first:
      stack = Work_Queue.Basic_FIFO_Work_Queue()
    else:
      stack = Work_Queue.Basic_LIFO_Work_Queue()
    initialize_stack(io, options, stack)
  else:
    if MPI_Work_Queue.rank == 0:
      master = MPI_Work_Queue.Master()
      initialize_stack(io, options, stack)
      if master.run_master():
        sys.exit(0)
      else:
        sys.exit(1)
    else:
      stack = MPI_Work_Queue.MPI_Worker_Work_Queue(master_proc_num=0)

  ## Enumerate machines
  enumerator = Enumerator(options.steps, options.time, stack, io,
                          options.save_freq, options.checkpoint,
                          options.randomize, options.seed, options)
  enumerator.continue_enum()

  if options.print_stats:
    pprint(enumerator.stats.__dict__)

if __name__ == "__main__":
  main(sys.argv[1:])
