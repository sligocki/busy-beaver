#! /usr/bin/env python
#
# Enumerate_Parallel.py
#
# This is a Busy Beaver Turing machine enumerator that runs in parallel (using
# pyMPI).  It enumerates a representative set of all Busy Beavers for given
# of states and symbols, runs the accelerated simulator, and records all
# results.
#

import copy, sys, time, math, random, os
import cPickle as pickle
import mpi

from Turing_Machine import Turing_Machine
from IO import IO
import Macro_Simulator

BB_NEXT = 0
BB_STOP = 1

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
  def pop(self):
    return self.recvItem()

  def push(self, item):
    return self.sendList([item])

  def extend(self, items):
    return self.sendList(items)

  def recvItem(self):
    if self.one != None:
      temp = self.one
      self.one = None
      return temp
    else:
      stime = time.time()
      msg,status = mpi.recv(0)
      etime = time.time()
      self.ttime += etime - stime
      # print "  worker %d received: %s (%d)" % (mpi.rank,msg,status.tag)
      # sys.stdout.flush()
      if status.tag == BB_STOP:
        return 0

    return msg
    
  def sendList(self, items):
    # print "  worker %d sent: %d" % (mpi.rank,len(items))
    # sys.stdout.flush()
    msg = [0,items]
    if len(items) > 0 and self.one == None:
      self.one = items.pop()
      msg = [1,items]
    else:
      msg = [0,items]

    stime = time.time()
    mpi.send(msg,0)
    etime = time.time()

    self.ttime += etime - stime
    

class DefaultDict(dict):
  def __init__(self, default):
    self.default = default
  def __getitem__(self, item):
    return self.get(item, self.default)

class Enumerator(object):
  """Holds enumeration state information for checkpointing."""
  def __init__(self, num_states, num_symbols, max_steps, max_time, io, seed,
                     save_freq=100000, checkpoint_filename="checkpoint",
                     save_unk=False):
    self.num_states = num_states
    self.num_symbols = num_symbols
    self.max_steps = max_steps
    self.max_time = max_time
    self.io = io
    self.save_freq = save_freq
    self.checkpoint_filename = checkpoint_filename
    self.save_unk = save_unk
    
    self.random = random
    self.random.seed(seed)
    self.stack = Stack()
    self.stack.ttime = 0.0
    self.stack.one = None
    self.tm_num = 0
    
    self.num_halt = self.num_infinite = self.num_unresolved = 0
    self.best_steps = self.best_score = 0
    self.inf_type = DefaultDict(0)
    self.num_over_time = self.num_over_steps = 0
  
  def __getstate__(self):
    d = self.__dict__.copy()
    del d["io"], d["random"]
    d["random_state"] = self.random.getstate()
    return d
  
  def __setstate__(self, d):
    random.setstate(d["random_state"])
    del d["random_state"]
    self.__dict__ = d
    self.random = random
  
  def enum(self):
    """Enumerate all num_states*num_symbols TMs in Tree-Normal Form"""
    # blank_tm = Turing_Machine(self.num_states, self.num_symbols)
    # self.stack.push(blank_tm)
    self.continue_enum()

  def continue_enum(self):
    stime = time.time()
    i = 0
    self.start_time = time.time()
    while 1:
      # print "  worker %d - save..." % mpi.rank
      # sys.stdout.flush()
      if (i % self.save_freq) == 0:
        self.save()
      i += 1
      # While we have machines to run, pop one off the stack ...
      # print "  worker %d - pop..." % mpi.rank
      # sys.stdout.flush()
      cur_tm = self.stack.pop()
      if cur_tm == 0:
        etime = time.time()
        print "  stopped %d - %f (%f)..." % (mpi.rank,etime-stime,self.stack.ttime)
        sys.exit(0)
      # ... and run it
      cond, info = self.run(cur_tm)
      
      # If it hits an undefined transition ...
      if cond == Macro_Simulator.UNDEFINED:
        # print "  worker %d - undefined..." % mpi.rank
        # sys.stdout.flush()
        on_state, on_symbol, steps, score = info
        # ... push all the possible non-halting transitions onto the stack ...
        self.add_transitions(cur_tm, on_state, on_symbol)
        # ... and make this tm the halting one (mutates cur_tm)
        self.add_halt_trans(cur_tm, on_state, on_symbol, steps, score)
      # Otherwise record defined result
      elif cond == Macro_Simulator.HALT:
        # print "  worker %d - halt..." % mpi.rank
        # sys.stdout.flush()
        steps, score = info
        self.add_halt(cur_tm, steps, score)
        self.stack.extend([])
      elif cond == Macro_Simulator.INFINITE:
        # print "  worker %d - infinite..." % mpi.rank
        # sys.stdout.flush()
        reason, = info
        self.add_infinite(cur_tm, reason)
        self.stack.extend([])
      elif cond == Macro_Simulator.OVERSTEPS:
        # print "  worker %d - oversteps..." % mpi.rank
        # sys.stdout.flush()
        steps, = info
        self.add_unresolved(cur_tm, cond, steps)
        self.stack.extend([])
      elif cond == Macro_Simulator.TIMEOUT:
        # print "  worker %d - timeout..." % mpi.rank
        # sys.stdout.flush()
        runtime, steps = info
        self.add_unresolved(cur_tm, cond, steps, runtime)
        self.stack.extend([])
      else:
        raise Exception, "Enumerator.enum() - unexpected condition (%r)" % cond
  
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

      self.random.shuffle(new_tms)

      # Push the (randomize) list of TMs onto the stack
      self.stack.extend(new_tms)
    else:
      self.stack.extend([])

  def add_halt_trans(self, tm, on_state, on_symbol, steps, score):
    #   1) Add the halt state
    tm.add_cell(on_state, on_symbol, -1, 1, 1)
    #   2) This machine  *may* write one more symbol
    if on_symbol == 0:
      score += 1
    #   3) Save this machine
    self.add_halt(tm, steps, score)
  
  def add_halt(self, tm, steps, score):
    self.num_halt += 1
    self.io.write_result(self.tm_num, -1, -1, (0, score, steps), tm)
    if steps > self.best_steps or score > self.best_score:
      ## Magic nums: the '-1' is for tape size (not used) .. the '0' is for halting.
      self.best_steps = max(self.best_steps, steps)
      self.best_score = max(self.best_score, score)
    self.tm_num += 1
  def add_infinite(self, tm, reason):
    self.io.write_result(self.tm_num, -1, -1, (4, "Infinite"), tm)
    self.num_infinite += 1
    self.inf_type[reason] += 1
    self.tm_num += 1
  def add_unresolved(self, tm, cond, steps, runtime=None):
    self.io.write_result(self.tm_num, -1, -1, (2, "Timeout"), tm)
    self.num_unresolved += 1
    if runtime == None:
      self.num_over_steps
    else:
      self.num_over_time
    self.tm_num += 1

