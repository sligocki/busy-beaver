#! /usr/bin/env python3
"""Convert TMs from generic form to Tree Normal Form."""

import argparse
from pathlib import Path

import Direct_Simulator
import IO
import Output_Machine

import io_pb2


def permute_table(old_ttable, state_order, symbol_order):
  state_old2new = {old: new for (new, old) in enumerate(state_order)}
  symbol_old2new = {old: new for (new, old) in enumerate(symbol_order)}
  new_ttable = [[None] * len(symbol_order)
                for _ in range(len(state_order))]
  for new_state, old_state in enumerate(state_order):
    for new_symbol, old_symbol in enumerate(symbol_order):
      (old_symbol_out, dir_out, old_state_out) = old_ttable[old_state][old_symbol]

      new_symbol_out = symbol_old2new[old_symbol_out]
      new_state_out = state_old2new[old_state_out]

      new_ttable[new_state][new_symbol] = (
        new_symbol_out, dir_out, new_state_out)

  return new_ttable

def to_TNF(old_ttable, max_steps):
  state_order = [0]
  symbol_order = [0]
  unordered_states = set(range(len(old_ttable))) - set(state_order)
  unordered_symbols = set(range(len(old_ttable[0]))) - set(symbol_order)

  sim = Direct_Simulator.DirectSimulator(old_ttable)
  while unordered_states or unordered_symbols:
    if sim.step_num > max_steps:
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

  return permute_table(old_ttable, state_order, symbol_order)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm_file", type=Path)
  parser.add_argument("--max-steps", type=int, default=1_000)
  args = parser.parse_args()

  with open(args.tm_file, "r") as infile:
    for io_record in IO.IO(infile, None):
      new_ttable = to_TNF(io_record.ttable, args.max_steps)
      print(Output_Machine.display_ttable(new_ttable))

if __name__ == "__main__":
  main()
