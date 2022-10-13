#! /usr/bin/env python3
"""
Given two text files. Split into 3 categories of the Venn Diagram:
 1) Common lines between both files (indersection).
 2) Lines only in left file (set diff 1).
 3) Lines only in right file (set diff 2).
"""

import argparse
from pathlib import Path


def venn_diff(in_left, in_right, out_inter, out_lonly, out_ronly):
  left_lines = set()
  for line in in_left:
    left_lines.add(line)

  left_only = left_lines
  left_all = frozenset(left_lines)
  for line in in_right:
    if line in left_all:
      # Line is in both left and right
      left_only.remove(line)
      out_inter.write(line)

    else:
      # Line is only in right
      out_ronly.write(line)

  for line in left_only:
    out_lonly.write(line)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("in_left", type=Path)
  parser.add_argument("in_right", type=Path)
  parser.add_argument("out_inter", type=Path)
  parser.add_argument("out_lonly", type=Path)
  parser.add_argument("out_ronly", type=Path)
  args = parser.parse_args()

  with open(args.in_left, "r") as in_left, \
       open(args.in_right, "r") as in_right, \
       open(args.out_inter, "w") as out_inter, \
       open(args.out_lonly, "w") as out_lonly, \
       open(args.out_ronly, "w") as out_ronly:
    venn_diff(in_left, in_right, out_inter, out_lonly, out_ronly)

if __name__ == "__main__":
  main()
