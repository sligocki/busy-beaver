#! /usr/bin/env python
#
# Tree Filter which uses the Macro Machine Simulator

import IO
from Macro import Chain_Simulator, Turing_Machine, Block_Finder

max_step2inf = 0
max_loop2inf = 0

# Return Conditions
ERROR = -1
HALT = 0
OVER_TAPE = 1
MAX_STEPS = 2
UNKNOWN = (OVER_TAPE, MAX_STEPS)
UNDEF_CELL = 3
INFINITE = 4

def run(TTable, block_size, level, steps, progress):
  # Get and initialize a new simulator object
  m1 = Turing_Machine.Simple_Machine(TTable)
  if not block_size:
    # Find optimal macro block size automatically
    block_size = Block_Finder.block_finder(m1, steps // 10)
  m2 = Turing_Machine.Block_Macro_Machine(m1, block_size)
  m3 = Turing_Machine.Backsymbol_Macro_Machine(m2)

  sim = Chain_Simulator.Simulator()
  sim.init(m3)
  sim.loop_run(steps)
  if sim.op_state == Turing_Machine.RUNNING:
    if progress:
      print "Unknown", block_size, sim.step_num, sim.num_loops
    return MAX_STEPS, sim.get_nonzeros(), sim.step_num
  elif sim.op_state == Turing_Machine.INF_REPEAT:
    if progress:
      global max_step2inf, max_loop2inf
      max_step2inf = max(max_step2inf, sim.step_num)
      max_loop2inf = max(max_loop2inf, sim.num_loops)
      print "\t\tInfinite", block_size, (sim.step_num, max_step2inf), (sim.num_loops, max_loop2inf)
    return INFINITE, 4, block_size, "Macro_Tree_Filter2"
  elif sim.op_state == Turing_Machine.HALT:
    if progress:
      print "\t\t\tHalted", sim.get_nonzeros(), sim.step_num
    return HALT, sim.get_nonzeros(), sim.step_num
  elif sim.op_state == Turing_Machine.UNDEFINED:
    if progress:
      print "\t\t\tUndefined", sim.get_nonzeros(), sim.step_num
    # sim.op_details[0][0 & 1] stores the symbol and state that we halted on
    return UNDEF_CELL, sim.op_details[0][0], sim.op_details[0][1], sim.get_nonzeros(), sim.step_num
  else:
    raise Exception, "unexpected op_state"

if __name__ == "__main__":
  import sys
  from Option_Parser import Filter_Option_Parser

  # Get command line options.
  opts, args = Filter_Option_Parser(sys.argv, [("size" , int, None, False, True),
                                               ("level", int,    3, False, True),
                                               ("progress", None, None, False, False)])

  log_number = opts["log_number"]
  progress = opts["progress"]
  io = IO.IO(opts["infile"], opts["outfile"], log_number)
  next = io.read_result()

  while next:
    if progress:
      print next[0], # Machine Number
    TTable = next[6]
    # Run the simulator/filter on this machine
    results = run(TTable, opts["size"], opts["level"], opts["steps"], progress)

    # If we could not decide anything, leave the old result alone.
    if results[0] in UNKNOWN:
      io.write_result_raw(*next)
    # Otherwise classify it as beeing decided in some way.
    else:
      # We do not expect to find halting machines with this filter.
      # However, finding them is not a problem, but user should know.
      if results[0] == HALT:
        sys.stderr.write("Number: %d in file: %s - halted!\n" % (next[0], opts["infilename"]))
      if results[0] == UNDEF_CELL:
        sys.stderr.write("Number: %d in file: %s - undefined cell!\n" % (next[0], opts["infilename"]))
      old_results = next[5]
      io.write_result_raw(*(next[0:5]+(results, TTable, log_number, old_results)))

    next = io.read_result()
