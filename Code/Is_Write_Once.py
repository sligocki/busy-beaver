"""
Filter TMs to only ones that are "write-once" meaning that they never modify a non-blank symbol.
"""

import argparse
from pathlib import Path
import sys

from Macro.Turing_Machine import RUNNING
from Macro.Turing_Machine import Simple_Machine as TM
import IO


def is_write_once(tm: TM):
  for state_in in tm.states:
    for symbol_in in tm.symbols:
      if symbol_in != tm.init_symbol:
        trans = tm.get_trans_object(symbol_in, state_in)
        if trans.condition == RUNNING and trans.symbol_out != symbol_in:
          return False
  return True


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("infile", type=Path)
  parser.add_argument("outfile", type=Path, nargs="?", default=sys.stdout)
  args = parser.parse_args()

  with IO.Writer(args.outfile) as writer:
    with IO.Reader(args.infile) as reader:
      for tm_record in reader:
        if is_write_once(tm_record.tm()):
          writer.write_record(tm_record)

if __name__ == "__main__":
  main()