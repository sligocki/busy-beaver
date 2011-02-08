#! /usr/bin/env python
#
# Count the number of distinct TM represented by machines in tree-normal-form
# With the restriction that A0->1RB and Halt=1RH.
#
# Note that for the space of Q-state, S-symbol TMs, there are
#   (QS-1) * (2QS)^(QS-2) with such restrictions. Thus, if we run this count
#   over a completed TNF set of machines, we should get this value.
#

def fact2(n, m=0):
  """Computes n!/m! = n*(n-1)*...*(m+1)"""
  assert n >= m >= 0
  if n == m:
    return 1
  else:
    return n*fact2(n-1, m)

def count(ttable):
  """Count the number of TM's that are equivolent to this one.
     With the restriction that A0->1RB and Halt=1RH."""
  undefs = 0
  has_halt = False
  max_symbol = 0
  max_state = 0
  num_states = len(ttable)
  num_symbols = len(ttable[0])
  # Get stats.  Number of undefined transitions, whether there is a halt and the max-symbol/states
  for state_in in range(num_states):
    for symbol_in in range(num_symbols):
      symbol, dir, state = ttable[state_in][symbol_in]
      if symbol == -1:
        undefs += 1
      elif state == -1:
        has_halt = True
      else:
        max_symbol = max(max_symbol, symbol)
        max_state = max(max_state, state)
  symbols_used = max_symbol + 1
  states_used = max_state + 1
  # Count the number of permutations of symbols/states possible
  result = fact2(num_symbols - 2, num_symbols - symbols_used) \
         * fact2(num_states - 2, num_states - states_used)
  if has_halt:
    result *= (2*num_states*num_symbols)**undefs
  else:
    result *= undefs * (2*num_states*num_symbols)**(undefs - 1)
  return result

#main prog
import sys

import IO

def count_all(filename):
  """Count total number of machines represented in a file."""
  if filename == "-":
    infile = sys.stdin
  else:
    infile = open(filename, "r")
  io = IO.IO(infile, None)

  total = 0
  for result in io:
    n = count(result.ttable)
    #print n, total
    total += n

  infile.close()
  return total

if __name__ == "__main__":
  total = 0
  for filename in sys.argv[1:]:
    subtotal = count_all(filename)
    print "", filename, subtotal
    sys.stdout.flush()
    total += subtotal
  print "Total", total
  # TODO(shawn): Print out the (QS-1) * ...
  #print "Expected %dx%d: %d" % (
