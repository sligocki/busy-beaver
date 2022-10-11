#! /usr/bin/env python3
"""
Closed Graph Filter (aka CPS, aka Markov) is a twist on CTL where the langauge is a graph-based language.

This is my implementation of savask's Closed Position Set (CPS) decider
  https://gist.github.com/savask/1c43a0e5cdd81229f236dcf2b0611c3f
Which they reverse-engineered from Skelet's program originally.

While reading savask's description, I realized that many of the details he uses
are captured directly in the Block Macro Machine idea.
"""

import argparse
from collections import defaultdict
import math
from pathlib import Path

import Halting_Lib
import IO
from Macro import Turing_Machine
from Macro.Turing_Machine import (LEFT, RIGHT, other_dir,
                                  RUNNING, INF_REPEAT, HALT, UNDEFINED, GAVE_UP)

import io_pb2


DIRS = (LEFT, RIGHT)


def block_to_str(block) -> str:
  return "".join(str(symbol) for symbol in block)

class Config:
  """A subset of a TM configuration. Includes TM state, dir,
  subset of tape (window) and pos on that window."""
  def __init__(self, state, dir, window, block_size, pos = None):
    self.state = state
    self.dir = dir
    self.window = tuple(window)
    self.block_size = block_size

    if pos == None:
      # TM should have block_size symbols in front of it.
      if dir == LEFT:
        pos = block_size - 1
      else:
        assert dir == RIGHT
        pos = len(window) - block_size
    self.pos = pos

  def get_block(self, dir, index):
    start = index * self.block_size
    end = (index + 1) * self.block_size
    if dir == RIGHT:
      # Flip
      start, end = len(self.window) - end, len(self.window) - start
    return self.window[start:end]

  def shift_front(self, new_front):
    if self.dir == LEFT:
      new_window = new_front + self.window[:len(self.window) - self.block_size]
    else:
      new_window = self.window[self.block_size:] + new_front
    return Config(self.state, self.dir, new_window, self.block_size)

  def __str__(self):
    # TM is "looking" at self.pos so different TM directions need slight
    # tweaks for printing.
    if self.dir == LEFT:
      return f"{block_to_str(self.window[:self.pos + 1])} <{self.state} {block_to_str(self.window[self.pos + 1:])}"
    else:
      return f"{block_to_str(self.window[:self.pos])} {self.state}> {block_to_str(self.window[self.pos:])}"

  # Needed to make these work in a set.
  def __hash__(self):
    return hash((self.state, self.dir, self.window, self.pos))
  def __eq__(self, other):
    return (self.state == other.state and self.dir == other.dir and
            self.window == other.window and self.pos == other.pos)


