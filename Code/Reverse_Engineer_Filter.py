#! /usr/bin/env python3
#
# Reverse_Engineer_Filter.py
#
"""
Filters out machines whose halt states obviously cannot be reached based
on a simple end case fact:
  If machine:
    * only halts on symbol 2 and in state B,
    * only writes 2s when moving Left (thus all 2s are on it's Right) and
    * only transitions to state B when moving Left
  then it cannot ever halt.
"""

from Common import Exit_Condition, HALT_STATE
import Halting_Lib
import IO
from IO.TM_Record import TM_Record
from Macro import Turing_Machine
import TM_Enum

import io_pb2

def get_stats(tm):
  """Finds all halt transitions and other statistical info"""
  halts = []
  # List of transitions to this state.
  to_state =  [ [] for i in range(tm.num_states) ]
  # List of transitions which write this symbol.
  to_symbol = [ [] for i in range(tm.num_symbols) ]
  for state in range(tm.num_states):
    for symbol in range(tm.num_symbols):
      trans = tm.trans_table[state][symbol]
      if trans.condition in [Turing_Machine.HALT, Turing_Machine.UNDEFINED]:
        halts.append((state, symbol))
      else:
        assert trans.condition == Turing_Machine.RUNNING
        to_state[trans.state_out].append(((state, symbol), trans))
        to_symbol[trans.symbol_out].append(((state, symbol), trans))
  return halts, to_state, to_symbol

def cannot_reach_halt(halt_state, halt_symbol, to_state, to_symbol):
  """True means it is imposible to reach the halt state.
     False is inconclusive."""
  def same_direction():
    """Test whether all transitions to halt_state are in the same direction as
       all the transitions writing halt_symbol."""
    _, trans = to_state[halt_state][0]
    prehalt_dir = trans.dir_out
    for _, trans in to_state[halt_state]:
      if trans.dir_out != prehalt_dir:
        return False
    for _, trans in to_symbol[halt_symbol]:
      if trans.dir_out != prehalt_dir:
        return False
    # If all trans in the same direction, then we cannot reach this halt.
    return True

  # If no transitions go to halt_state -> never halt (Unless A0 -> Halt)
  if len(to_state[halt_state]) == 0 and (halt_state, halt_symbol) != (0, 0):
    return True
  # Method 1 requires that we write the symbol that we halt on.
  if halt_symbol != 0:
    # If no transitions write the halt_symbol -> never halt (Assumes symbol != 0)
    if len(to_symbol[halt_symbol]) == 0:
      return True
    # If all transitions to halt_state and from halt_symbol are the same
    #   direction and we must write the symbol we halt on we cannot halt.
    if same_direction():
      return True
  # If none of the methods work, we cannot prove it will not halt.
  return False

def is_infinite(tm : Turing_Machine.Simple_Machine) -> bool:
  # Get initial stat info
  halts, to_state, to_symbol = get_stats(tm)
  # See if all halts cannot be reached
  for halt in halts:
    if not cannot_reach_halt(*halt, to_state, to_symbol):
      # This halt transition is reachable. We cannot prove that this TM
      # is infinite.
      return False
  # No halt transitions can be reached -> proven infinite!
  return True


if __name__ == "__main__":
  import sys
  from Option_Parser import Filter_Option_Parser
  # Get command line options.
  opts, args = Filter_Option_Parser(sys.argv, [])

  io = IO.Text.ReaderWriter(opts["infile"], opts["outfile"], opts["log_number"])
  for io_record in io:
    tm = Turing_Machine.Simple_Machine(io_record.ttable)
    tm_enum = TM_Enum.TM_Enum(tm, allow_no_halt = False)
    tm_record = TM_Record(tm_enum = tm_enum)
    if is_infinite(tm):
      tm_record.proto.filter.reverse_engineer.success = True
      Halting_Lib.set_not_halting(tm_record.proto.status,
                                  io_pb2.INF_REVERSE_ENGINEER)
      # Note: quasihalting result is not computable when using Reverse_Engineer filter.
      tm_record.proto.status.quasihalt_status.is_decided = False
    else:
      tm_record.proto.filter.reverse_engineer.success = False
    io.write_record(tm_record)
