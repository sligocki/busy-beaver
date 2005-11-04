#! /usr/bin/env python
from BB_Format import FIELD, TEST

def count_lines(lines, field, test):
  count = 0
  for line in lines:
    fields = line.split()
    field_value = field.type(fields[field.num])
    if test(field_value):
      count += 1
  return count

def best_from_lines(lines, field, test):
  best_value = None
  for line in lines:
    fields = line.split()
    field_value = field.type(fields[field.num])
    if test(value=field_value, best_value=best_value):
      best_value = field_value
  return best_value
  
def filter_lines(lines, field, test):
  new_lines = []
  for line in lines:
    fields = line.split()
    field_value = field.type(fields[field.num])
    if test(field_value):
      new_lines.append(line)
  return new_lines


# Main Program
import getopt, sys

usage = "BB_Analyzer.py [--help] [--max=] [--number=] [--percentage=] data-filename"

# Get arguments
try:
  opts, args = getopt.getopt(sys.argv[1:], "",
                             ["help",
                              "max=",
                              "number=",
                              "percentage="])
except getopt.GetoptError:
  print usage
  sys.exit(1)

try:
  data_file = file(args[0], "r")
  lines_complete = [line for line in data_file]
except IndexError:
  print "No data file provided"
  print usage
  sys.exit(1)  
except IOError:
  print "No such file: '%s'" % args[0]
  print usage
  sys.exit(1)

if len(opts) == 0:
  opts = [("--max", "steps"), ("--max", "symbols"),
          ("--number", "total"), ("--number", "halt"),
          ("--number", "infinite"), ("--number", "unknown"),
          ("--percentage", "halt"), ("--percentage", "infinite"),
          ("--percentage", "unknown")]

for opt, arg in opts:
  lines = lines_complete

  if opt == "--help":
    print usage
    sys.exit(0)

  elif opt == "--max":
    if arg == "steps":
      field = FIELD.STEPS
    elif arg == "symbols":
      field = FIELD.SYMBOLS
    else:
      print "--max=%s invalid" % arg
      max_usage = "--max=[steps|symbols]"
      print max_usage
      sys.exit(1)
    lines = filter_lines(lines, FIELD.CONDITION, TEST.IS_HALT)
    print "Max %.11s\t= %d" % (arg, best_from_lines(lines, field, TEST.MAX))

  elif opt == "--number":
    if arg == "total":
      test = TEST.ALL
    elif arg == "halt":
      test = TEST.IS_HALT
    elif arg == "infinite":
      test = TEST.IS_INFINITE
    elif arg == "unknown":
      test = TEST.IS_UNKNOWN
    elif arg == "over_tape":
      test = TEST.IS_OVER_TAPE
    elif arg == "over_steps":
      test = TEST.IS_OVER_STEPS
    else:
      print "--number=%s invalid" % arg
      number_usage = "--number=[total|halt|infinite|unknown|over_tape|over_steps]"
      print number_usage
      sys.exit(1)
    print "Number %.8s\t= %d" % (arg, count_lines(lines, FIELD.CONDITION, test))

  elif opt == "--percentage":
    if arg == "halt":
      test = TEST.IS_HALT
    elif arg == "infinite":
      test = TEST.IS_INFINITE
    elif arg == "unknown":
      test = TEST.IS_UNKNOWN
    elif arg == "over_tape":
      test = TEST.IS_OVER_TAPE
    elif arg == "over_steps":
      test = TEST.IS_OVER_STEPS
    else:
      print "--percentage=%s invalid" % arg
      percentage_usage = "--percentage=[halt|infinite|unknown|over_tape|over_steps]"
      print percentage_usage
      sys.exit(1)
    percentage = float(count_lines(lines, FIELD.CONDITION, test)) / \
                 float(count_lines(lines, FIELD.CONDITION, TEST.ALL))
    print "Percent %.7s\t= %f" % (arg, percentage)
