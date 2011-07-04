#! /usr/bin/env python
#
# Read_Profile.py
#
"""
Reads profiling information produced by:

    > python -m cProfile -o FILE PROGRAM

and prints a few useful bits of info.
"""

from optparse import OptionParser
import pstats

parser = OptionParser(usage="usage: %prog [options] filename [print-params ...]")
# What to sort by:
parser.add_option("--time", "--tottime",
                  action="store_const", const="time", dest="sort_by",
                  help="Sort by total time in function itself (not it's children). [Default]")
parser.add_option("--cumulative", "--cumtime",
                  action="store_const", const="cumulative", dest="sort_by",
                  help="Sort by cumulative time in function (including in it's children).")
parser.add_option("--calls", "--ncalls",
                  action="store_const", const="calls", dest="sort_by",
                  help="Sort by number of calls to function.")
# What to print by:
parser.add_option("--callers",
                  action="store_const", const="print_callers", dest="print_method",
                  help="Print callers of functions.")
parser.add_option("--callees",
                  action="store_const", const="print_callees", dest="print_method",
                  help="Print callees of functions.")
parser.set_defaults(sort_by="time", print_method="print_stats")
(options, args) = parser.parse_args()

if len(args) < 1:
  parser.error("Must have at least one argument, filename")
prof_file = args[0]

def smart_eval(arg):
  """If arg is text of an int, convert it to an int, otherwise, leave it a string."""
  try:
    return int(arg)
  except ValueError:
    return arg

print_args = map(smart_eval, args[1:])
if len(print_args) == 0:
  print_args = [20]

p = pstats.Stats(prof_file)
getattr(p.strip_dirs().sort_stats(options.sort_by), options.print_method)(*print_args)
# Ex: by default:
# p.strip_dirs().sort_stats("time").print_stats(20)
