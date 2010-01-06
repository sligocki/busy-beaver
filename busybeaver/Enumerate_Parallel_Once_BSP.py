#! /usr/bin/env python
#
# Enumerate_Parallel_Once.py
#
# This is a Busy Beaver Turing machine enumerator that runs in parallel (using
# ScientificPython and BSP).  It enumerates a representative set of all Busy
# Beavers for given of states and symbols, runs the accelerated simulator,
# and records all results.
#
# This code generates an initial seed population using one processor and a
# breath first search.  When this population is large enough, it distributes
# it evenly to all the processors and then they all run until they are done
# with their work or time runs out - no further load balancing.
#

import copy, sys, time, math, random, os, shutil, operator
# import bz2
import cPickle as pickle

from Scientific.BSP import *

from Turing_Machine import Turing_Machine
from IO import IO
import Macro_Simulator

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

class Stack(list):
  """A simple FILO type. Has push(x) and pop()"""
  def push(self, item):
    return self.append(item)

class DefaultDict(dict):
  """Dictionary that defaults to a value."""
  def __init__(self, default):
    self.default = default
  def __getitem__(self, item):
    return self.get(item, self.default)

class Enumerator(object):
  """Holds enumeration state information for checkpointing."""
  def __init__(self, num_states, num_symbols, max_steps, max_time, io,
                     save_freq=100000, checkpoint_filename="checkpoint",
                     randomize=False, seed=None, options=None):
    # Main TM attributes
    self.num_states = num_states
    self.num_symbols = num_symbols
    self.max_steps = max_steps
    self.max_time = max_time
    # I/O info
    self.io = io
    self.save_freq = save_freq
    self.checkpoint_filename = checkpoint_filename
    self.backup_checkpoint_filename = checkpoint_filename + ".bak"

    self.options = options # Has options for things such as block_finder ...

    # Stack of TM descriptions to simulate
    self.stack = Stack()

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

  def enum(self):
    """Enumerate all num_states, num_symbols TMs in Tree-Normal Form"""
    # blank_tm = Turing_Machine(self.num_states, self.num_symbols)
    # self.stack.push(blank_tm)
    return self.continue_enum()

  def continue_enum(self):
    """
    Pull one machine off of the stack and simulate it, perhaps creating more
    machines to push back onto the stack.
    """
    self.start_time = time.time()
    stime = time.time()
    while time.time() - stime < 10*self.max_time and len(self.stack) > 0:
      # Periodically save state
      if (self.tm_num % self.save_freq) == 0:
        self.save()
      # While we have machines to run, pop one off the stack ...
      tm = self.stack.pop()
      # ... and run it
      cond, info = self.run(tm)

      # If it hits an undefined transition ...
      if cond == Macro_Simulator.UNDEFINED:
        on_state, on_symbol, steps, score = info
        # ... push all the possible non-halting transitions onto the stack ...
        self.add_transitions(tm, on_state, on_symbol)
        # ... and make this TM the halting one (mutates tm)
        self.add_halt_trans(tm, on_state, on_symbol, steps, score)
      # Otherwise record defined result
      elif cond == Macro_Simulator.HALT:
        steps, score = info
        self.add_halt(tm, steps, score)
      elif cond == Macro_Simulator.INFINITE:
        reason, = info
        self.add_infinite(tm, reason)
      elif cond == Macro_Simulator.OVERSTEPS:
        steps, = info
        self.add_unresolved(tm, Macro_Simulator.OVERSTEPS, steps)
      elif cond == Macro_Simulator.TIMEOUT:
        runtime, steps = info
        self.add_unresolved(tm, Macro_Simulator.TIMEOUT, steps, runtime)
      else:
        raise Exception, "Enumerator.enum() - unexpected condition (%r)" % cond

    # Done
    if len(self.stack) == 0:
      self.save()

    return self.stack

  def save(self):
    """Save a checkpoint file so that computation can be restarted if it fails."""
    self.end_time = time.time()

    # Print out statistical data
    # print "Stat Worker: " + str(processorID) + " (" + str(numberOfProcessors) + ") -",
    # print self.tm_num, "-",
    # print self.num_halt, self.num_infinite, self.num_unresolved, "-",
    # print long_to_eng_str(self.best_steps,1,3),
    # print long_to_eng_str(self.best_score,1,3),
    # print "(%.2f)" % (self.end_time - self.start_time)

    # Backup old checkpoint file (in case the new checkpoint is interrupted in mid-write)
    if os.path.exists(self.checkpoint_filename):
      shutil.move(self.checkpoint_filename, self.backup_checkpoint_filename)
    # Save checkpoint file
    f = file(self.checkpoint_filename, "wb")
    pickle.dump(self, f)
    f.close()

    # Restart timer
    self.start_time = time.time()

  def run(self, tm):
    """Simulate TM"""
    return Macro_Simulator.run(tm.get_TTable(), self.options, self.max_steps, self.max_time,
                               self.options.block_size, self.options.backsymbol,
                               self.options.prover, self.options.recursive)

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
      self.stack.extend(new_tms)

  def add_halt_trans(self, tm, on_state, on_symbol, steps, score):
    """Edit the TM to have a halt at on_stat/on_symbol and save the result."""
    #   1) Add the halt state
    tm.add_cell(on_state, on_symbol, -1, 1, 1)
    #   2) Save this machine
    self.add_halt(tm, steps, score)

  def add_halt(self, tm, steps, score):
    """Note a halting TM. Add statistics and output it with score/steps."""
    self.num_halt += 1
    ## Magic nums: the '-1's are for tape size and max_steps (not used) .. the '0' is for halting.
    self.io.write_result(self.tm_num, -1, -1, (0, score, steps), tm)
    if steps > self.best_steps or score > self.best_score:
      self.best_steps = max(self.best_steps, steps)
      self.best_score = max(self.best_score, score)
    self.tm_num += 1

  def add_infinite(self, tm, reason):
    """Note an infinite TM. Add statistics and output it with reason."""
    self.num_infinite += 1
    self.io.write_result(self.tm_num, -1, -1, (4, "Infinite"), tm)
    self.inf_type[reason] += 1
    self.tm_num += 1

  def add_unresolved(self, tm, reason, steps, runtime=None):
    """Note an unresolved TM. Add statistics and output it with reason."""
    self.num_unresolved += 1
    self.io.write_result(self.tm_num, -1, -1, (2, reason), tm)
    if reason == Macro_Simulator.OVERSTEPS:
      self.num_over_steps += 1
    else:
      assert reason == Macro_Simulator.TIMEOUT, "Invalid reason (%r)" % reason
      self.num_over_time += 1
    self.tm_num += 1

