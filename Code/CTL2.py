#! /usr/bin/env python3
#
# CTL2.py
#
"""
Runs the CTL (A* B) on a machine to discover infinite behavior
"""

import sys
import argparse
import time

import IO
from Macro import Turing_Machine, Simulator
import globals

DIR_NAME = {
  Turing_Machine.LEFT:  "L",
  Turing_Machine.RIGHT: "R",
}

class CTL_Table(dict):
  def __getitem__(self, key):
    if key not in self:
      self[key] = ((set(), set()), (set(), set()))
    return dict.__getitem__(self, key)

def CTL(machine, config, verbose=False):
  """Runs the CTL on a machine given an advaced tape config"""
  # Initialize the table with the current configuration
  new_table = CTL_Table()
  for d in range(2):
    for symb in config.tape[d][:-1]:
      new_table[config.state, config.dir][d][0].add(symb)
    if len(config.tape[d]) == 0:
      new_table[config.state, config.dir][d][1].add(machine.init_symbol)
    else:
      new_table[config.state, config.dir][d][1].add(config.tape[d][-1])
  # Iterate through the table completing it, until:
  #   1) It includes a halt (Failure)
  #   2) The table is unchanged after iteration (Success)
  table = None
  num_iters = 0

  while table != new_table:
    if not globals.time_remaining:
      print("--- CTL2 timeout ---")
      sys.stdout.flush()
      return False, num_iters

    if verbose:
      for term in new_table:
        print(term,":",new_table[term])
      print()

    table, new_table = new_table, CTL_Table()
    for state, dir in table:
      # We could be looking at any of these symbols in A
      for symb in table[state, dir][dir][0]:
        trans = machine.get_trans_object(symb, state, dir)
        if trans.condition != Turing_Machine.RUNNING:
          return False, num_iters
        if verbose:
          print("(", symb, state, DIR_NAME[dir], ") -> (",
                trans.symbol_out, trans.state_out, DIR_NAME[trans.dir_out], ")")
        # Ex: (3) (1|5)* A> 4 (1|4|5)* (0) -> (3) (1|5)* <B 2 (1|4|5)* (0)
        # table[<B][0] = table[A>][0]; table[<B][1] = table[A>][1] + [2]
        for d in range(2):
          for s in range(2):
            new_table[trans.state_out, trans.dir_out][d][s].update(table[state, dir][d][s])
        new_table[trans.state_out, trans.dir_out][not trans.dir_out][0].add(trans.symbol_out)
      # Or we could be looking at a symbol in B
      for symb in table[state, dir][dir][1]:
        trans = machine.get_trans_object(symb, state, dir)
        if trans.condition != Turing_Machine.RUNNING:
          return False, num_iters
        if verbose:
          print("(", symb, state, DIR_NAME[dir], ") -> (",
                trans.symbol_out, trans.state_out, DIR_NAME[trans.dir_out], ")")
        for s in range(2):
          new_table[trans.state_out, trans.dir_out][not dir][s].update(table[state, dir][not dir][s])
        if trans.dir_out == dir:
          # Ex: (3) (1|5)* A> (1) -> (3) (1|5)* 2 B>
          new_table[trans.state_out, trans.dir_out][not trans.dir_out][0].add(trans.symbol_out)
          new_table[trans.state_out, trans.dir_out][trans.dir_out][1].add(machine.init_symbol)
        else: # trans.dir_out != dir
          # Ex: (3) (1|5)* A> (1) -> (3) (1|5)* <B 2
          new_table[trans.state_out, trans.dir_out][not trans.dir_out][1].add(trans.symbol_out)
    # Make new_table complete by unioning it with table
    for x in table:
      for d in range(2):
        for s in range(2):
          new_table[x][d][s].update(table[x][d][s])
    num_iters += 1
  return True, num_iters

class GenContainer:
  """Generic Container class"""
  def __init__(self, **args):
    for atr in args:
      self.__dict__[atr] = args[atr]

def test_CTL(base_tm, cutoff, block_size=1, offset=None, use_backsymbol=True,
             verbose=False):
  if verbose:
    print(base_tm.ttable_str())
  m = base_tm
  if block_size != 1:
    m = Turing_Machine.Block_Macro_Machine(m, block_size, offset)
  if use_backsymbol:
    m = Turing_Machine.Backsymbol_Macro_Machine(m)
  options = Simulator.create_default_options()
  options.prover = False
  sim = Simulator.Simulator(m, options)
  sim.seek(cutoff)
  if sim.op_state != Turing_Machine.RUNNING:
    return False, 0
  if verbose:
    print(sim.state, sim.tape)
    print()
  tape = [None, None]
  for d in range(2):
    # Pass all symbols from this side of tape except for inf 0s
    #   and possibly the last symbol before the inf 0s
    tape[d] = [block.symbol for block in reversed(sim.tape.tape[d][1:])]
    if len(sim.tape.tape[d]) >= 2 and sim.tape.tape[d][1].num > 1:
      tape[d].append(sim.tape.tape[d][1].symbol)
  config = GenContainer(state=sim.state, dir=sim.dir, tape=tape)
  return CTL(m, config, verbose=verbose)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm", help="Turing Machine or file or file:record_num (0-indexed).")
  parser.add_argument("cutoff", type=int)
  parser.add_argument("block_size", type=int)
  parser.add_argument("offset", type=int)
  parser.add_argument("--no-backsymbol", action="store_true")
  args = parser.parse_args()

  tm = IO.get_tm(args.tm)
  success, num_iters = test_CTL(
    tm, cutoff=args.cutoff, block_size=args.block_size, offset=args.offset,
    use_backsymbol=(not args.no_backsymbol), verbose=True)
  print()
  if success:
    print("Success :) in", num_iters, "iterations")
  else:
    print("Failure :( in", num_iters, "iterations")

if __name__ == "__main__":
  main()
