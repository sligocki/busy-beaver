#! /usr/bin/env python3
#
# Test_BSP.py
#
"""
Some communication timing tests for BSP from ScientificPython.
"""

import copy, sys, time, math, random, os, shutil, operator
import pickle as pickle

from Scientific.BSP import *

def print_value(value):
  print(value)

def print_blank():
  print()

# Command line interpretter code
if __name__ == "__main__":
  stime = time.time()

  global_print_value = ParRootFunction(print_value)
  global_print_blank = ParRootFunction(print_blank)

  range0000001 = list(range(0,   1))
  range0000010 = list(range(0,  10))
  range0000100 = list(range(0, 100))
  range0001000 = list(range(0,1000))

  range0010000 =   10*range0001000
  range0100000 =  100*range0001000
  range1000000 = 1000*range0001000

  count1 = 10000
  xcount1 = range(0,count1)

  count2 = 100
  xcount2 = range(0,count2)

  count3 = 100
  xcount3 = range(0,count3)

  t1 = time.time()
  for i in xcount1:
    temp = ParSequence(range0000001)
  t2 = time.time()
  global_print_value("Time 1s, 0000001: %20.13e" % (t2-t1))

  t1 = time.time()
  for i in xcount2:
    temp2 = temp.reduce(operator.add, [])
  t2 = time.time()
  global_print_value("Time 1g         : %20.13e" % (t2-t1))

  t1 = time.time()
  for i in xcount3:
    temp = ParRootSequence(temp2)
  t2 = time.time()
  global_print_value("Time 1s         : %20.13e" % (t2-t1))
  global_print_blank()

  t1 = time.time()
  for i in xcount1:
    temp = ParSequence(range0000010)
  t2 = time.time()
  global_print_value("Time 1s, 0000010: %20.13e" % (t2-t1))

  t1 = time.time()
  for i in xcount2:
    temp2 = temp.reduce(operator.add, [])
  t2 = time.time()
  global_print_value("Time 1g         : %20.13e" % (t2-t1))

  t1 = time.time()
  for i in xcount3:
    temp = ParRootSequence(temp2)
  t2 = time.time()
  global_print_value("Time 1s         : %20.13e" % (t2-t1))
  global_print_blank()

  t1 = time.time()
  for i in xcount1:
    temp = ParSequence(range0000100)
  t2 = time.time()
  global_print_value("Time 1s, 0000100: %20.13e" % (t2-t1))

  t1 = time.time()
  for i in xcount2:
    temp2 = temp.reduce(operator.add, [])
  t2 = time.time()
  global_print_value("Time 1g         : %20.13e" % (t2-t1))

  t1 = time.time()
  for i in xcount3:
    temp = ParRootSequence(temp2)
  t2 = time.time()
  global_print_value("Time 1s         : %20.13e" % (t2-t1))
  global_print_blank()

  t1 = time.time()
  for i in xcount1:
    temp = ParSequence(range0001000)
  t2 = time.time()
  global_print_value("Time 1s, 0001000: %20.13e" % (t2-t1))

  t1 = time.time()
  for i in xcount2:
    temp2 = temp.reduce(operator.add, [])
  t2 = time.time()
  global_print_value("Time 1g         : %20.13e" % (t2-t1))

  t1 = time.time()
  for i in xcount3:
    temp = ParRootSequence(temp2)
  t2 = time.time()
  global_print_value("Time 1s         : %20.13e" % (t2-t1))
  global_print_blank()

  t1 = time.time()
  for i in xcount1:
    temp = ParSequence(range0010000)
  t2 = time.time()
  global_print_value("Time 1s, 0010000: %20.13e" % (t2-t1))

  t1 = time.time()
  for i in xcount2:
    temp2 = temp.reduce(operator.add, [])
  t2 = time.time()
  global_print_value("Time 1g         : %20.13e" % (t2-t1))

  t1 = time.time()
  for i in xcount3:
    temp = ParRootSequence(temp2)
  t2 = time.time()
  global_print_value("Time 1s         : %20.13e" % (t2-t1))
  global_print_blank()

  t1 = time.time()
  for i in xcount1:
    temp = ParSequence(range0100000)
  t2 = time.time()
  global_print_value("Time 1s, 0100000: %20.13e" % (t2-t1))

  t1 = time.time()
  for i in xcount2:
    temp2 = temp.reduce(operator.add, [])
  t2 = time.time()
  global_print_value("Time 1g         : %20.13e" % (t2-t1))

  t1 = time.time()
  for i in xcount3:
    temp = ParRootSequence(temp2)
  t2 = time.time()
  global_print_value("Time 1s         : %20.13e" % (t2-t1))
  global_print_blank()

  t1 = time.time()
  for i in xcount1:
    temp = ParSequence(range1000000)
  t2 = time.time()
  global_print_value("Time 1s, 1000000: %20.13e" % (t2-t1))

  t1 = time.time()
  for i in xcount2:
    temp2 = temp.reduce(operator.add, [])
  t2 = time.time()
  global_print_value("Time 1g         : %20.13e" % (t2-t1))

  t1 = time.time()
  for i in xcount3:
    temp = ParRootSequence(temp2)
  t2 = time.time()
  global_print_value("Time 1s         : %20.13e" % (t2-t1))
  global_print_blank()

  t1 = time.time()
  for i in xcount1:
    temp = ParData(lambda pid, nProcs: range0000001)
  t2 = time.time()
  global_print_value("Time 2s, 0000001: %20.13e" % (t2-t1))

  if (numberOfProcessors * 1) < 10000000:
    t1 = time.time()
    for i in xcount2:
      temp2 = temp.reduce(operator.add, [])
    t2 = time.time()
    global_print_value("Time 2g         : %20.13e" % (t2-t1))

    t1 = time.time()
    for i in xcount3:
      temp = ParRootSequence(temp2)
    t2 = time.time()
    global_print_value("Time 2s         : %20.13e" % (t2-t1))
    global_print_blank()

  t1 = time.time()
  for i in xcount1:
    temp = ParData(lambda pid, nProcs: range0000010)
  t2 = time.time()
  global_print_value("Time 2s, 0000010: %20.13e" % (t2-t1))

  if (numberOfProcessors * 10) < 10000000:
    t1 = time.time()
    for i in xcount2:
      temp2 = temp.reduce(operator.add, [])
    t2 = time.time()
    global_print_value("Time 2g         : %20.13e" % (t2-t1))

    t1 = time.time()
    for i in xcount3:
      temp = ParRootSequence(temp2)
    t2 = time.time()
    global_print_value("Time 2s         : %20.13e" % (t2-t1))
    global_print_blank()

  t1 = time.time()
  for i in xcount1:
    temp = ParData(lambda pid, nProcs: range0000100)
  t2 = time.time()
  global_print_value("Time 2s, 0000100: %20.13e" % (t2-t1))

  if (numberOfProcessors * 100) < 10000000:
    t1 = time.time()
    for i in xcount2:
      temp2 = temp.reduce(operator.add, [])
    t2 = time.time()
    global_print_value("Time 2g         : %20.13e" % (t2-t1))

    t1 = time.time()
    for i in xcount3:
      temp = ParRootSequence(temp2)
    t2 = time.time()
    global_print_value("Time 2s         : %20.13e" % (t2-t1))
    global_print_blank()

  t1 = time.time()
  for i in xcount1:
    temp = ParData(lambda pid, nProcs: range0001000)
  t2 = time.time()
  global_print_value("Time 2s, 0001000: %20.13e" % (t2-t1))

  if (numberOfProcessors * 1000) < 10000000:
    t1 = time.time()
    for i in xcount2:
      temp2 = temp.reduce(operator.add, [])
    t2 = time.time()
    global_print_value("Time 2g         : %20.13e" % (t2-t1))

    t1 = time.time()
    for i in xcount3:
      temp = ParRootSequence(temp2)
    t2 = time.time()
    global_print_value("Time 2s         : %20.13e" % (t2-t1))
    global_print_blank()

  t1 = time.time()
  for i in xcount1:
    temp = ParData(lambda pid, nProcs: range0010000)
  t2 = time.time()
  global_print_value("Time 2s, 0010000: %20.13e" % (t2-t1))

  if (numberOfProcessors * 10000) < 10000000:
    t1 = time.time()
    for i in xcount2:
      temp2 = temp.reduce(operator.add, [])
    t2 = time.time()
    global_print_value("Time 2g         : %20.13e" % (t2-t1))

    t1 = time.time()
    for i in xcount3:
      temp = ParRootSequence(temp2)
    t2 = time.time()
    global_print_value("Time 2s         : %20.13e" % (t2-t1))
    global_print_blank()

  t1 = time.time()
  for i in xcount1:
    temp = ParData(lambda pid, nProcs: range0100000)
  t2 = time.time()
  global_print_value("Time 2s, 0100000: %20.13e" % (t2-t1))

  if (numberOfProcessors * 100000) < 10000000:
    t1 = time.time()
    for i in xcount2:
      temp2 = temp.reduce(operator.add, [])
    t2 = time.time()
    global_print_value("Time 2g         : %20.13e" % (t2-t1))

    t1 = time.time()
    for i in xcount3:
      temp = ParRootSequence(temp2)
    t2 = time.time()
    global_print_value("Time 2s         : %20.13e" % (t2-t1))
    global_print_blank()

  t1 = time.time()
  for i in xcount1:
    temp = ParData(lambda pid, nProcs: range1000000)
  t2 = time.time()
  global_print_value("Time 2s, 1000000: %20.13e" % (t2-t1))

  if (numberOfProcessors * 1000000) < 10000000:
    t1 = time.time()
    for i in xcount2:
      temp2 = temp.reduce(operator.add, [])
    t2 = time.time()
    global_print_value("Time 2g         : %20.13e" % (t2-t1))

    t1 = time.time()
    for i in xcount3:
      temp = ParRootSequence(temp2)
    t2 = time.time()
    global_print_value("Time 2s         : %20.13e" % (t2-t1))
    global_print_blank()

