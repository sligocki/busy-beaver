#! /usr/bin/env python
"""Tree Filter which uses the Macro Machine Simulator."""

from Common import Exit_Condition
import IO
from Macro import Chain_Simulator, Turing_Machine, Block_Finder
from Alarm import ALARM, AlarmException

max_step2inf = 0
max_loop2inf = 0

def run(TTable, block_size, level, steps, runtime, recursive, progress):
  # Get and initialize a new simulator object.
  m1 = Turing_Machine.Simple_Machine(TTable)
  if not block_size:
    # Find optimal macro block size automatically.
    block_size = Block_Finder.block_finder(m1, steps // 10)
  m2 = Turing_Machine.Block_Macro_Machine(m1, block_size)
  m3 = Turing_Machine.Backsymbol_Macro_Machine(m2)

  sim = Chain_Simulator.Simulator(m3, recursive)

  # Run with an optional timer.
  try:
    if runtime:
      ALARM.set_alarm(runtime)
      
    sim.loop_run(steps)

    ALARM.cancel_alarm()

  except AlarmException:
    ALARM.cancel_alarm()
    sim.op_state = Turing_Machine.TIME_OUT

  if sim.op_state == Turing_Machine.RUNNING:
    if progress:
      pass #print "\tUnknown", block_size, sim.step_num, sim.num_loops
    return Exit_Condition.MAX_STEPS, sim.get_nonzeros(), sim.step_num
  elif sim.op_state == Turing_Machine.INF_REPEAT:
    if progress:
      global max_step2inf, max_loop2inf
      max_step2inf = max(max_step2inf, sim.step_num)
      max_loop2inf = max(max_loop2inf, sim.num_loops)
      print "\tInfinite", block_size, (sim.step_num, max_step2inf), (sim.num_loops, max_loop2inf)
    return Exit_Condition.INFINITE, 4, block_size, "Macro_Simulator_Filter"
  elif sim.op_state == Turing_Machine.HALT:
    if progress:
      print "\tHalted", sim.get_nonzeros(), sim.step_num
    return Exit_Condition.HALT, sim.get_nonzeros(), sim.step_num
  elif sim.op_state == Turing_Machine.UNDEFINED:
    if progress:
      print "\tUndefined", sim.get_nonzeros(), sim.step_num
    # sim.op_details[0][0 & 1] stores the symbol and state that we halted on.
    return Exit_Condition.UNDEF_CELL, sim.op_details[0][1], sim.op_details[0][0], sim.get_nonzeros(), sim.step_num
  elif sim.op_state == Turing_Machine.TIME_OUT:
    if progress:
      print "\tTimeout", block_size, sim.step_num, sim.num_loops
    return Exit_Condition.TIME_OUT, sim.get_nonzeros(), sim.step_num
  else:
    raise Exception, "unexpected op_state"

if __name__ == "__main__":
  import sys
  from Option_Parser import Filter_Option_Parser

  # Get command line options.
  opts, args = Filter_Option_Parser(sys.argv,
      [("size"     , int,   None, False, True),
       ("level"    , int,      3, False, True),
       ("time"     , float, None, False, True),
       ("recursive", None,  None, False, False),
       ("progress" , None,  None, False, False)])

  log_number = opts["log_number"]
  progress = opts["progress"]
  io = IO.IO(opts["infile"], opts["outfile"], log_number)
  next = io.read_result()

  num_halt = 0
  num_undefined = 0

  while next:
    if progress:
      pass #print next[0], # Machine Number
    TTable = next[6]
    # Run the simulator/filter on this machine.
    results = run(TTable, opts["size"], opts["level"], opts["steps"], 
                  opts["time"], opts["recursive"], progress)

    # If we could not decide anything, leave the old result alone.
    if results[0] in Exit_Condition.UNKNOWN_SET:
      io.write_result_raw(*next)
    # Otherwise classify it as beeing decided in some way.
    else:
      # We do not expect to find halting machines with this filter.
      # However, finding them is not a problem, but user should know.
      if results[0] == Exit_Condition.HALT:
        num_halt += 1
      if results[0] == Exit_Condition.UNDEF_CELL:
        num_undefined += 1
      old_results = next[5]
      io.write_result_raw(*(next[0:5]+
                            (results, TTable, log_number, old_results)))

    next = io.read_result()

  # Print number of TMs that halted.
  if num_halt > 0:
    sys.stderr.write("%d in file: %s - halted!\n" % 
                     (num_halt, opts["infilename"]))

  # Print number of TMs that reached an undefined transition.
  if num_undefined > 0:
    sys.stderr.write("%d in file: %s - undefined transitions reached!\n" %
                     (num_undefined, opts["infilename"]))
