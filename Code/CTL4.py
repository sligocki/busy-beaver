#! /usr/bin/env python3
#
# CTL4.py
#
"""
Runs the CTL (A* B C) on a machine to discover infinite behavior
"""

import sys
import argparse
import time

import IO
from Macro import Turing_Machine, Simulator
import globals

class CTL_Table(dict):
  def __getitem__(self, key):
    if key not in self:
      self[key] = ((set(), set(), set()), (set(), set(), set()))
    return dict.__getitem__(self, key)

def CTL(machine, config, verbose=False):
  """Runs the CTL on a machine given an advaced tape config"""
  # Initialize the table with the current configuration
  new_table = CTL_Table()
  new_table[config.state, config.dir] = config.init_sets
  # Iterate through the table completing it, until:
  #   1) It includes a halt (Failure)
  #   2) The table is unchanged after iteration (Success)
  table = None
  num_iters = 0

  while table != new_table:
    if not globals.time_remaining:
      print("--- CTL4 timeout ---")
      sys.stdout.flush()
      return False, num_iters

    if verbose:
      for term in new_table:
        print(term,":",new_table[term])
      print()
    table, new_table = new_table, CTL_Table()
    # For each entry in the old table, generate the possible outcomes and add
    # them to the new table
    for state, dir in table:
      # We could be looking at any of these symbols in A
      for symb in table[state, dir][dir][0]:
        cond, trans, steps = machine.get_transition(symb, state, dir)
        if cond[0] != Turing_Machine.RUNNING:
          return False, num_iters
        new_symb, new_state, new_dir = trans
        # Ex: (2) (3) (1|5)* A> 4 (1|4|5)* (1) (0)
        #  -> (2) (3) (1|5)* <B 2 (1|4|5)* (1) (0)
        # table[<B][0] = table[A>][0]; table[<B][1] = table[A>][1] + [2]
        for d in range(2):
          for s in range(3):
            new_table[new_state, new_dir][d][s].update(table[state, dir][d][s])
        new_table[new_state, new_dir][not new_dir][0].add(new_symb)
      # Or we could be looking at a symbol in B
      for symb in table[state, dir][dir][1]:
        cond, trans, steps = machine.get_transition(symb, state, dir)
        if cond[0] != Turing_Machine.RUNNING:
          return False, num_iters
        new_symb, new_state, new_dir = trans
        for s in range(3):
          new_table[new_state, new_dir][not dir][s].update(table[state, dir][not dir][s])
        if new_dir == dir:
          # Ex: (2) (3) (1|5)* A> (1) (4) -> (2) (3) (1|5)* 2 B> (4)
          new_table[new_state, new_dir][not new_dir][0].add(new_symb)
          new_table[new_state, new_dir][new_dir][1].update(
            table[state, dir][new_dir][2])
          new_table[new_state, new_dir][new_dir][2].add(machine.init_symbol)
        else: # new_dir != dir
          # Ex: (2) (3) (1|5)* A> (1) (4) -> (2) (3) (1|5)* <B 2 (4)
          new_table[new_state, new_dir][not new_dir][1].add(new_symb)
          new_table[new_state, new_dir][not new_dir][2].update(
            table[state, dir][not new_dir][2])
    # Make new_table complete by unioning it with table
    for x in table:
      for d in range(2):
        for s in range(3):
          new_table[x][d][s].update(table[x][d][s])
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
  sets = [None, None]
  for d in range(2):
    # Pass all symbols from this side of tape except for inf 0s
    # A is set of all symbols except the last two non-zeros
    A = set([block.symbol for block in sim.tape.tape[d][2:]])
    # The number of non-zero symbols not in A is at least 2
    # Set C to the last non-zero symbol
    # Set B to the second to last non-zero symbol
    # Add all other non-zero symbols to A
    if  len(sim.tape.tape[d]) >= 3 or \
       (len(sim.tape.tape[d]) == 2 and sim.tape.tape[d][1].num > 1):
      C = set([sim.tape.tape[d][1].symbol])
      if sim.tape.tape[d][1].num > 1:
        B = set([sim.tape.tape[d][1].symbol])
        if len(sim.tape.tape[d]) >= 3:
          A.add(sim.tape.tape[d][2].symbol)
        if sim.tape.tape[d][-2].num > 2:
          A.add(sim.tape.tape[d][1].symbol)
      else:
        B = set([sim.tape.tape[d][2].symbol])
        if sim.tape.tape[d][-3].num > 1:
          A.add(sim.tape.tape[d][2].symbol)
    # Only one non-zero symbols not in A
    # Set C to the zero symbol
    # Set B to the last non-zero symbol
    elif len(sim.tape.tape[d]) == 2:
      C = set([sim.tape.tape[d][0].symbol])
      B = set([sim.tape.tape[d][1].symbol])
    # No non-zero symbols not in A
    # Set B and C to the zero symbol
    else:
      C = set([sim.tape.tape[d][0].symbol])
      B = set([sim.tape.tape[d][0].symbol])
    sets[d] = (A, B, C)
  config = GenContainer(state=sim.state, dir=sim.dir, init_sets=tuple(sets))
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
