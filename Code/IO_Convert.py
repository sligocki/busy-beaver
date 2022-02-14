#! /usr/bin/env python3
#
# IO_Convert.py
#
"""
Convert a data file from old format to new or vice-versa.
"""

from optparse import OptionParser

import IO
import IO_old

usage = "usage: %prog [options] infile outfile"
parser = OptionParser(usage=usage)
parser.add_option("--old2new", action="store_true", default=True,
                  help="Convert from old format to new. [Default]")
parser.add_option("--new2old", action="store_false", dest="old2new",
                  help="Convert from new format to old.")
(options, args) = parser.parse_args()

if len(args) != 2:
  parser.error("Must pass in exactly 2 arguments.")

infilename, outfilename = args

infile = open(infilename, "r")
outfile = open(outfilename, "w")

if options.old2new:
  in_io = IO_old.IO(infile, None)
  out_io = IO.IO(None, outfile)
else:
  in_io = IO.IO(infile, None)
  out_io = IO_old.IO(None, outfile)

result = in_io.read_result()
while result:
  out_io.write_result_raw(*result)
  result = in_io.read_result()
