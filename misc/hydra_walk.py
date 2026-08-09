# Simulate Antihydra using algorithm like `hydra_map.py`.
# Adds random walk tracking.

import argparse
import os
import time

from gmpy2 import mpz, bit_mask
import psutil


# Direct computation of t steps of hydra map with random walk.
# Returns:
#   * hydra value H^t(n)
#   * final offset based upon random walk
#   * minimal offset (furthest left gone) during entire trip
def direct(n,t):
  offset = 0
  min_offset = 0
  for _ in range(t):
    if n % 2 == 0:
      offset -= 1
      min_offset = min(min_offset, offset)
    else:
      offset += 2
    n += n>>1
  return (n, offset, min_offset)

# Accelerated computation of 2**e steps of hydra
def accel_pow(n,e):
  if e<7: return direct(n,1<<e)
  t = 1<<(e-1)
  p3t = mpz(3)**t
  m = bit_mask(t)
  # First half
  n1, w1, mw1 = accel_pow(n&m,e-1)
  n1 += p3t*(n>>t)
  # Second half
  n2, w2, mw2 = accel_pow(n1&m,e-1)
  n2 += p3t*(n1>>t)
  return (n2, w1+w2, min(mw1, w1 + mw2))


def process_memory() -> int:
  """Return process memory in Bytes."""
  return psutil.Process(os.getpid()).memory_info().rss

def print_info(start_n, pow, n, w, mdw):
  print(f"H^{{{pow}}}({start_n:_}): {w=:_} {mdw=} ~2^{n.bit_length():_} ≡ {n % (1<<32)} (mod 2^32)  ({process_memory() // 10**6:_}MB {time.process_time():_.0f}s)")

def sim_forever(start_n: int, start_e: int = 20) -> None:
  e = start_e
  n, w, mdw = accel_pow(mpz(start_n), e)
  while True:
    print_info(start_n, f"2^{e:_}", n, w, mdw)
    n, dw, mdw = accel_pow(n, e)
    if w + mdw < 0:
      print("Halted!")
      return
    w += dw
    e += 1

def sim_verbose(start_n: int, num_steps: int) -> None:
  n = start_n
  w = 0
  for i in range(num_steps):
    print_info(start_n, f"{i:_}", n, w, None)
    n, dw, mdw = direct(n, 1)
    if w + mdw < 0:
      print("Halted!")
      return
    w += dw
  print_info(start_n, f"{num_steps:_}", n, w, None)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("start_value", type=int, nargs="?", default=3)
  parser.add_argument("verbose_steps", type=int, nargs="?")
  args = parser.parse_args()

  if args.verbose_steps:
    sim_verbose(args.start_value, args.verbose_steps)
  else:
    sim_forever(args.start_value)

main()
