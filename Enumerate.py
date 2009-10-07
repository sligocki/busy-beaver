#! /usr/bin/env python
#
# Enumerate.py
#
# This is a Busy Beaver Turing machine enumerator.  It enumerates a 
# representative set of all Busy Beavers for given # of states and symbols,
# runs the accelerated simulator, gathers statistics, and outputs the machines
# that take the longest to halt.
#

import copy, sys, time, math
import cPickle as pickle

from Turing_Machine import Turing_Machine
from IO import IO
import Macro_Simulator

def long_to_eng_str(number,left,right):
  if number != 0:
    expo = int(math.log(abs(number))/math.log(10))
    number_str = str(int(number / 10**(expo-right)))

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
  def push(self, item):
    return self.append(item)

class DefaultDict(dict):
  def __init__(self, default):
    self.default = default
  def __getitem__(self, item):
    return self.get(item, self.default)

class Enumerator(object):
  """Holds enumeration state information for checkpointing."""
  def __init__(self, num_states, num_symbols, max_steps, max_time, io, seed,
                     save_freq=100000, checkpoint_filename="checkpoint",
                     save_unk=False, randomize=False):
    import random
    self.num_states = num_states
    self.num_symbols = num_symbols
    self.max_steps = max_steps
    self.max_time = max_time
    self.io = io
    self.save_freq = save_freq
    self.checkpoint_filename = checkpoint_filename
    self.save_unk = save_unk
    
    self.stack = Stack()
    self.tm_num = 0
    
    self.randomize = randomize
    if randomize:
      self.random = random
      self.random.seed(seed)
    
    self.num_halt = self.num_infinite = self.num_unresolved = 0
    self.best_steps = self.best_score = 0
    self.inf_type = DefaultDict(0)
    self.num_over_time = self.num_over_steps = 0
  
  def __getstate__(self):
    d = self.__dict__.copy()
    del d["io"]
    if self.randomize:
      del d["random"]
      d["random_state"] = self.random.getstate()
    return d
  
  def __setstate__(self, d):
    import random
    if d["randomize"]:
      random.setstate(d["random_state"])
      d["random"] = random
      del d["random_state"]
    self.__dict__ = d
  
  def enum(self):
    """Enumerate all num_states*num_symbols TMs in Tree-Normal Form"""
    blank_tm = Turing_Machine(self.num_states, self.num_symbols)
    self.stack.push(blank_tm)
    self.continue_enum()

  def continue_enum(self):
    i = 0
    self.start_time = time.time()
    while len(self.stack) > 0:
      if (i % self.save_freq) == 0:
        self.save()
      i += 1
      # While we have machines to run, pop one off the stack ...
      cur_tm = self.stack.pop()
      # ... and run it
      cond, info = self.run(cur_tm)
      
      # If it hits an undefined transition ...
      if cond == Macro_Simulator.UNDEFINED:
        on_state, on_symbol, steps, score = info
        # ... push all the possible non-halting transitions onto the stack ...
        self.add_transitions(cur_tm, on_state, on_symbol)
        # ... and make this tm the halting one (mutates cur_tm)
        self.add_halt_trans(cur_tm, on_state, on_symbol, steps, score)
      # Otherwise record defined result
      elif cond == Macro_Simulator.HALT:
        steps, score = info
        self.add_halt(cur_tm, steps, score)
      elif cond == Macro_Simulator.INFINITE:
        reason, = info
        self.add_infinite(cur_tm, reason)
      elif cond == Macro_Simulator.OVERSTEPS:
        steps, = info
        self.add_unresolved(cur_tm, Macro_Simulator.OVERSTEPS, steps)
      elif cond == Macro_Simulator.TIMEOUT:
        runtime, steps = info
        self.add_unresolved(cur_tm, Macro_Simulator.TIMEOUT, steps, runtime)
        if (self.save_unk):
          self.io.write_result(self.tm_num, -1, -1, (2, -1, -1), cur_tm)
      else:
        raise Exception, "Enumerator.enum() - unexpected condition (%r)" % cond

    self.save()
  
  def save(self):
    self.end_time = time.time()

    print self.num_halt+self.num_infinite+self.num_unresolved, "-", 
    print self.num_halt, self.num_infinite, self.num_unresolved, "-", 
    print long_to_eng_str(self.best_steps,1,3),
    print long_to_eng_str(self.best_score,1,3),
    print "(%.2f)" % (self.end_time - self.start_time)
    sys.stdout.flush()

    self.start_time = time.time()

    f = file(self.checkpoint_filename, "wb")
    pickle.dump(self, f)
    f.close()
  
  def run(self, tm):
    return Macro_Simulator.run(tm.get_TTable(), self.max_steps, self.max_time)
  
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
    #   1) Add the halt state
    tm.add_cell(on_state, on_symbol, -1, 1, 1)
    #   2) Save this machine
    self.add_halt(tm, steps, score)
  
  def add_halt(self, tm, steps, score):
    self.num_halt += 1
    ## Magic nums: the '-1' is for tape size (not used) .. the '0' is for halting.
    self.io.write_result(self.tm_num, -1, -1, (0, score, steps), tm)
    if steps > self.best_steps or score > self.best_score:
      self.best_steps = max(self.best_steps, steps)
      self.best_score = max(self.best_score, score)
    self.tm_num += 1

  def add_infinite(self, tm, reason):
    self.num_infinite += 1
    self.io.write_result(self.tm_num, -1, -1, (4, "Infinite"), tm)
    self.inf_type[reason] += 1
    self.tm_num += 1

  def add_unresolved(self, tm, reason, steps, runtime=None):
    self.num_unresolved += 1
    self.io.write_result(self.tm_num, -1, -1, (2, "Timeout"), tm)
    if runtime == None:
      self.num_over_steps
    else:
      self.num_over_time
    self.tm_num += 1

