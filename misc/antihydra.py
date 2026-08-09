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
      offset += 2
    else:
      offset -= 1
      min_offset = min(min_offset, offset)
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

def print_info(start_n, e, n, w, mdw):
  print(f"H^{{2^{e:_}}}({start_n:_}): {w=:_} {mdw=:_} ~2^{n.bit_length():_} ≡ {n % (1<<32)} (mod 2^32)  ({process_memory() // 10**6:_}MB {time.process_time():_.0f}s)")

def sim_forever(start_n: int, start_w: int, *, start_e: int = 20) -> None:
  w = start_w
  e = start_e - 1
  n, dw, mdw = accel_pow(mpz(start_n), e+1)
  while w + mdw >= 0:
    w += dw
    e += 1
    print_info(start_n, e, n, w, mdw)
    n, dw, mdw = accel_pow(n, e)
  print("Halted!")


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("start_value", type=int, nargs="?", default=8)
  parser.add_argument("start_offset", type=int, nargs="?", default=0,
                      help="Starting walk offset, Antihydra starts at 0.")
  args = parser.parse_args()

  sim_forever(args.start_value, args.start_offset)

main()
