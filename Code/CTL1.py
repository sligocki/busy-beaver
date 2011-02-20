#! /usr/bin/env python
#
# Runs the trivial CTL (A*) on a machine to discover infinite behavior

import IO
from Macro import Turing_Machine, Simulator

VERBOSE = False

class CTL_Table(dict):
  def __getitem__(self, key):
    if not self.has_key(key):
      self[key] = (set(), set())
    return dict.__getitem__(self, key)

def CTL(machine, config):
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
  while table != new_table:
    if VERBOSE:
      for term in new_table:
        print term,":",new_table[term]
      print
    table, new_table = new_table, CTL_Table()
    for state, dir in table:
      # We could be looking at any of these symbols
      for symb in table[state, dir][dir]:
        cond, trans, steps = machine.get_transition(symb, state, dir)
        if cond[0] != Turing_Machine.RUNNING:
          return False
        new_symb, new_state, new_dir = trans
        # Ex: (1|5)* A> 4 (1|4|5)* -> (1|5)* <B 2 (1|4|5)*
        # table[<B][0] = table[A>][0]; table[<B][1] = table[A>][1] + [2]
        for d in range(2):
          new_table[new_state, new_dir][d].update(table[state, dir][d])
        new_table[new_state, new_dir][not new_dir].add(new_symb)
      # Or we could be looking at blank (i.e. 00...)
      symb = machine.init_symbol
      cond, trans, steps = machine.get_transition(symb, state, dir)
      if cond[0] != Turing_Machine.RUNNING:
        return False
      new_symb, new_state, new_dir = trans
      # Ex: (1|5)* A> 0 -> (1|5)* <B 2 
      new_table[new_state, new_dir][not dir].update(table[state, dir][not dir])
      new_table[new_state, new_dir][not new_dir].add(new_symb)
    # Make new_table complete by unioning it with table
    for x in table:
      for d in range(2):
        new_table[x][d].update(table[x][d])
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
  tape = [None, None]
  for d in range(2):
    tape[d] = [block.symbol for block in reversed(sim.tape.tape[d]) if block.num != "Inf"]
  config = GenContainer(state=sim.state, dir=sim.dir, tape=tape)
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
    print "CTL1.py filename line_num cutoff block_size offset"
    sys.exit(1)
  VERBOSE = True
  test_from_file(filename, line, cutoff, block_size, offset)
