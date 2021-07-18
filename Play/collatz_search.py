"""
Enumerate Collatz-like functions and search for long orbits.
"""

import argparse
import itertools
from pprint import pprint


def orbit_length(col_func, start_val):
  vals = set()
  val = start_val
  for n in itertools.count(1):
    vals.add(val)
    val = col_func(val)
    # If orbit finishes.
    if val is None:
      return n
    # If orbit cycles.
    if val in vals:
      return None
  # Note: This will never end if orbit diverges!

def find_long_orbits(col_func, start_range):
  orbits = [(length, val) for val in start_range
            if (length := orbit_length(col_func, val)) is not None]
  return sorted(orbits, reverse=True)

def enum_cartesian_power(val_range, val_count):
  if val_count == 0:
    yield []
  else:
    for sub in enum_cartesian_power(val_range, val_count - 1):
      for val in val_range:
        yield sub + [val]

def enum_cartesian(a_list, b_enum):
  for b in b_enum:
    for a in a_list:
      yield [a] + b

class CollatzFunction:
  def __init__(self, in_mod, out_mod, remainders):
    assert len(remainders) == in_mod, (in_mod, remainders)
    self.in_mod = in_mod
    self.out_mod = out_mod
    self.remainders = remainders
    
  def __call__(self, val):
    k, r = divmod(val, self.in_mod)
    if self.remainders[r] is None:
      return None
    else:
      return self.out_mod * k + self.remainders[r]
    
  def __repr__(self):
    return f"CollatzFunction({self.in_mod}, {self.out_mod}, {self.remainders})"

def search_collatz(in_mod, out_mod, max_remainder_diff, start_range):
  orbits = []
  # We search for Collatz functions in "Normal Form". Specifically,
  #  * Require undefined transition to be the last one.
  #  * Require first remainder to be in range 0..(out_mod - in_mod).
  for remainder0 in range(out_mod - in_mod):
    remainder_range = list(range(remainder0 - max_remainder_diff,
                                 remainder0 + max_remainder_diff + 1))
    for rest in enum_cartesian_power(remainder_range, in_mod - 2):
      col_func = CollatzFunction(in_mod, out_mod, [remainder0] + rest + [None])
      orbits += [(orbit_len, start_val, col_func)
                 for (orbit_len, start_val) in find_long_orbits(col_func, start_range)]
  return sorted(orbits, key=(lambda x: (-x[0], abs(x[1]))))[:40]

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("in_mod", type=int)
  parser.add_argument("out_mod", type=int)
  parser.add_argument("--max-remainder-diff", type=int, default=10)
  parser.add_argument("--max-start-val", type=int, default=20)
  args = parser.parse_args()

  start_range = list(range(-args.max_start_val, args.max_start_val + 1))
  pprint(search_collatz(args.in_mod, args.out_mod, args.max_remainder_diff, start_range))

if __name__ == "__main__":
  main()
