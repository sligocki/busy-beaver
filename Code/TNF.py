#! /usr/bin/env python3
"""
Convert TMs from generic form to Tree Normal Form.

Note: Only permutes states/symbols/directions. It does not remove unreachable transitions.
"""

import argparse
import copy
import sys

import Direct_Simulator
import IO
from Macro import Turing_Machine


def permute_table(old_tm, state_order, symbol_order, swap_dirs=False):
  state_old2new = {old: new for (new, old) in enumerate(state_order)}
  symbol_old2new = {old: new for (new, old) in enumerate(symbol_order)}
  new_tm = copy.deepcopy(old_tm)
  for new_state, old_state in enumerate(state_order):
    for new_symbol, old_symbol in enumerate(symbol_order):
      old_trans = old_tm.trans_table[old_state][old_symbol]

      if old_trans.condition == Turing_Machine.RUNNING:
        if swap_dirs:
          new_dir = Turing_Machine.other_dir(old_trans.dir_out)
        else:
          new_dir = old_trans.dir_out

        new_tm.trans_table[new_state][new_symbol] = Turing_Machine.Transition(
          symbol_out = symbol_old2new[old_trans.symbol_out],
          dir_out = new_dir,
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

def to_TNF(tm : Turing_Machine.Simple_Machine, max_steps : int) -> Turing_Machine.Simple_Machine | None:
  state_order = [0]
  symbol_order = [0]
  unordered_states = set(range(tm.num_states)) - set(state_order)
  unordered_symbols = set(range(tm.num_symbols)) - set(symbol_order)
  # If first trans is to the LEFT, swap dirs.
  swap_dirs = (tm.get_trans_object(tm.init_symbol, tm.init_state).dir_out
               == Turing_Machine.LEFT)

  sim = Direct_Simulator.DirectSimulator(tm)
  while unordered_states or unordered_symbols:
    if sim.step_num > max_steps or sim.halted:
      return None

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

  return permute_table(tm, state_order, symbol_order, swap_dirs)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm", nargs="?",
                      help="Literal Turing Machine. If missing read from stdin.")
  parser.add_argument("--max-steps", type=int, default=1_000)
  args = parser.parse_args()

  with IO.StdText.Writer(sys.stdout) as writer:
    if args.tm:
      tm = IO.parse_tm(args.tm)
      new_tm = to_TNF(tm, args.max_steps)
      if new_tm:
        writer.write_tm(new_tm)
      else:
        print(f"Failed to find TNF for {tm.ttable_str()}")
    else:
      with IO.StdText.Reader(sys.stdin) as reader:
        for tm_record in reader:
          new_tm = to_TNF(tm_record.tm(), args.max_steps)
          if new_tm:
            writer.write_tm(new_tm)
          else:
            print(f"Failed to find TNF for {tm.ttable_str()}")

if __name__ == "__main__":
  main()
