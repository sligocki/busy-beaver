#!/usr/bin/env python3
"""
Randomly shuffle lines from a file and split them out into N new files.
"""

import argparse
import random


parser = argparse.ArgumentParser()
parser.add_argument("infile")
parser.add_argument("num_chunks", type=int)
args = parser.parse_args()

# NOTE: This reads all lines into memory and then shuffles them, so is only
# a good idea for a small-ish file. For larger files, a more clever algorithm
# would be needed.
with open(args.infile, "r") as infile:
  lines = infile.readlines()
random.shuffle(lines)

lines_per_chunk = len(lines) / args.num_chunks
chunk_breaks = [round(lines_per_chunk * chunk_num) for chunk_num in range(args.num_chunks + 1)]
for chunk_num in range(args.num_chunks):
  outfilename = f"{args.infile}.part_{chunk_num}_of_{args.num_chunks}"
  with open(outfilename, "w") as outfile:
    outfile.writelines(lines[chunk_breaks[chunk_num] : chunk_breaks[chunk_num + 1]])
