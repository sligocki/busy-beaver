# Enumerate all constant collatz (mod_in -> mod_out) trajectories and sort by longest stopping time.

import argparse
from dataclasses import dataclass
import itertools
import math


class SimOversteps(Exception):
  """Simulation did not complete by max steps"""


@dataclass
class ConstCollatz:
  mod_in: int
  mod_out: int
  bs: list[int | None]

  def __str__(self):
    parts = [f"f({self.mod_in}k+{r})={self.mod_out}k{b:+}" for (r, b) in enumerate(self.bs) if b is not None]
    return ", ".join(parts)

  def step(self, val: int) -> int | None:
    k, r = divmod(val, self.mod_in)
    b = self.bs[r]
    if b is None:
      return None
    return self.mod_out * k + b

  def run(self, start: int, max_steps: int) -> int | None:
    """Return stopping time if it stops. Return None if it cycles. Raise Exception if neither."""
    val = start
    seen = {val}
    for n in range(max_steps):
      val = self.step(val)
      if val is None:
        # Halted after n steps
        return n
      if val in seen:
        # Cycle detected
        return None
      seen.add(val)
    # Never halted after max_steps steps
    raise SimOversteps(self, start, val)

  def seq(self, start: int) -> list[int]:
    val = start
    ret = []
    while val is not None:
      ret.append(val)
      val = self.step(val)
    return ret

  def num_lanes(self) -> int:
    cs = [self.mod_in * b - self.mod_out * r for r, b in enumerate(self.bs) if b is not None]
    dcs = [x - y for x, y in zip(cs[:-1], cs[1:])]
    return abs(math.gcd(*dcs))

  def lanes(self) -> list[int]:
    n = self.num_lanes()
    lanes = [-1 for r in range(n)]
    for r_in in range(n):
      x = r_in
      # Figure out f(nk + r) % n
      # It must be constant across each lane
      while (r_out := self.step(x)) is None:
        # Only inconsistency can be if f halts on a given value
        # But it can't halt on all
        x += n
      lanes[r_in] = r_out % n
    return lanes

  def lane_seq(self, start: int) -> list[int]:
    lanes = self.lanes()
    n = len(lanes)
    seq = [start % n]
    while (r := lanes[seq[-1]]) not in seq:
      seq.append(r)
    seq.append(r)
    return seq


def gen_tuples(length: int, target_sum: int):
  if length == 0:
    if target_sum == 0:
      yield ()
    return
  for abs_val in range(target_sum + 1):
    if abs_val == 0:
      for rest in gen_tuples(length - 1, target_sum):
        yield (0,) + rest
    else:
      for rest in gen_tuples(length - 1, target_sum - abs_val):
        yield (abs_val,) + rest
        yield (-abs_val,) + rest


def enum_trajectories_by_size(max_size: int):
  for size in range(2, max_size + 1):
    for mod_in in range(1, size):
      for mod_out in range(mod_in + 1, size - mod_in + 1):
        rem_size = size - mod_in - mod_out
        for abs_start in range(rem_size + 1):
          starts = [0] if abs_start == 0 else [abs_start, -abs_start]
          target_sum_b = rem_size - abs_start
          for none_pos in range(mod_in):
            for b_tuple in gen_tuples(mod_in - 1, target_sum_b):
              bs = list(b_tuple)
              bs.insert(none_pos, None)
              f = ConstCollatz(mod_in, mod_out, bs)
              for start in starts:
                yield size, f, start


def search_by_size(max_size: int, max_steps: int):
  best_for_size = {}
  for size, f, start in enum_trajectories_by_size(max_size):
    try:
      stopping_time = f.run(start, max_steps)
    except SimOversteps:
      continue
    if stopping_time is not None:
      if size not in best_for_size or stopping_time > best_for_size[size][0]:
        best_for_size[size] = (stopping_time, f, start)

  for size in sorted(best_for_size.keys()):
    st, f, st_val = best_for_size[size]
    print(f"Size {size:2d}: max steps {st:4d}  start {st_val:4d}  {f}")


def enum_maps(mod_in: int, mod_out: int, max_b: int):
  # Translation normalize so that:
  #   1. undefined transition is first
  #   2. b_1 in [2, |mod_out-mod_in|+2)
  assert mod_in >= 2
  assert mod_out != mod_in

  b1_range = range(2, abs(mod_out - mod_in) + 2)
  other_b_range = range(0, max_b + 1)

  for b1 in b1_range:
    for other_bs in itertools.product(other_b_range, repeat=mod_in - 2):
      yield ConstCollatz(mod_in, mod_out, [None, b1] + list(other_bs))


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("mod_in", type=int, nargs="?")
  parser.add_argument("mod_out", type=int, nargs="?")

  parser.add_argument("--max-b", type=int, default=20)
  parser.add_argument("--max-start", type=int, default=20)
  parser.add_argument("--max-steps", type=int, default=1000)
  parser.add_argument(
    "--by-size", type=int, help="Enumerate up to this max size and list longest stopping time for each size."
  )
  args = parser.parse_args()

  if args.by_size is not None:
    search_by_size(args.by_size, args.max_steps)
    return

  if args.mod_in is None or args.mod_out is None:
    parser.error("mod_in and mod_out are required unless --by-size is provided")

  results = []
  for f in enum_maps(args.mod_in, args.mod_out, args.max_b):
    for start in range(args.max_start + 1):
      stopping_time = f.run(start, args.max_steps)
      if stopping_time:
        results.append((f, start, stopping_time))

  # Sort first by stopping_time (desc) then by start (asc)
  results.sort(key=lambda x: (-x[2], x[0].num_lanes(), x[1]))
  for f, start, stopping_time in results[:20]:
    print(f"{stopping_time:4d}  {start:4d}  {f.num_lanes():4d}  {f}  {f.lane_seq(start)}")


main()