class ClosedGraphSim:
  def __init__(self, tm : Turing_Machine.Simple_Machine,
               block_size : int, window_size : int,
               max_steps : int, max_iters : int, max_configs : int, max_edges : int,
               result : io_pb2.ClosedGraphFilterResult):
    self.tm = tm
    self.block_size = block_size
    self.window_size = window_size
    self.max_steps = max_steps
    self.max_iters = max_iters
    self.max_configs = max_configs
    self.max_edges = max_edges
    self.result = result

    blank_block = (tm.init_symbol,) * self.block_size
    blank_window = (tm.init_symbol,) * self.window_size

    # set of |Config|s to evaluate and add to |transitions|
    self.todo_configs = {
      Config(tm.init_state, RIGHT, blank_window, self.block_size)
    }
    # dict of Config -> PostConfig saving evaluation on window.
    self.transitions = {}
    # continuations[dir][block] = set of blocks that can appear directly after
    # |block| on that half-tape.
    self.continuations = {}
    # Initially, the only continuations are blank block -> blank block
    for dir in DIRS:
      self.continuations[dir] = defaultdict(set)
      self.continuations[dir][blank_block].add(blank_block)


  def run(self):
    self.result.num_iters = 0
    while True:
      self.result.num_iters += 1
      while self.todo_configs:
        # Note: We need to make a copy, since step() updates todo_configs.
        configs = self.todo_configs
        self.todo_configs = set()
        for config in configs:
          sim_condition = self.sim_config(config)
          if sim_condition == RUNNING:
            # Update self.todo_configs and self.continuations
            self.update_set(config)

          elif sim_condition != INF_REPEAT:
            # Failure: Our Closed Graph Set grew too large and now includes
            # a halting config (or a config we gave up trying to simulate ...)
            # NOTE: We allow INF_REPEAT. In this case we know that the TM will
            # for sure be infinite if it gets to this config, so that's great!
            self.result.success = False
            return

      # Re-examine self.transitions to see if any have grown.
      was_modified = False
      configs = frozenset(self.transitions.keys())
      for config in configs:
        if self.update_set(config):
          was_modified = True

      if not was_modified:
        # Success: This set is now closed and thus we have successfully proven
        # that this TM will never halt!
        self.result.success = True
        return

      if (self.result.num_iters >= self.max_iters or
          self.result.num_configs >= self.max_configs or
          self.result.num_edges >= self.max_edges):
        # Failure: Over one of the limits.
        self.result.success = False
        return

  def sim_config(self, old_config : Config):
    """Simulate TM on |old_config| until it leaves the tape, halts, is
    detected infinite or runs too long."""
    max_steps = self.max_steps - self.result.num_steps
    # assert 0 <= old_config.pos < len(old_config.window), str(old_config)
    trans = Turing_Machine.sim_limited(
      self.tm, old_config.state, old_config.window,
      old_config.pos, old_config.dir, max_loops=max_steps)

    if trans.condition == RUNNING:
      # new_pos is outside the window, because we ran off the edge of it.
      if trans.dir_out == LEFT:
        new_pos = -1
      else:
        assert trans.dir_out == RIGHT
        new_pos = len(trans.symbol_out)
      new_config = Config(trans.state_out, trans.dir_out, trans.symbol_out,
                          self.block_size, new_pos)
    else:
      new_config = None

    if trans.condition == INF_REPEAT:
      self.result.found_inf_loop = True

    self.transitions[old_config] = (trans, new_config)
    self.result.num_steps += trans.num_base_steps

    return trans.condition

  def update_set(self, old_config : Config) -> bool:
    """Evaluate TM on this Config until it leaves the limited tape.
    Returns True iff any edges or configs were added."""
    trans, new_config = self.transitions[old_config]

    was_modified = False
    if trans.condition == RUNNING:
      front_dir = trans.dir_out
      behind_dir = other_dir(trans.dir_out)
      # The block furthest behind us in new_config, this is the block that will
      # be removed form the config.
      new_behind_furthest = new_config.get_block(behind_dir, 0)
      # The second furthest block behind us. This will be the new furthest behind
      # block after removing behind_furthest.
      new_behind_second_furthest = new_config.get_block(behind_dir, 1)

      # Update self.continuations by adding edges between blocks behind us.
      # One edge between the two furthest blocks behind us inside of new_config.
      if self.add_edge(behind_dir, new_behind_second_furthest, new_behind_furthest):
        was_modified = True
      # And an edge for all old edges from the previous furthest back
      # to the new furthest back.
      # NOTE: This block may not have been behind in old_config. It is instead
      # the original contents of |new_behind_furthest|.
      old_behind_furthest = old_config.get_block(behind_dir, 0)
      for dst in self.continuations[behind_dir][old_behind_furthest]:
        if self.add_edge(behind_dir, new_behind_furthest, dst):
          was_modified = True

      # Update self.configs by using graphs to find new front block options.
      old_front = old_config.get_block(trans.dir_out, 0)
      for new_front in self.continuations[front_dir][old_front]:
        next_config = new_config.shift_front(new_front)
        if self.add_config(next_config):
          was_modified = True

    return was_modified

  def add_edge(self, dir, src, dst) -> bool:
    # DEBUG: print("    Adding edge", dir, src, dst)
    if dst not in self.continuations[dir][src]:
      self.continuations[dir][src].add(dst)
      self.result.num_edges += 1
      return True
    return False

  def add_config(self, config) -> bool:
    # DEBUG: print("    Adding config", str(config))
    # assert 0 <= config.pos < len(config.window), str(config)
    if config not in self.transitions and config not in self.todo_configs:
      self.todo_configs.add(config)
      self.result.num_configs += 1
      return True
    return False

  def trans_to_string(self, old_config : Config) -> str:
    trans, new_config = self.transitions[old_config]
    if trans.condition == RUNNING:
      return f"{old_config}  --({trans.num_base_steps:3d})-->  {new_config}"
    elif trans.condition == INF_REPEAT:
      return f"{old_config}  -->  (Infinite Loop)"
    elif trans.condition == GAVE_UP:
      return f"{old_config}  --({trans.num_base_steps:3d})-->  (Over Max Steps)"
    else:
      assert trans.condition in (HALT, UNDEFINED)
      return f"{old_config}  --({trans.num_base_steps:3d})-->  (Halt)"

  def print_debug(self):
    print()
    for dir in DIRS:
      print(f"* {dir} continuations:")
      for src in sorted(self.continuations[dir].keys()):
        dst_strs = sorted(block_to_str(dst) for dst in self.continuations[dir][src])
        dsts_str = "{" + ", ".join(dst_strs) + "}"
        print("   ", block_to_str(src), "->", dsts_str)

    print()
    print("* Configs:")
    for config in self.transitions:
      print("   ", self.trans_to_string(config))

    if self.todo_configs:
      for config in self.todo_configs:
        print("   ", str(config))

    print()
    print(f"* #configs={self.result.num_configs} #adj={self.result.num_edges}")


