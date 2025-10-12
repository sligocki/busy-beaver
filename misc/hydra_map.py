# Fast simulation of iterated hydra map. Almost linear runtime.
# This is addapted from an example shared by Greg Kuperberg.

import argparse
from functools import lru_cache
import hashlib
import os
import time

from gmpy2 import mpz, bit_mask, log2, floor
import psutil


# Direct computation of t steps of hydra
def direct(n,t):
  for _ in range(t): n += n>>1
  return n

@lru_cache
def pow_mem(b, p) -> mpz:
  return mpz(b)**p

# Accelerated computation of 2**e steps of hydra
def accel_pow(n,e):
  if e<8: return direct(n,1<<e)
  t = 1<<(e-1)
  p3t = pow_mem(3, t)
  m = bit_mask(t)
  n = p3t*(n>>t) + accel_pow(n&m,e-1)
  return p3t*(n>>t) + accel_pow(n&m,e-1)

def hydra(n,t):
  """H^t(n)"""
  n = mpz(n)
  while t > 0:
    e = int(floor(log2(t)))
    n = accel_pow(n, e)
    t -= 2**e
  return n


def process_memory() -> int:
  """Return process memory in Bytes."""
  return psutil.Process(os.getpid()).memory_info().rss

def shahash(n: mpz) -> str:
  hasher = hashlib.sha256()
  num_bytes = (n.bit_length() + 7)//8
  hasher.update(n.to_bytes(num_bytes))
  return hasher.hexdigest()

def print_info(n, t, res):
  # print(f"H^{t:_}({n:_}): ~2^{res.bit_length():_} ≡ {res % (1<<128)} (mod 2^128) hash: {shahash(res)}  ({time.process_time():_.0f}s)")
  print(f"H^{t:_}({n:_}): ~2^{res.bit_length():_} ≡ {res % (1<<128)} (mod 2^128)  ({process_memory() // 10**6:_}MB {time.process_time():_.0f}s)")

def sim_forever(start_n: int, start_e: int = 20) -> None:
  e = start_e
  n = accel_pow(mpz(start_n), e)
  while True:
    print_info(start_n, 1<<e, n)
    n = accel_pow(n, e)
    e += 1


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("start_value", type=int)
  parser.add_argument("num_iters", type=int, nargs="?")
  args = parser.parse_args()

  if args.num_iters:
    res = hydra(args.start_value, args.num_iters)
    print_info(args.start_value, args.num_iters, res)
  else:
    sim_forever(args.start_value)

main()