class Enumerator_Startup(object):
  """Holds enumeration state information for parallel startup."""
  def __init__(self, num_states, num_symbols, max_steps, max_time, io,
                     save_freq=100000, checkpoint_filename="checkpoint",
                     randomize=False, seed=None, options=None):
    # Main TM attributes
    self.num_states = num_states
    self.num_symbols = num_symbols
    self.max_steps = max_steps
    self.max_time = max_time
    # I/O info
    self.io = io
    self.save_freq = save_freq
    self.checkpoint_filename = checkpoint_filename
    self.backup_checkpoint_filename = checkpoint_filename + ".bak"

    self.options = options # Has options for things such as block_finder ...

    # Stack of TM descriptions to simulate
    self.stack = Stack()

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

  def enum(self):
    """Enumerate all num_states, num_symbols TMs in Tree-Normal Form"""
    blank_tm = Turing_Machine(self.num_states, self.num_symbols)
    self.stack.push(blank_tm)
    return self.continue_enum()

  def continue_enum(self):
    """
    Pull one machine off of the stack and simulate it, perhaps creating more
    machines to push back onto the stack.
    """
    self.start_time = time.time()
    while len(self.stack) > 0:
      # Periodically save state
      if (self.tm_num % self.save_freq) == 0:
        self.save()
      if len(self.stack) >= numberOfProcessors*10:
        return self.stack
      # While we have machines to run, pop one off the stack (breadth first)...
      tm = self.stack.pop(0)
      # ... and run it
      cond, info = self.run(tm)

      # If it hits an undefined transition ...
      if cond == Macro_Simulator.UNDEFINED:
        on_state, on_symbol, steps, score = info
        # ... push all the possible non-halting transitions onto the stack ...
        self.add_transitions(tm, on_state, on_symbol)
        # ... and make this TM the halting one (mutates tm)
        self.add_halt_trans(tm, on_state, on_symbol, steps, score)
      # Otherwise record defined result
      elif cond == Macro_Simulator.HALT:
        steps, score = info
        self.add_halt(tm, steps, score)
      elif cond == Macro_Simulator.INFINITE:
        reason, = info
        self.add_infinite(tm, reason)
      elif cond == Macro_Simulator.OVERSTEPS:
        steps, = info
        self.add_unresolved(tm, Macro_Simulator.OVERSTEPS, steps)
      elif cond == Macro_Simulator.TIMEOUT:
        runtime, steps = info
        self.add_unresolved(tm, Macro_Simulator.TIMEOUT, steps, runtime)
      else:
        raise Exception, "Enumerator.enum() - unexpected condition (%r)" % cond

    # Done
    return []

  def save(self):
    """Save a checkpoint file so that computation can be restarted if it fails."""
    self.end_time = time.time()

    # Print out statistical data
    # print self.tm_num, "-",
    # print self.num_halt, self.num_infinite, self.num_unresolved, "-",
    # print long_to_eng_str(self.best_steps,1,3),
    # print long_to_eng_str(self.best_score,1,3),
    # print "(%.2f)" % (self.end_time - self.start_time)

    # Backup old checkpoint file (in case the new checkpoint is interrupted in mid-write)
    # if os.path.exists(self.checkpoint_filename):
    #   shutil.move(self.checkpoint_filename, self.backup_checkpoint_filename)
    # Save checkpoint file
    # f = file(self.checkpoint_filename, "wb")
    # pickle.dump(self, f)
    # f.close()

    # Restart timer
    self.start_time = time.time()

  def run(self, tm):
    """Simulate TM"""
    return Macro_Simulator.run(tm.get_TTable(), self.options, self.max_steps, self.max_time,
                               self.options.block_size, self.options.backsymbol,
                               self.options.prover, self.options.recursive)

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
      self.stack.extend(new_tms)

  def add_halt_trans(self, tm, on_state, on_symbol, steps, score):
    """Edit the TM to have a halt at on_stat/on_symbol and save the result."""
    #   1) Add the halt state
    tm.add_cell(on_state, on_symbol, -1, 1, 1)
    #   2) Save this machine
    self.add_halt(tm, steps, score)

  def add_halt(self, tm, steps, score):
    """Note a halting TM. Add statistics and output it with score/steps."""
    self.num_halt += 1
    ## Magic nums: the '-1's are for tape size and max_steps (not used) .. the '0' is for halting.
    if processorID == 0:
      self.io.write_result(self.tm_num, -1, -1, (0, score, steps), tm)
    if steps > self.best_steps or score > self.best_score:
      self.best_steps = max(self.best_steps, steps)
      self.best_score = max(self.best_score, score)
    self.tm_num += 1

  def add_infinite(self, tm, reason):
    """Note an infinite TM. Add statistics and output it with reason."""
    self.num_infinite += 1
    if processorID == 0:
      self.io.write_result(self.tm_num, -1, -1, (4, "Infinite"), tm)
    self.inf_type[reason] += 1
    self.tm_num += 1

  def add_unresolved(self, tm, reason, steps, runtime=None):
    """Note an unresolved TM. Add statistics and output it with reason."""
    self.num_unresolved += 1
    if processorID == 0:
      self.io.write_result(self.tm_num, -1, -1, (2, reason), tm)
    if reason == Macro_Simulator.OVERSTEPS:
      self.num_over_steps += 1
    else:
      assert reason == Macro_Simulator.TIMEOUT, "Invalid reason (%r)" % reason
      self.num_over_time += 1
    self.tm_num += 1

