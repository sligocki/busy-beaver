#! /usr/bin/env python
import sys, pickle
from Enumerate import *
from IO import IO

try:
  checkpoint_fn = sys.argv[1]
  output_fn = sys.argv[2]
except:
  print "Usage: Restart_Enumerate.py checkpoint_filename output_filename"
  sys.exit(1)

enumerator = pickle.load( file(checkpoint_fn, "r") )
outfile = file(output_fn, "ab")
enumerator.io = IO(None, outfile, None)

# TODO(shawn): Automatically clear duplicate machines?
outfile.write("\nRestarted - Some machines will be duplicated.\n")

enumerator.continue_enum()

