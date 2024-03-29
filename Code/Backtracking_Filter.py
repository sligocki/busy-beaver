#! /usr/bin/env python3
"""
Filters out machines whose halt states obviously cannot be reached based
on backtracking.
"""

import argparse
import copy
from pathlib import Path
import sys

from Common import HALT_STATE
import Halting_Lib
import IO

import io_pb2


# Constants
BACKTRACK = "Backtrack"

def get_info(TTable):
  """Finds all halt transitions, transitions that could get to
  each state and all of the single-sided symbols."""
  num_states = len(TTable)
  num_symbols = len(TTable[0])
  halts = []
  to_state = [[] for x in range(num_states)]
  dir_to_symbol = [[False, False] for x in range(num_symbols)]
  # The zero symbol is in both directions by default.
  dir_to_symbol[0] = [True, True]
  for state_in in range(num_states):
    for symbol_in in range(num_symbols):
      symbol_out, dir_out, state_out = cell = TTable[state_in][symbol_in]
      if state_out == HALT_STATE:
        # Counts both halting and undefined transitions.
        halts.append((state_in, symbol_in))
      else:
        # Add this input transition to those that can lead to this state.
        to_state[state_out].append(((state_in, symbol_in), cell))
        # And note that that this symbol can be found on the opposite
        # side of the tape (the direction we are moving away from).
        dir_to_symbol[symbol_out][not dir_out] = True
  return halts, to_state, dir_to_symbol

class Partial_Config:
  def __init__(self, state, symbol):
    self.dir = ([], [])
    self.current = symbol
    self.state = state

  def __repr__(self):
    return "%r %r %r %r" % (self.dir[0], self.state, self.current, self.dir[1])

  def applies(self, addr, cell):
    """Tests whether this transition could have been applied to reach
    this configuration."""
    (state_in, symbol_in) = addr
    (symbol_out, dir_out, state_out) = cell
    return len(self.dir[not dir_out]) == 0 or \
           self.dir[not dir_out][0] == symbol_out

  def apply_trans(self, addr, cell):
    """Return a new configuration with transition applied backwards."""
    (state_in, symbol_in) = addr
    (symbol_out, dir_out, state_out) = cell
    new_config = copy.deepcopy(self)
    # Back away from the current symbol.
    new_config.dir[dir_out].insert(0, new_config.current)
    # Step onto the symbol we came from.
    if len(new_config.dir[not dir_out]) != 0:
      del new_config.dir[not dir_out][0]
    # Set the symbol and state to what they must have been to apply this
    # transition.
    new_config.current = symbol_in
    new_config.state = state_in
    return new_config

def is_init_config(config):
  """Is this config the start configuration? If so, stop backtracking.
  We've proven this machine halts (in the most ass-backwards way :/ )."""
  if config.current != 0 or config.state != 0:
    return False
  for side in config.dir:
    for symbol in side:
      if symbol != 0:
        return False
  return True

def is_possible_config(config, dir_to_symbol):
  """Is this configuration possible? Based solely off of dir_to_symbol
  which stores which symbols can be on which sides of the tape."""
  for dir in range(2):
    for symbol in config.dir[dir]:
      if not dir_to_symbol[symbol][dir]:
        return False
  return True

class BacktrackResult:
  def __init__(self, success, halted, max_steps, max_width, num_nodes):
    self.success = success
    self.halted = halted
    self.max_steps = max_steps
    self.max_width = max_width
    self.num_nodes = num_nodes

  def merge(self, other):
    self.success = self.success and other.success
    self.halted = self.halted or other.halted
    self.max_steps = max(self.max_steps, other.max_steps)
    self.max_width = max(self.max_width, other.max_width)
    self.num_nodes += other.num_nodes

