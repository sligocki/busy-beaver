#!/usr/bin/env python3
"""
Command line tool to print TM in different formats.
"""

import argparse
from pathlib import Path

import IO
from Macro import Turing_Machine


def tm_to_markdown(tm : Turing_Machine.Simple_Machine) -> str:
  """
  Write TM transition table to a Markdown table for use in, say, blog posts.

  Ex:
    |     |  0  |  1  |  2  |  3  |
    | :-: | :-: | :-: | :-: | :-: |
    |  A  | 1RB | 2LA | 1RA | 1RA |
    |  B  | 1LB | 1LA | 3RB | 1RZ |
  """

  result = ""

  # Column names
  result += "|     |"
  for symbol in range(tm.num_symbols):
    result += "  %d  |" % symbol
  result += "\n"

  result += "| :-: " * (tm.num_symbols + 1) + "|\n"

  # Transitions
  for state_in in range(tm.num_states):
    # Row name
    result += "|  %c  |" % Turing_Machine.STATES[state_in]
    for symbol_in in range(tm.num_symbols):
      trans = tm.get_trans_object(state_in = state_in, symbol_in = symbol_in)
      if trans.condition == Turing_Machine.UNDEFINED:
        result += " --- |"  # Undefined transition
      else:
        result += " %c%c%c |" % (Turing_Machine.SYMBOLS[trans.symbol_out],
                                 Turing_Machine.DIRS[trans.dir_out],
                                 Turing_Machine.STATES[trans.state_out])
    result += "\n"

  return result

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm_file", type=Path)
  parser.add_argument("record_num", type=int, nargs="?", default=0)
  parser.add_argument("--format", choices = ["markdown"], default="markdown")  # TODO: text, HTML?
  args = parser.parse_args()

  tm = IO.load_tm(args.tm_file, args.record_num)

  if args.format == "markdown":
    print(tm_to_markdown(tm))
  else:
    raise Exception("Unexpected value for --format: %s" % (args.format,))

if __name__ == "__main__":
  main()