# Command line interpretter code
if __name__ == "__main__":
  from optparse import OptionParser, OptionGroup
  # Parse command line options.
  usage = "usage: %prog --states= --symbols= [options]"
  parser = OptionParser(usage=usage)
  req_parser = OptionGroup(parser, "Required Parameters") # Oxymoron?
  req_parser.add_option("--states",  type=int, help="Number of states")
  req_parser.add_option("--symbols", type=int, help="Number of symbols")
  parser.add_option_group(req_parser)
  
  enum_parser = OptionGroup(parser, "Enumeration Options")
  enum_parser.add_option("--steps", type=int, default=10000, help="Max steps to run each machine [Default: %default]")
  enum_parser.add_option("--time", type=float, default=15., help="Max (real) time to run each machine [Default: %default]")
  enum_parser.add_option("--save_unk", action="store_true", default=False)
  enum_parser.add_option("--randomize", action="store_true", default=False, help="Randomize the order of enumeration.")
  enum_parser.add_option("--seed", type=int, help="Seed to randomize with.")
  parser.add_option_group(enum_parser)
  
  out_parser = OptionGroup(parser, "Output Options")
  out_parser.add_option("--outfile", dest="outfilename", metavar="OUTFILE", help="Output file name [Default: Enum.STATES.SYMBOLS.STEPS.out]")
  out_parser.add_option("--log_number", type=int, metavar="NUM", help="Log number to use in output file")
  out_parser.add_option("--checkpoint", metavar="FILE", help="Checkpoint file name [Default: OUTFILE.check]")
  enum_parser.add_option("--save_freq", type=int, default=100000, metavar="FREQ", help="Freq to save checkpoints [Default: %default]")
  parser.add_option_group(out_parser)
  
  (options, args) = parser.parse_args()
  
  # Enforce required parameters
  if not options.states or not options.symbols:
    parser.error("--states= and --symbols= are required parameters")
  
  ## Set defaults
  if not options.seed:
    options.seed = long(1000*time.time())
  if options.steps == 0:
    options.steps = Macro_Simulator.INF
  if not options.outfilename:
    options.outfilename = "Enum.%d.%d.%d.out" % (options.states, options.symbols, options.steps)
  if not options.checkpoint:
    options.checkpoint = options.outfilename + ".check"
  
  # Set up I/O
  outfile = open(options.outfilename, "w")
  io = IO(None, outfile, options.log_number)
  
  # Print command
  print "Enumerate.py --states=%d --symbols=%d --steps=%d --time=%f --save_freq=%d" \
    % (options.states, options.symbols, options.steps, options.time, options.save_freq),
  if options.save_unk:
    print "--save_unk",
  if options.randomize:
    print "--randomize --seed=%d" % options.seed,
  
  print "--outfile=%s --checkpoint=%s" % (options.outfilename, options.checkpoint),
  if options.log_number:
    print "--log_number=%d" % options.log_number,
  print
  
  enumerator = Enumerator(options.states, options.symbols, options.steps,
                          options.time, io, options.seed, options.save_freq,
                          options.checkpoint, options.save_unk, options.randomize)
  enumerator.enum()
