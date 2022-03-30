#!/usr/bin/env python3
"""
Command line tool to print TM in different formats.
"""

import argparse
from pathlib import Path

import IO
from Macro import Turing_Machine


def ttable_to_markdown(ttable):
  """
  Write TM transition table to a Markdown table for use in, say, blog posts.
  
  Ex:
    |     |  0  |  1  |  2  |  3  |
    | :-: | :-: | :-: | :-: | :-: |
    |  A  | 1RB | 2LA | 1RA | 1RA |
    |  B  | 1LB | 1LA | 3RB | 1RZ |
  """
  
  num_states = len(ttable)
  num_symbols = len(ttable[0])

  result = ""

  # Column names
  result += "|     |"
  for symbol in range(num_symbols):
    result += "  %d  |" % symbol
  result += "\n"
  
  result += "| :-: " * (num_symbols + 1) + "|\n"

  # Transitions
  for state_in in range(num_states):
    # Row name
    result += "|  %c  |" % Turing_Machine.states[state_in]
    for symbol_in in range(num_symbols):
      (symbol_out, dir_out, state_out) = ttable[state_in][symbol_in]
      if symbol_out == -1:
        result += " --- |"  # Undefined transition
      else:
        result += " %c%c%c |" % (Turing_Machine.symbols[symbol_out],
                                 Turing_Machine.dirs[dir_out],
                                 Turing_Machine.states[state_out])
    result += "\n"

  return result

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm_file", type=Path)
  parser.add_argument("line_num", type=int, nargs="?", default=1)
  parser.add_argument("--format", choices = ["markdown"], default="markdown")  # TODO: text, HTML?
  args = parser.parse_args()
  
  ttable = IO.load_TTable_filename(args.tm_file, args.line_num)

  if args.format == "markdown":
    print(ttable_to_markdown(ttable))
  else:
    raise Exception("Unexpected value for --format: %s" % (args.format,))

if __name__ == "__main__":
  main()