def enumerate(init_stack,io,checkpoint,options):
  enumerator = Enumerator(options.states, options.symbols,
                          options.steps, options.time, io,
                          options.save_freq, checkpoint,
                          options.randomize, options.seed, options)
  enumerator.stack = init_stack[:]

  cur_stack = enumerator.enum()

  return cur_stack

def get_and_print_stats(string,mylist):
  min_list = mylist.reduce(min,1000000)
  max_list = mylist.reduce(max,0)
  sum_list = mylist.reduce(operator.add,0)

  global_print_stats(string,min_list,max_list,sum_list)

def print_stats(string,min_list,max_list,sum_list):
  print string + "(%.2f %.2f %.2f)..." % (min_list,max_list,sum_list/numberOfProcessors)

def print_blank():
  print

# Command line interpretter code
if __name__ == "__main__":
  stime = time.time()

  global_enumerate = ParFunction(enumerate)
  global_print_stats = ParRootFunction(print_stats)
  global_print_blank = ParRootFunction(print_blank)

  from optparse import OptionParser, OptionGroup

  ## Parse command line options.
  usage = "usage: %prog --states= --symbols= [options]"
  parser = OptionParser(usage=usage)
  req_parser = OptionGroup(parser, "Required Parameters") # Oxymoron?
  req_parser.add_option("--states",  type=int, help="Number of states")
  req_parser.add_option("--symbols", type=int, help="Number of symbols")
  parser.add_option_group(req_parser)

  enum_parser = OptionGroup(parser, "Enumeration Options")
  enum_parser.add_option("--steps", type=int, default=10000, help="Max simulation steps to run each machine (0 for infinite) [Default: %default]")
  enum_parser.add_option("--time", type=float, default=15., help="Max (real) time (in seconds) to run each machine [Default: %default]")
  enum_parser.add_option("--randomize", action="store_true", default=False, help="Randomize the order of enumeration.")
  enum_parser.add_option("--seed", type=int, help="Seed to randomize with.")

  enum_parser.add_option("-b", "--no-backsymbol", action="store_false", dest="backsymbol", default=True,
                    help="Turn off backsymbol macro machine")
  enum_parser.add_option("-p", "--no-prover", action="store_false", dest="prover", default=True,
                    help="Turn off proof system")
  enum_parser.add_option("-r", "--recursive", action="store_true", default=False,
                    help="Turn ON recursive proof system [Very Experimental]")

  parser.add_option_group(enum_parser)

  block_options = OptionGroup(parser, "Block Finder options")
  block_options.add_option("--block-size", type=int, help="Block size to use in macro machine simulator (default is to guess with the block_finder algorithm)")
  block_options.add_option("--bf-limit1", type=int, default=200, metavar="LIMIT", help="Number of steps to run the first half of block finder [Default: %default].")
  block_options.add_option("--bf-limit2", type=int, default=200, metavar="LIMIT", help="Number of stpes to run the second half of block finder [Default: %default].")
  block_options.add_option("--bf-run1", action="store_true", default=True, help="In first half, find worst tape before limit.")
  block_options.add_option("--bf-no-run1", action="store_false", dest="bf_run1", help="In first half, just run to limit.")
  block_options.add_option("--bf-run2", action="store_true", default=True, help="Run second half of block finder.")
  block_options.add_option("--bf-no-run2", action="store_false", dest="bf_run2", help="Don't run second half of block finder.")
  block_options.add_option("--bf-extra-mult", type=int, default=2, metavar="MULT", help="How far ahead to search in second half of block finder.")
  parser.add_option_group(block_options)

  out_parser = OptionGroup(parser, "Output Options")
  out_parser.add_option("--outfile", dest="outfilename", metavar="OUTFILE", help="Output file name [Default: Enum.STATES.SYMBOLS.STEPS.out]")
  out_parser.add_option("--log_number", type=int, metavar="NUM", help="Log number to use in output file")
  out_parser.add_option("--checkpoint", metavar="FILE", help="Checkpoint file name [Default: OUTFILE.check]")
  out_parser.add_option("--save_freq", type=int, default=100000, metavar="FREQ", help="Freq to save checkpoints [Default: %default]")
  parser.add_option_group(out_parser)

  (options, args) = parser.parse_args()

  ## Enforce required parameters
  if not options.states or not options.symbols:
    parser.error("--states= and --symbols= are required parameters")

  ## Set complex defaults
  if not options.seed:
    options.seed = long(1000*time.time())

  if options.steps == 0:
    options.steps = Macro_Simulator.INF

  if not options.outfilename:
    if options.steps == Macro_Simulator.INF:
      options.outfilename = "Enum.%d.%d.%d.out" % (options.states, options.symbols, 0)
    else:
      options.outfilename = "Enum.%d.%d.%d.out" % (options.states, options.symbols, options.steps)

  if not options.checkpoint:
    options.checkpoint = options.outfilename + ".check"

  if processorID == 0:
    ## Print command line
    print "Enumerate.py --states=%d --symbols=%d --steps=%d --time=%f" \
      % (options.states, options.symbols, options.steps, options.time),
    if options.randomize:
      print "--randomize",
    print "--seed=%d" % options.seed,
    print "--outfile=%s" % options.outfilename,
    if options.log_number:
      print "--log_number=%d" % options.log_number,
    print "--checkpoint=%s --save_freq=%d" % (options.checkpoint, options.save_freq),
    print

  states      = options.states
  symbols     = options.symbols
  timeout     = options.time
  outfilename = options.outfilename
  log_number  = options.log_number
  seed        = options.seed
  save_freq   = options.save_freq
  checkpoint  = options.checkpoint
  steps       = options.steps
  #save_unk    = options.save_unk

  if outfilename == "-":
    outfile = sys.stdout
  else:
    outfilename = outfilename + ".%05d" % processorID + ".%05d" % numberOfProcessors
    if os.path.exists(outfilename):
      sys.stderr.write("Output test file, '%s', exists\n" % outfilename)
      exit(1)
    # outfile = bz2.BZ2File(outfilename, "w")
    outfile = file(outfilename, "w")

  checkpoint = checkpoint + ".%05d" % processorID + ".%05d" % numberOfProcessors

  # io = IO(None, outfile, log_number, True)
  io = IO(None, outfile, log_number, False)

  if processorID == 0:
    # Enumerate some machines
    enumerator = Enumerator_Startup(options.states, options.symbols,
                                    options.steps, options.time, io,
                                    options.save_freq, checkpoint,
                                    options.randomize, options.seed, options)

    full_stack = enumerator.enum()
    #full_stack = [item for i in xrange(numberOfProcessors) for item in full_stack[i::numberOfProcessors]]
    random.seed(seed)
    random.shuffle(full_stack)
  else:
    full_stack = []

  full_stack_len = ParData(lambda pid, nProcs: len(full_stack));
  get_and_print_stats("Full     Stack Size: ",full_stack_len)

  init_stack = ParData(lambda pID, nProcs: full_stack)
  init_stack = ParRootSequence(init_stack)

  init_stack_len = ParData(lambda pid, nProcs: len(init_stack));
  get_and_print_stats("Init     Stack Size: ",init_stack_len)

  global_print_blank()

  time_enum = 0.0
  time_gath = 0.0
  time_scat = 0.0

  iter = 0

  while 1:
    iter += 1

    t1 = time.time()

    cur_stack = global_enumerate(init_stack,io,checkpoint,options)

    t2 = time.time()
    time_enum += t2 - t1

    all_cur_stack = cur_stack.reduce(operator.add, [])

    t3 = time.time()
    time_gath += t3 - t2

    init_stack = ParRootSequence(all_cur_stack)

    init_stack_len = ParData(lambda pid, nProcs: len(init_stack));
    get_and_print_stats("Loop %3d Stack Size: " % (iter,),init_stack_len)

    t4 = time.time()
    time_scat += t4 - t3

    if not init_stack.totalLength().anytrue():
      break

  outfile.close()

  global_print_blank()

  enum_time = ParData(lambda pid, nProcs: time_enum);
  get_and_print_stats("Enum    Time: ",enum_time)

  gath_time = ParData(lambda pid, nProcs: time_gath);
  get_and_print_stats("Gather  Time: ",gath_time)

  scat_time = ParData(lambda pid, nProcs: time_scat);
  get_and_print_stats("Scatter Time: ",scat_time)

  etime = time.time()

  total_time = ParData(lambda pid, nProcs: etime - stime)
  get_and_print_stats("Total   Time: ",total_time)
