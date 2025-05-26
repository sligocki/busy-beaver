#! /usr/bin/env python3
#
# CTL3.py
#
"""
Runs the CTL (A B*) on a machine to discover infinite behavior
"""

import sys
import argparse
import time

import IO
from Macro import Turing_Machine, Simulator

class CTL_Table(dict):
  def __getitem__(self, key):
    if key not in self:
      self[key] = ((set(), set()), (set(), set()))
    return dict.__getitem__(self, key)

def CTL(machine, config, max_time=0.0, verbose=False):
  """Runs the CTL on a machine given an advaced tape config"""
  # Initialize the table with the current configuration
  new_table = CTL_Table()
  new_table[config.state, config.dir] = config.init_sets
  # Iterate through the table completing it, until:
  #   1) It includes a halt (Failure)
  #   2) The table is unchanged after iteration (Success)
  table = None
  num_iters = 0
  end_time = None
  if max_time > 0:
    end_time = time.time() + max_time

  while table != new_table:
    if end_time and time.time() >= end_time:
      return False, num_iters

    if verbose:
      for term in new_table:
        print(term,":",new_table[term])
      print()
    table, new_table = new_table, CTL_Table()
    for state, dir in table:
      # We could be looking at any symbol in A
      for symb in table[state, dir][dir][0]:
        cond, trans, steps = machine.get_transition(symb, state, dir)
        if cond[0] != Turing_Machine.RUNNING:
          return False, num_iters
        new_symb, new_state, new_dir = trans

        new_sets = new_table[new_state, new_dir]
        old_sets = table[state, dir]
        if new_dir != dir:
          # Ex: D* C A> 4 B* -> D* C <B 2 B*
          new_sets[new_dir][0].update(old_sets[new_dir][0])
          new_sets[new_dir][1].update(old_sets[new_dir][1])
          new_sets[not new_dir][0].add(new_symb)
          new_sets[not new_dir][1].update(old_sets[not new_dir][1])
        else: # new_dir == dir:
          # Ex: D* C A> 4 B* -> (D|C)* 2 B> (B|0) B*
          new_sets[new_dir][0].update(old_sets[new_dir][1])
          new_sets[new_dir][0].add(machine.init_symbol)
          new_sets[new_dir][1].update(old_sets[new_dir][1])
          new_sets[not new_dir][0].add(new_symb)
          new_sets[not new_dir][1].update(old_sets[not new_dir][0])
          new_sets[not new_dir][1].update(old_sets[not new_dir][1])
    # Make new_table complete by unioning it with table
    for x in table:
      for d in range(2):
        for s in range(2):
          new_table[x][d][s].update(table[x][d][s])
  return True, num_iters

class GenContainer:
  """Generic Container class"""
  def __init__(self, **args):
    for atr in args:
      self.__dict__[atr] = args[atr]

def test_CTL(base_tm, cutoff, block_size=1, offset=None, use_backsymbol=True,
             max_time=0.0, verbose=False):
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
  sets = [None, None]
  for d in range(2):
    # Pass all symbols from this side of tape except for inf 0s
    # A is the first symbol
    A = set([sim.tape.tape[d][-1].symbol])
    # B is set of all other symbols before inf 0s
    B = set([block.symbol for block in reversed(sim.tape.tape[d][1:-1])])
    if sim.tape.tape[d][-1].num >= 2 and sim.tape.tape[d][-1] != "Inf":
      B.add(sim.tape.tape[d][-1].symbol)
    sets[d] = (A, B)
  config = GenContainer(state=sim.state, dir=sim.dir, init_sets=tuple(sets))
  return CTL(m, config, max_time=max_time, verbose=verbose)


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
