#! /usr/bin/env python
#
# Tree Filter which uses the Macro Machine Simulator

import IO, Macro_Simulator
from Macro_Simulator import HALT_STATE, INF

max_step2inf = 0

# Return Conditions
ERROR = -1
HALT = 0
OVER_TAPE = 1
MAX_STEPS = 2
UNKNOWN = (OVER_TAPE, MAX_STEPS)
UNDEF_CELL = 3
INFINITE = 4

def run(TTable, macro_size, level, steps, progress):
  # Get and initialize a new simulator object
  sim = Macro_Simulator.Macro_Simulator()
  sim.init_new(TTable, macro_size, level)
  sim.seek(steps)
  if sim.state == HALT_STATE:
    if progress:
      print "Halted", sim.tape.get_nonzeros(), sim.cur_step_num
    return HALT, sim.tape.get_nonzeros(), sim.cur_step_num
  elif sim.state == INF:
    if progress:
      global max_step2inf
      max_step2inf = max(max_step2inf, sim.cur_step_num)
      print "\t\tInfinite", sim.cur_step_num, max_step2inf
    return INFINITE, 3, macro_size, "Macro_Tree_Filter"
  else:
    if progress:
      print "Unknown", sim.tape.get_nonzeros(), sim.cur_step_num
    return MAX_STEPS, sim.tape.get_nonzeros(), sim.cur_step_num

if __name__ == "__main__":
  import sys
  from Option_Parser import Filter_Option_Parser

  # Get command line options.
  opts, args = Filter_Option_Parser(sys.argv, [("size" , int, None,  True, True),
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
      if results[0] is HALT:
        sys.stderr.write("Macro_Tree_Filter encountered halting machine!\nNumber: %d in file: %s" % (next[0], opts["infile"]))
      old_results = next[5]
      io.write_result_raw(*(next[0:5]+(results, TTable, log_number, old_results)))

    next = io.read_result()
