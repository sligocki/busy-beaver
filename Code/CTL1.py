#! /usr/bin/env python3
#
# CTL1.py
#
"""
Runs the trivial CTL (A*) on a machine to discover infinite behavior
"""

import argparse
import time

import IO
from Macro import Turing_Machine, Simulator

DIR_NAME = {
  Turing_Machine.LEFT:  "L",
  Turing_Machine.RIGHT: "R",
}

class CTL_Table(dict):
  def __getitem__(self, key):
    if key not in self:
      self[key] = (set(), set())
    return dict.__getitem__(self, key)

def CTL(machine, config, end_time=None, verbose=False):
  """Runs the CTL on a machine given an advaced tape config"""
  # Initialize the table with the current configuration
  new_table = CTL_Table()
  for d in range(2):
    new_table[config.state, config.dir]
    for symb in config.tape[d]:
      new_table[config.state, config.dir][d].add(symb)
  # Iterate through the table completing it, until:
  #   1) It includes a halt (Failure)
  #   2) The table is unchanged after iteration (Success)
  table = None
  num_iters = 0
  while table != new_table:
    if end_time and time.time() >= end_time:
      return False, num_iters

    if verbose:
      for term in new_table:
        print(term,":",new_table[term])
      print()

    table, new_table = new_table, CTL_Table()
    for state, dir in table:
      # We could be looking at any of these symbols
      for symb in table[state, dir][dir]:
        trans = machine.get_trans_object(symb, state, dir)
        if trans.condition != Turing_Machine.RUNNING:
          return False, num_iters
        if verbose:
          print("(", symb, state, DIR_NAME[dir], ") -> (",
                trans.symbol_out, trans.state_out, DIR_NAME[trans.dir_out], ")")

        # Ex: (1|5)* A> 4 (1|4|5)* -> (1|5)* <B 2 (1|4|5)*
        # table[<B][0] = table[A>][0]; table[<B][1] = table[A>][1] + [2]
        for d in range(2):
          new_table[trans.state_out, trans.dir_out][d].update(table[state, dir][d])
        new_table[trans.state_out, trans.dir_out][not trans.dir_out].add(
          trans.symbol_out)
      # Or we could be looking at blank (i.e. 00...)
      symb = machine.init_symbol
      trans = machine.get_trans_object(symb, state, dir)
      if trans.condition != Turing_Machine.RUNNING:
        return False, num_iters
      # Ex: (1|5)* A> 0 -> (1|5)* <B 2
      new_table[trans.state_out, trans.dir_out][not dir].update(table[state, dir][not dir])
      new_table[trans.state_out, trans.dir_out][not trans.dir_out].add(
        trans.symbol_out)
    # Make new_table complete by unioning it with table
    for x in table:
      for d in range(2):
        new_table[x][d].update(table[x][d])
    num_iters += 1
  return True, num_iters

class GenContainer:
  """Generic Container class"""
  def __init__(self, **args):
    for atr in args:
      self.__dict__[atr] = args[atr]

def test_CTL(base_tm, cutoff, block_size=1, offset=None, use_backsymbol=True, verbose=False):
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
    print(sim.tape.print_with_state(sim.state))
    print()
  tape = [None, None]
  for d in range(2):
    tape[d] = [block.symbol for block in reversed(sim.tape.tape[d]) if block.num != "Inf"]
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
