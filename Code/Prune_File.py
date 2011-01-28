#! /usr/bin/env python
"""
Read two files - a reference file and a completed file - and output the
TTables in the reference file that were not in the completed file.
"""

import sys, IO

def map_to_undef(tm):
  for i, trans_list in enumerate(tm):
    for j, trans in enumerate(trans_list):
      if trans == (1, 1, -1):
        tm[i][j] = (-1, 0, -1)

if __name__ == "__main__":
  ref = open(sys.argv[1], "r")
  ref_IO = IO.IO(ref, sys.stdout)

  next = ref_IO.read_result()
  ref_list = []

  while next:
    ref_list.append(next)
    next = ref_IO.read_result()

  com = open(sys.argv[2], "r")
  com_IO = IO.IO(com, None)

  next = com_IO.read_result()
  com_list = []

  while next:
    map_to_undef(next[6])
    com_list.append(next)
    next = com_IO.read_result()

  com_found = [0] * len(com_list)

  for ref_item in ref_list:
    found = False
    for i, com_item in enumerate(com_list):
      if ref_item[6] == com_item[6]:
        com_found[i] += 1
        found = True
        break

    if not found:
      ref_IO.write_result_raw(ref_item[0], ref_item[1], ref_item[2], ref_item[3], ref_item[4], ref_item[5], ref_item[6], ref_item[7], ref_item[8])

  not_found  = com_found.count(0)
  found_once = com_found.count(1)
  found_more = len(com_found) - not_found - found_once

  sys.stderr.write("Not found: %d, Found once: %d, Found more: %d\n" % (not_found,found_once,found_more))
