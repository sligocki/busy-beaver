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
enumerator.io = IO(None, file(output_fn, "ab"), None)
enumerator.continue_enum()