def backtrack_single_halt(halt_state, halt_symbol,
                          to_state, dir_to_symbol, steps, max_width_allowed):
  """Try backtrackying |steps| steps from this specific halting
  config. |to_state| is a list of transitions that lead to each state.
  |dir_to_symbol| indicates which direction symbols can be found."""
  pos_configs = [Partial_Config(halt_state, halt_symbol)]
  max_width_seen = len(pos_configs)
  num_nodes = 0
  for i in range(steps):
    # All configurations that could lead to pos_configs in one step.
    prev_configs = []
    for config in pos_configs:
      num_nodes += 1
      for addr, cell in to_state[config.state]:
        if config.applies(addr, cell):
          prev_config = config.apply_trans(addr, cell)
          if is_init_config(prev_config):
            # We've proven that we can get to halt from the initial config.
            # Probably this should not happen in practice because we will
            # simulate all machines for more steps forwards before trying
            # to simulate them backwards, but we keep this for correctness.
            return BacktrackResult(success = False, halted = True,
                                   max_steps = i + 1, max_width = max_width_seen,
                                   num_nodes = num_nodes)
          if is_possible_config(prev_config, dir_to_symbol):
            prev_configs.append(prev_config)
    pos_configs = prev_configs
    max_width_seen = max(max_width_seen, len(pos_configs))
    if len(pos_configs) == 0:
      return BacktrackResult(success = True, halted = False,
                             max_steps = i + 1, max_width = max_width_seen,
                             num_nodes = num_nodes)
    elif max_width_seen > max_width_allowed:
      break
  return BacktrackResult(success = False, halted = False,
                         max_steps = i + 1, max_width = max_width_seen,
                         num_nodes = num_nodes)

def backtrack_ttable(TTable, steps, max_width):
  """Try backtracking |steps| steps for each halting config in TTable,
  giving up if there are more than |max_width| possible configs."""
  # Get initial ttable info.
  halts, to_state, dir_to_symbol = get_info(TTable)
  combined_result = None
  # See if all halts cannot be reached
  for halt_state, halt_symbol in halts:
    for symbol_out, dir_out, state_out in TTable[halt_state]:
      if state_out == halt_state:
        # Optimization: Fail early if there are any Q -> Q transitions
        # (for any Q -> Halt).
        # TODO(shawn): With new improvements, this initial criterion may be
        # stifling.
        # For example, this is why we cannot prove "1RB ---  1LB 1RZ" Halting.
        return BacktrackResult(success = False, halted = False,
                               max_steps = 0, max_width = 0, num_nodes = 0)

    result = backtrack_single_halt(halt_state, halt_symbol,
                                   to_state, dir_to_symbol,
                                   steps, max_width)
    # If any of the backtracks fail, the whole thing fails.
    if not result.success:
      return result

    if combined_result:
      combined_result.merge(result)
    else:
      combined_result = result

  # If all halt states cannot be reached, we have succeeded!
  return combined_result

def backtrack(tm_record, num_steps, max_width):
  info = tm_record.proto.filter.backtrack
  with IO.Timer(info.result):
    TTable = IO.parse_ttable(tm_record.tm().ttable_str())
    # Run the simulator/filter on this machine
    result = backtrack_ttable(TTable, num_steps, max_width)

    info.parameters.num_steps = num_steps
    info.parameters.max_width = max_width
    info.result.success = result.success
    info.result.max_steps = result.max_steps
    info.result.max_width = result.max_width
    info.result.num_nodes = result.num_nodes
    # Note: quasihalting result is not computed when using Backtracking filter.
    tm_record.proto.status.quasihalt_status.is_decided = False
    if result.success:
      assert not result.halted
      Halting_Lib.set_not_halting(tm_record.proto.status, io_pb2.INF_BACKTRACK)
      return True
  return False


def main(argv):
  parser = argparse.ArgumentParser()
  parser.add_argument("--infile", type=Path, required=True)
  parser.add_argument("--outfile", type=Path, required=True)

  parser.add_argument("--steps", type=int, required=True,
                      help="Number of steps to backtrack.")
  parser.add_argument("--max-width", type=int, default=10,
                      help="Maximum width of backtracking tree. (Maximum number "
                      "of configs to keep track of while backtracking.)")
  args = parser.parse_args()

  with IO.Proto.Writer(args.outfile) as writer:
    with IO.Reader(args.infile) as reader:
      for tm_record in reader:
        backtrack(tm_record, args.steps, args.max_width)
        writer.write_record(tm_record)

if __name__ == "__main__":
  main(sys.argv)