def filter(tm : Turing_Machine.Simple_Machine,
           block_size : int, window_size : int,
           max_steps : int, max_iters : int, max_configs : int, max_edges : int,
           cg_result : io_pb2.ClosedGraphFilterResult,
           bb_status : io_pb2.BBStatus):
  cg_result.Clear()
  graph_set = ClosedGraphSim(tm, block_size, window_size,
                             max_steps, max_iters, max_configs, max_edges,
                             cg_result)
  graph_set.run()
  cg_result.block_size = block_size
  cg_result.window_size = window_size
  if cg_result.success:
    Halting_Lib.set_not_halting(bb_status, io_pb2.INF_CLOSED_GRAPH)
    # Note: quasihalting result is not computed when using Closed Graph filters.
  # Return graph_set in case you want to debug / print the verification details.
  return graph_set


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm_file", type=Path)
  parser.add_argument("record_num", type=int)
  parser.add_argument("block_size", type=int)
  parser.add_argument("window_size", type=int, nargs="?")

  parser.add_argument("--max-steps", type=int, default=1_000_000)
  parser.add_argument("--max-iters", type=int, default=500)
  parser.add_argument("--max-configs", type=int, default=10_000)
  parser.add_argument("--max-edges", type=int, default=10_000)

  parser.add_argument("--verbose", "-v", action="store_true")
  args = parser.parse_args()

  if not args.window_size:
    args.window_size = 3 * args.block_size

  assert args.window_size >= 2 * args.block_size

  cg_result = io_pb2.ClosedGraphFilterResult()
  bb_status = io_pb2.BBStatus()

  tm = IO.load_tm(args.tm_file, args.record_num)
  print(tm.ttable_str())
  graph_set = filter(tm, args.block_size, args.window_size,
                     args.max_steps, args.max_iters, args.max_configs, args.max_edges,
                     cg_result, bb_status)

  if args.verbose:
    graph_set.print_debug()
  print()
  print(cg_result)
  print(bb_status)

if __name__ == "__main__":
  main()
