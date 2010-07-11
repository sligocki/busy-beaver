#! /usr/bin/env python

"""
Reads profiling information produced by:
> python -m cProfile -o FILE PROGRAM
and prints a few useful bits of info.
"""

import pstats
import sys

if len(sys.argv) != 2:
  print >>sys.stderr, "usage: Read_Profile.py filename"
  sys.exit(1)

prof_file = sys.argv[1]

p = pstats.Stats(prof_file)
p.strip_dirs().sort_stats("time").print_stats(10)
p.strip_dirs().sort_stats("cumulative").print_stats(10)