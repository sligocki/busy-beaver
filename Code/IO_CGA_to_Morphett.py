"""
One-off parser for TMs listed in:
  https://gist.github.com/anonymous/a64213f391339236c2fe31f8749a0df6
"""

import argparse
from pathlib import Path

import IO
from IO import TM_Record
from Macro import Turing_Machine
import TM_Enum


DIRS = "LR"
def parse_tm(text : str) -> Turing_Machine.Simple_Machine:
  rows = []
  for line in text.split("\n"):
    line = line.split("#")[0].strip()
    parts = line.split()
    if parts:
      assert len(parts) == 7, line
      rows.append(parts)
  states = [row[0] for row in rows]
  symbols = [0, 1]

  def parse_trans(symb, dir, state):
    if symb == "-":
      assert dir == "-" and state == "-", (symb, dir, state)
      return (None, None, None)

    elif symb == "H":
      assert dir == "H" and state == "H", (symb, dir, state)
      return (1, 1, -1)  # 1RH

    else:
      symb = int(symb)
      assert symb in symbols, (symb, dir, state)
      dir = DIRS.find(dir)
      assert state in states, (symb, dir, state)
      return (symb, dir, state)

  quints = []
  for (state_in, sy0, d0, st0, sy1, d1, st1) in rows:
    quints.append((state_in, 0, *parse_trans(sy0, d0, st0)))
    quints.append((state_in, 1, *parse_trans(sy1, d1, st1)))
  return Turing_Machine.tm_from_quintuples(quints, states, symbols)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("infile", type=Path)
  parser.add_argument("outfile", type=Path)
  args = parser.parse_args()

  with open(args.infile, "r") as f:
    tm = parse_tm(f.read())

  with IO.Morphett.Writer(args.outfile) as writer:
    tm_enum = TM_Enum.TM_Enum(tm, allow_no_halt = False)
    tm_record = TM_Record.TM_Record(tm_enum = tm_enum)
    writer.write_record(tm_record)

main()
