#! /usr/bin/env python3
"""
Closed Graph Filter is a twist on CTL where the langauge is a graph-based language.

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

import IO
from Macro import Turing_Machine
from Macro.Turing_Machine import (LEFT, RIGHT, other_dir,
                                  RUNNING, INF_REPEAT, HALT, UNDEFINED, GAVE_UP)


DIRS = (LEFT, RIGHT)


class Config:
  """A fixed-sized (3 symbol) subset of a TM configuration. Includes TM state,
  dir and subset of tape (always 1 symbol in front and 2 behind)."""
  def __init__(self, state, dir, subtape):
    self.state = state
    self.dir = dir
    # |subtape| is a sequence of 3 symbols around the TM head (1 in front, 2 behind).
    # It is always interpretted left to right so context[0] is the left-most symbol
    # That's the one in front of the TM if TM is pointed left, or 2 behind if it's
    # pointed right.
    self.subtape = tuple(subtape)

  def __str__(self):
    if self.dir == LEFT:
      return f"{self.subtape[0]} <{self.state} {self.subtape[1]} {self.subtape[2]}"
    else:
      return f"{self.subtape[0]} {self.subtape[1]} {self.state}> {self.subtape[2]}"

  # Needed to make these work in a set.
  def __hash__(self):
    return hash((self.state, self.dir, self.subtape))
  def __eq__(self, other):
    return (self.state == other.state and self.dir == other.dir and
            self.subtape == other.subtape)


class GraphSet:
  @classmethod
  def BlankTape(cls, init_state, init_symbol):
    graph_set = GraphSet()

    # Start position on blank tape.
    graph_set.configs = {
      Config(init_state, RIGHT, (init_symbol, init_symbol, init_symbol))
    }

    # graph[dir][block] = set of blocks that can appear directly after |block|
    # on that half-tape. This forms a directed graph of blocks (macro symbols).
    # Initially the only allowed blocks are 0 blocks following 0 blocks (empty tape).
    graph_set.graph = {}
    for dir in DIRS:
      graph_set.graph[dir] = defaultdict(set)
      graph_set.graph[dir][init_symbol].add(init_symbol)

    return graph_set

  def step(self, tm, config : Config, max_macro_steps : int):
    """Evaluate TM on this Config until it leaves the limited tape.
    Returns a pair: (TM condition, was_modified)."""
    was_modified = False
    # DEBUG: print("  Start config", str(config))

    if config.dir == LEFT:
      pos = 0
    else:
      pos = len(config.subtape) - 1
    # Limit max_loops so that we don't run for too long on extreme examples.
    trans = Turing_Machine.sim_limited(
      tm, config.state, config.subtape, pos, config.dir,
      max_loops=max_macro_steps)

    # DEBUG: print("    End config", trans.condition, trans.symbol_out, trans.dir_out, trans.state_out)
    if trans.condition == RUNNING:
      if trans.dir_out == LEFT:
        behind_post_close, behind_post_mid, behind_post_far = trans.symbol_out
        front_pre, behid_pre_mid, behind_pre_far = config.subtape
      else:
        assert trans.dir_out == RIGHT
        behind_post_far, behind_post_mid, behind_post_close = trans.symbol_out
        behind_pre_far, behid_pre_mid, front_pre = config.subtape

      # Update self.graph by adding edges between blocks behind us.
      # One edge between the two furthest blocks behind us.
      if self.add_edge(other_dir(trans.dir_out), behind_post_mid, behind_post_far):
        was_modified = True
      # And an edge for all old edges from the previous furthest back
      # to the new furthest back.
      for dst in self.graph[other_dir(trans.dir_out)][behind_pre_far]:
        if self.add_edge(other_dir(trans.dir_out), behind_post_far, dst):
          was_modified = True

      # Update self.configs by using graphs to find new front block options.
      for new_front in self.graph[trans.dir_out][front_pre]:
        if trans.dir_out == LEFT:
          new_subtape = (new_front, behind_post_close, behind_post_mid)
        else:
          assert trans.dir_out == RIGHT
          new_subtape = (behind_post_mid, behind_post_close, new_front)

        if self.add_config(Config(trans.state_out, trans.dir_out, new_subtape)):
          was_modified = True

    return trans.condition, was_modified

  def add_edge(self, dir, src, dst) -> bool:
    # DEBUG: print("    Adding edge", dir, src, dst)
    if dst not in self.graph[dir][src]:
      self.graph[dir][src].add(dst)
      return True
    return False

  def add_config(self, config) -> bool:
    # DEBUG: print("    Adding config", str(config))
    if config not in self.configs:
      self.configs.add(config)
      return True
    return False

  def print_debug(self):
    print()
    print("* Left continuations:")
    for src, dsts in sorted(self.graph[LEFT].items()):
      print("   ", src, "->", dsts)

    print()
    print("* Right continuations:")
    for src, dsts in sorted(self.graph[RIGHT].items()):
      print("   ", src, "->", dsts)

    print()
    print("* Configs:")
    config_strs = [str(config) for config in self.configs]
    for config_str in sorted(config_strs):
      print("   ", config_str)

    print()
    print(f"* #configs={len(self.configs)}")


# TODO
class ClosedGraphResult:
  def __init__(self, success : bool, num_iters : int, num_configs : int,
               had_inf_rep_macro_step : bool):
    self.success = success
    self.num_iters = num_iters
    self.num_configs = num_configs
    self.had_inf_rep_macro_step = had_inf_rep_macro_step


def test_closed_graph(tm : Turing_Machine.Simple_Machine,
                      block_size : int, offset : int,
                      max_configs : int, max_steps_per_rule : int):
  sqrt_max_steps = int(math.sqrt(max_steps_per_rule))
  if block_size > 1:
    # Limit max_sim_steps_per_symbol so that we don't run for too long on
    # extreme examples.
    tm = Turing_Machine.Block_Macro_Machine(tm, block_size, offset,
                                            max_sim_steps_per_symbol = sqrt_max_steps)

  # We maintain a set of Configs (1 block neighborhoods around TM head) and
  # graphs which tell us which new symbols we must search once this TM makes
  # a macro step.
  # We iteratively increase these sets until either:
  #   1) We add a Halt transition -> failure.
  #   2) They stabilize (closed under TM step) with no Halt positions -> success!
  graph_set = GraphSet.BlankTape(tm.init_state, tm.init_symbol)
  num_iters = 0
  while True:
    # DEBUG: print("Num Iters", num_iters)
    was_modified = False
    # Note: We need to make a copy, since graph_set.step() updates graph_set.configs.
    old_configs = frozenset(graph_set.configs)
    for config in old_configs:
      # TODO-maybe: Make this more efficient by avoiding re-stepping for configs
      # we've already stepped from in a previous iteration?
      # NOTE: This is not trivial because if graph_set.graph changed, that can
      # change the new configs!
      tm_condition, this_modified = graph_set.step(tm, config, sqrt_max_steps)
      if this_modified:
        was_modified = True
      if tm_condition not in (RUNNING, INF_REPEAT):
        # Failure, Our Closed Graph Set grew too large and now includes
        # a halting config (or a config we gave up trying to simulate ...)
        # NOTE: We allow INF_REPEAT. In this case we know that the TM will
        # for sure be infinite if it gets to this config, so that's great!
        return False, num_iters, len(graph_set.configs)

    num_iters += 1
    if not was_modified:
      graph_set.print_debug()
      # Success, we've found a GraphSet closed under step() with no Halting
      # configs, so we have proven that this TM will never halt.
      return True, num_iters, len(graph_set.configs)

    if len(graph_set.configs) >= max_configs:
      # Failure, we gave up trying to find the closure of the GraphSet.
      return False, num_iters, len(graph_set.configs)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("filename")
  parser.add_argument("record_num", type=int)
  parser.add_argument("block_size", type=int)
  parser.add_argument("offset", type=int)
  parser.add_argument("max_configs", type=int)
  parser.add_argument("--max-steps-per-rule", type=int, default=1_000_000)
  args = parser.parse_args()

  tm = IO.load_tm(args.filename, args.record_num)
  success, num_iters, num_configs = test_closed_graph(
    tm, block_size=args.block_size, offset=args.offset, max_configs=args.max_configs,
    max_steps_per_rule=args.max_steps_per_rule)
  print()
  print("Proven Infinite?:", success)
  print("Iterations:", num_iters)
  print("Num Configs:", num_configs)

if __name__ == "__main__":
  main()
