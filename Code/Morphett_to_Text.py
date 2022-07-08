"""
Read TM format used on http://morphett.info/turing/turing.html and commonly
used in Googology posts.
"""

import argparse
from pathlib import Path

from Macro import Turing_Machine


class IO_Error(Exception): pass


def parse_dir(dir_str):
  if dir_str == "l":
    return Turing_Machine.LEFT
  elif dir_str == "r":
    return Turing_Machine.RIGHT
  else:
    raise IO_Error(dir_str)

def parse_symbol(symb_str):
  if symb_str == "_":
    return 0
  else:
    return int(symb_str)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("infile", type=Path)
  args = parser.parse_args()

  with open(args.infile, "r") as infile:
    # Load all transitions and map states to integers.
    state2index = {}
    transitions = []
    max_symbol = 0
    for line in infile:
      # Strip comments
      line = line.split(";")[0]
      # Strip !
      line = line.replace("!", "")
      line = line.strip()
      if line:
        trans = line.split()
        transitions.append(trans)
        assert len(trans) == 5, trans
        state_in, symbol_in = trans[:2]
        if state_in not in state2index:
          state2index[state_in] = len(state2index)
        max_symbol = max(max_symbol, parse_symbol(symbol_in))
    num_states = len(state2index)
    state2index["halt"] = -1
    num_symbols = max_symbol + 1

  # Build Transition Table.
  ttable = [[(-1, 0, -1)] * num_symbols  for _ in range(num_states)]
  for state_in, symbol_in, symbol_out, dir_out, state_out in transitions:
    ttable[state2index[state_in]][parse_symbol(symbol_in)] = (
      parse_symbol(symbol_out), parse_dir(dir_out), state2index[state_out])

  tm = Turing_Machine.Simple_Machine(ttable)
  print(tm.ttable_str())

if __name__ == "__main__":
  main()
