#! /usr/bin/env python3
"""Convert TMs from generic form to Tree Normal Form."""

import argparse
import copy
from pathlib import Path

import Direct_Simulator
import IO
from Macro import Turing_Machine

import io_pb2


def permute_table(old_tm, state_order, symbol_order):
  state_old2new = {old: new for (new, old) in enumerate(state_order)}
  symbol_old2new = {old: new for (new, old) in enumerate(symbol_order)}
  new_tm = copy.deepcopy(old_tm)
  for new_state, old_state in enumerate(state_order):
    for new_symbol, old_symbol in enumerate(symbol_order):
      old_trans = old_tm.trans_table[old_state][old_symbol]

      if old_trans.condition == Turing_Machine.RUNNING:
        new_tm.trans_table[new_state][new_symbol] = Turing_Machine.Transition(
          symbol_out = symbol_old2new[old_trans.symbol_out],
          # NOTE: We do not currently support swapping dirs.
          dir_out = old_trans.dir_out,
          state_out = state_old2new[old_trans.state_out],
          # Rest is copied from old_trans
          condition = old_trans.condition,
          condition_details = old_trans.condition_details,
          num_base_steps = old_trans.num_base_steps,
          # We don't need/use this field.
          states_last_seen = None
        )
      else:
        assert old_trans.condition in [Turing_Machine.HALT, Turing_Machine.UNDEFINED]
        new_tm.trans_table[new_state][new_symbol] = Turing_Machine.Transition(
          condition = old_trans.condition,
          symbol_out = 1, dir_out = Turing_Machine.RIGHT,
          state_out = Turing_Machine.Simple_Machine_State(-1),  # Halt
          num_base_steps = 1,
          # We don't need/use this field.
          states_last_seen = None
        )

  return new_tm

def to_TNF(tm, max_steps, skip_over_steps):
  state_order = [0]
  symbol_order = [0]
  unordered_states = set(range(tm.num_states)) - set(state_order)
  unordered_symbols = set(range(tm.num_symbols)) - set(symbol_order)

  sim = Direct_Simulator.DirectSimulator(tm)
  while unordered_states or unordered_symbols:
    if sim.step_num > max_steps:
      if skip_over_steps:
        return
      else:
        raise Exception

    sim.step()

    if sim.state in unordered_states:
      state_order.append(sim.state)
      unordered_states.remove(sim.state)
    cur_symb = sim.tape.read()
    if cur_symb in unordered_symbols:
      symbol_order.append(cur_symb)
      unordered_symbols.remove(cur_symb)

    if len(unordered_states) == 1:
      state_order.append(unordered_states.pop())
    if len(unordered_symbols) == 1:
      symbol_order.append(unordered_symbols.pop())

  return permute_table(tm, state_order, symbol_order)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm_file", type=Path)
  parser.add_argument("--max-steps", type=int, default=1_000)
  parser.add_argument("--skip-over-steps", action="store_true")
  args = parser.parse_args()

  with open(args.tm_file, "r") as infile:
    for io_record in IO.IO(infile, None):
      old_tm = Turing_Machine.Simple_Machine(io_record.ttable)
      new_tm = to_TNF(old_tm, args.max_steps, args.skip_over_steps)
      if new_tm:
        print(new_tm.ttable_str())

if __name__ == "__main__":
  main()