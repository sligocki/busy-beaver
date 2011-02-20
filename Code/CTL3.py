#! /usr/bin/env python
#
# Runs the CTL (A B*) on a machine to discover infinite behavior

import IO
from Macro import Turing_Machine, Simulator

VERBOSE = False

class CTL_Table(dict):
  def __getitem__(self, key):
    if not self.has_key(key):
      self[key] = ((set(), set()), (set(), set()))
    return dict.__getitem__(self, key)

def CTL(machine, config):
  """Runs the CTL on a machine given an advaced tape config"""
  # Initialize the table with the current configuration
  new_table = CTL_Table()
  new_table[config.state, config.dir] = config.init_sets
  # Iterate through the table completing it, until:
  #   1) It includes a halt (Failure)
  #   2) The table is unchanged after iteration (Success)
  table = None
  while table != new_table:
    if VERBOSE:
      for term in new_table:
        print term,":",new_table[term]
      print
    table, new_table = new_table, CTL_Table()
    for state, dir in table:
      # We could be looking at any symbol in A
      for symb in table[state, dir][dir][0]:
        cond, trans, steps = machine.get_transition(symb, state, dir)
        if cond[0] != Turing_Machine.RUNNING:
          return False
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
  return True

class GenContainer:
  """Generic Container class"""
  def __init__(self, **args):
    for atr in args:
      self.__dict__[atr] = args[atr]

def test_CTL(ttable, cutoff, block_size=1, offset=None):
  m = Turing_Machine.Simple_Machine(ttable)
  if block_size != 1:
    m = Turing_Machine.Block_Macro_Machine(m, block_size, offset)
  m = Turing_Machine.Backsymbol_Macro_Machine(m)
  sim = Simulator.Simulator(m, enable_prover=False)
  sim.seek(cutoff)
  if sim.op_state != Turing_Machine.RUNNING:
    return False
  if VERBOSE:
    print sim.state, sim.tape
    print
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
  return CTL(m, config)

def test_from_file(filename, line, cutoff, block_size, offset):
  ttable = IO.load_TTable_filename(filename, line)
  if VERBOSE:
    for term in ttable:
      print term
    print
  if test_CTL(ttable, cutoff, block_size, offset):
    if VERBOSE:
      print "Success :)"
  else:
    if VERBOSE:
      print "Failure :("

# Main
if __name__ == "__main__":
  import sys
  try:
    filename = sys.argv[1]
    line = int(sys.argv[2])
    cutoff = int(sys.argv[3])
    block_size = int(sys.argv[4])
    offset = int(sys.argv[5])
  except:
    print "CTL3.py filename line_num cutoff block_size offset"
    sys.exit(1)
  VERBOSE = True
  test_from_file(filename, line, cutoff, block_size, offset)
