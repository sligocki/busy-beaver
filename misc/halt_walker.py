# General framework for fast simulation of halting random walkers
# like many BBf or MBB unbiased random walker.
#
# This supports mappings with:
#   * One Constant Collatz parameter (h)
#   * One Walk param (w)
# which halt iff w < 0

from abc import ABC, abstractmethod
import argparse
import itertools
import os
import time

import psutil
from gmpy2 import mpz


def process_memory() -> int:
  """Return process memory in Bytes."""
  return psutil.Process(os.getpid()).memory_info().rss


class Halt(Exception):
  pass


def print_info(i, start_h, w, max_w, h, t=0):
  mod = 3**32
  if h < mod:
    h_str = f"{h:_}"
  else:
    h_str = f"~2^{h.bit_length():_} ≡ {h % mod} (mod 3^32)"

  if t:
    t_str = f"t≈2^{t.bit_length():_}"
  else:
    t_str = ""

  print(
    f"  f^{{{i:_}}}({start_h:_}): w={w:_} max_w={max_w:_} h = {h_str} {t_str}  "
    f"({process_memory() // 10**6:_}MB {time.process_time():_.0f}s)"
  )


class Sim(ABC):
  # Subclasses must define:
  #   mod_in: mpz
  #   mod_out: mpz
  #   init_runtime: mpz

  @abstractmethod
  def sim_step(self, h: mpz, w: int) -> tuple[mpz, int, mpz]:
    """Single simulation step: one application of high level function.
    Must be implement by subclass.
    Returns (new_h, new_w, delta_time)
    """

  def __init__(self, start_h: mpz, start_w: int):
    self.start_h = start_h
    self.h = start_h
    self.w = start_w
    self.max_w = start_w
    self.num_sim_steps = 0
    self.runtime = self.init_runtime
    self.is_halted = False

  def direct(self, h: mpz, w: int, num_sim_steps: int):
    """Directly simulate num_sim_steps sim_steps."""
    min_w = 0
    max_w = 0
    time = 0
    for _ in range(num_sim_steps):
      h, w, dt = self.sim_step(h, w)
      time += dt
      min_w = min(min_w, w)
      max_w = max(max_w, w)
    return (h, w, time, min_w, max_w)

  def accel_pow(self, h: mpz, w: int, e: int):
    """Accelerated sim of 2**e sim_steps. Uses divide-and-conquer."""
    if e <= 6:
      return self.direct(h, w, 2**e)
    x = 1 << (e - 1)
    p3t = self.mod_in**x
    p4t = self.mod_out**x
    # First half
    k, r = divmod(h, p3t)
    h1, w1, t1, lw1, hw1 = self.accel_pow(r, w, e - 1)
    h1 += p4t * k
    # Second half
    k1, r1 = divmod(h1, p3t)
    h2, w2, t2, lw2, hw2 = self.accel_pow(r1, w1, e - 1)
    h2 += p4t * k1
    return (h2, w2, t1 + t2, min(lw1, lw2), max(hw1, hw2))

  def try_run_pow(self, e: int) -> bool:
    """Attempt to run for 2^e sim_steps.
    If it ever moved walk < 0, do nothing and return False.
    Otherwise, apply sim_steps and return True.
    """
    h, w, t, lw, hw = self.accel_pow(self.h, self.w, e)

    if w < 0:
      # Went negative while running. Don't apply
      return False
    else:
      # Apply sim_steps
      self.h = h
      self.w = w
      self.max_w = max(self.max_w, hw)
      self.num_sim_steps += 2**e
      self.runtime += t
      return True

  def sim_forever(self, start_e: int = 0):
    """Simulate until halt (or memory failure)"""
    print("Exponential increase:")
    self.print_info()
    self.try_run_pow(start_e)
    self.print_info()
    # Start by exponentially increasing sim_step run
    for e in itertools.count(start_e):
      if self.try_run_pow(e):
        self.print_info()
      else:
        # Halted
        break

    # Once it halts, use binary search to find exact halting step
    print("Halt detected. Binary searching exact halt steps:")
    for e in range(e - 1, -1, -1):
      if self.try_run_pow(e):
        self.print_info()
    self.h, self.w, _ = self.sim_step(self.h, self.w)
    self.num_sim_steps += 1
    self.print_info()
    assert self.w == -1

    print(f"Halted after exactly {self.num_sim_steps:_} iterations")

  def sim_direct(self):
    h, w = self.h, self.w
    i = 0
    next_i = 1
    max_w = w
    t = 0
    while w >= 0:
      h, w, dt = self.sim_step(h, w)
      max_w = max(max_w, w)
      i += 1
      t += dt
      if i == next_i:
        print_info(i, self.start_h, w, max_w, h, t)
        next_i *= 2
    print("Halted")
    print_info(i, self.start_h, w, max_w, h, t)

  def print_info(self) -> None:
    print_info(self.num_sim_steps, self.start_h, self.w, self.max_w, self.h)


# Simulate MBB Cryptid: 0-BG_0-CF_0-DJ_1+E_1+A_2+J_2-H*_1-IE_0+J_0+H start @ state F
#   https://wiki.bbchallenge.org/wiki/Register_machine
#
# Let A(h, w) = E:[h, 0, w]
#
# A(3k, w+1) --(11k+7)--> A(4k+2, w)
# A(3k,   0) --( 5k+3)--> Halt(2k+1)
# A(3k+1, w) --(11k+9)--> A(4k+3, w+1)
# A(3k+2, w) --(11k+9)--> A(4k+3, w)
#
# Start: A(1, 1) @3
#
# f(3k)   = 4k+2
# f(3k+1) = 4k+3
# f(3k+2) = 4k+3
class MBB1(Sim):
  mod_in = mpz(3)
  mod_out = mpz(4)
  init_runtime = 3

  def sim_step(self, h: mpz, w: int) -> tuple[mpz, int, mpz]:
    k, r = divmod(h, 3)
    if r == 0:
      if w == 0:
        return (True, 5 * k + 3, 2 * k + 1)
      else:
        return (4 * k + 2, w - 1, 11 * k + 7)
    elif r == 1:
      return (4 * k + 3, w + 1, 11 * k + 9)
    else:
      return (4 * k + 3, w, 11 * k + 9)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("start_value", type=int, nargs="?", default=8)
  parser.add_argument(
    "start_offset",
    type=int,
    nargs="?",
    default=0,
    help="Starting walk offset, Antihydra starts at 0.",
  )
  args = parser.parse_args()

  sim = MBB1(args.start_value, args.start_offset)
  sim.sim_forever()
  # print()
  # sim_direct(args.start_value, args.start_offset)


main()