# Command line interpretter code
if __name__ == "__main__":
  if mpi.rank == 0:
    from Option_Parser_Parallel import Generator_Option_Parser
    
    # Get command line options.
    # Enumerate_Parallel.py may be sent an infile param but it should be ignored
    opts, args = Generator_Option_Parser(sys.argv, 
            [("time",      float,                     15, False, True), 
             ("save_freq",   int,                 100000, False, True),
             ("seed",       long, long(1000*time.time()), False, True),
             ("checkpoint",  str,                   None, False, True),
             ("save_unk"  , None,                  False, False, False)],
            ignore_infile=True)

    steps = (opts["steps"] if opts["steps"] > 0 else Macro_Simulator.INF)
    io = IO(None, opts["outfile"], opts["log_number"])

    save_unk_str = ""
    if opts["save_unk"]:
      save_unk_str = " --save_unk"

    if opts["checkpoint"] == None:
      opts["checkpoint"] = opts["outfilename"] + ".check"

    print "Enumerate_Parallel.py --steps=%s --time=%s --save_freq=%s --seed=%s --outfile=%s --checkpoint=%s%s --states=%s --symbols=%s" % \
          (opts["steps"],opts["time"],opts["save_freq"],opts["seed"],opts["outfilename"],opts["checkpoint"],save_unk_str,opts["states"],opts["symbols"])
    sys.stdout.flush()

    if opts["log_number"] != None:
      print "--log_number=%s" % (opts["log_number"])
    else:
      print ""
  
    nprocs = mpi.procs

    mpi.bcast((opts["states"],opts["symbols"],steps,opts["time"],opts["outfilename"],opts["log_number"],opts["seed"],opts["save_freq"],opts["checkpoint"],opts["save_unk"]))

    print "Manager: " + str(nprocs) + " processes..."
    sys.stdout.flush()

    master_stack = []
    master_list = range(2,nprocs)

    blank_tm = Turing_Machine(opts["states"],opts["symbols"])
    mpi.send(blank_tm,1,tag=BB_NEXT)

    while len(master_stack) > 0 or len(master_list) < nprocs-1:
      while len(master_stack) > 0 and len(master_list) > 0:
        next_tm   = master_stack.pop()
        next_proc = master_list .pop(0)

        # print "  manager sent: %s (%d)" % (next_tm,next_proc)
        # sys.stdout.flush()
        mpi.send(next_tm,next_proc,tag=BB_NEXT)

      msg,status = mpi.recv()
      # print "  manager received: %d (%d)" % (len(items),status.source)
      # sys.stdout.flush()

      master_stack.extend(msg[1])

      if msg[0] == 0:
        master_list.append(status.source)

    for proc in xrange(1,mpi.procs):
      print "  stopping %d..." % proc
      sys.stdout.flush()
      mpi.send((),proc,BB_STOP)
  else:
    params = mpi.bcast()

    print "Worker: " + str(mpi.rank) + " (" + str(len(params)) + ")..."
    sys.stdout.flush()

    states      = params[0]
    symbols     = params[1]
    steps       = params[2]
    timeout     = params[3]
    outfilename = params[4]
    log_number  = params[5]
    seed        = params[6]
    save_freq   = params[7]
    checkpoint  = params[8]
    save_unk    = params[9]

    if outfilename == "-":
      outfile = sys.stdout
    else:
      outfilename = outfilename + ".%05d" % mpi.rank
      if os.path.exists(outfilename):
        sys.stderr.write("Output test file, '%s', exists\n" % outfilename)
        sys.exit(1)
      outfile = file(outfilename, "w")
      
    io = IO(None, outfile, log_number)

    enumerator = Enumerator(states, symbols, steps, 
                            timeout, io, seed, save_freq,
                            checkpoint, save_unk)
    enumerator.enum()
