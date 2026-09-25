# General framework for fast simulation of halting random walkers
# like many BBf or MBB unbiased random walker.
#
# This supports mappings with:
#   * One Constant Collatz parameter (h)
#   * One Walk param (w)
# which halt iff w < 0

from __future__ import annotations

from abc import ABC, abstractmethod
import argparse
from dataclasses import dataclass, replace
import os
import time

import psutil
from gmpy2 import mpz


def process_memory() -> int:
  """Return process memory in Bytes."""
  return psutil.Process(os.getpid()).memory_info().rss


def approx_str(n: int | None) -> str:
  if n is None:
    return ""
  if n < 10**10:
    return f"={n:_}"
  else:
    return f"≈2^{n.bit_length():_}"


@dataclass
class Config:
  is_halt: bool
  h: mpz | None = None
  w: int | None = None
  halt_config: list[int] | None = None

  @staticmethod
  def running(h: mpz, w: int) -> Config:
    return Config(is_halt=False, h=h, w=w)

  @staticmethod
  def halt(config: list[int]) -> Config:
    # TODO: Make halt_config accurate
    return Config(is_halt=True)  # , halt_config=config)

  def __str__(self):
    if self.is_halt:
      # TODO: Add something about halt config
      return "Halt"
    else:
      h_str = approx_str(self.h)
      return f"w={self.w:_} h{h_str}"


@dataclass
class StepResult:
  """Result of taking one sim steps."""

  config: Config
  delta_runtime: mpz


@dataclass
class RunResult:
  """Result of taking one or more sim steps."""

  config: Config
  delta_sim_steps: int
  delta_runtime: mpz
  min_w: int
  max_w: int

  def concat(self, second: RunResult) -> RunResult:
    """Merge two consecutive results"""
    return RunResult(
      config=second.config,
      delta_sim_steps=self.delta_sim_steps + second.delta_sim_steps,
      delta_runtime=self.delta_runtime + second.delta_runtime,
      min_w=min(self.min_w, second.min_w),
      max_w=max(self.max_w, second.max_w),
    )

  def __str__(self):
    t_str = approx_str(self.delta_runtime)
    return f"  sim_steps={self.delta_sim_steps:_}:  {self.config!s}  w_range=[{self.min_w:_}, {self.max_w:_}]  t{t_str}"


class Sim(ABC):
  # Subclasses must define:
  #   mod_in: mpz
  #   mod_out: mpz
  #   mod_time: mpz

  @abstractmethod
  def sim_step(self, h: mpz, w: int) -> StepResult:
    """Single simulation step: one application of high level function."""

  def __init__(self, config: Config, init_runtime: mpz):
    self.result = RunResult(
      config=config,
      delta_sim_steps=0,
      delta_runtime=init_runtime,
      min_w=config.w,
      max_w=config.w,
    )
    # Copy
    self.start_config = replace(config)

  def direct(self, config: Config, max_sim_steps: int) -> RunResult:
    """Directly simulate for multiple steps (or until halt)"""
    min_w: int = config.w
    max_w: int = config.w
    sim_steps = 0
    time = 0
    while not config.is_halt and sim_steps < max_sim_steps:
      # Update min/max before step since config.w is None after halt
      min_w = min(min_w, config.w)
      max_w = max(max_w, config.w)

      res = self.sim_step(config.h, config.w)

      sim_steps += 1
      time += res.delta_runtime
      config = res.config

    return RunResult(config=config, delta_sim_steps=sim_steps, delta_runtime=time, min_w=min_w, max_w=max_w)

  def accel_pow(self, config: Config, e: int) -> RunResult:
    """Accelerated sim of 2**e sim_steps. Uses divide-and-conquer.
    Takes advantage of this identity:
      f^n(x mod_in^n + r) = x mod_out^n + f^n(r)
    """
    assert not config.is_halt
    if e <= 6:
      return self.direct(config, 2**e)

    def sim_expand(config: Config, e: int) -> RunResult:
      max_sim_steps = 2**e
      k, r = divmod(config.h, self.mod_in**max_sim_steps)
      res = self.accel_pow(Config.running(r, config.w), e)

      # Update h and runtime to account for extra (k) not accounted for in res
      # Note: We only update for the actual number of sim steps executed (not max_sim_steps)
      # TODO: How do we update halt config?
      if res.config.h:
        res.config.h += k * self.mod_out**res.delta_sim_steps
      res.delta_runtime += k * self.mod_time**res.delta_sim_steps
      return res

    # First half
    res1 = sim_expand(config, e - 1)
    if res1.config.is_halt:
      return res1

    # Second half
    res2 = sim_expand(res1.config, e - 1)
    return res1.concat(res2)

  def run_pow(self, e: int) -> None:
    """Run for 2^e sim_steps (or until halt if sooner). Updating self."""
    res = self.accel_pow(self.result.config, e)
    self.result = self.result.concat(res)

  def sim_forever(self, start_e: int = 0):
    """Simulate until halt (or memory failure)"""
    # Run forever. Print results at exponentially increasing checkpoints.
    self.print_info()
    self.run_pow(start_e)
    e = start_e
    while not self.result.config.is_halt:
      self.print_info()
      self.run_pow(e)
      e += 1
    print("Halt detected.")
    self.print_info()

  # TODO
  # def sim_direct(self):
  #   h, w = self.h, self.w
  #   i = 0
  #   next_i = 1
  #   max_w = w
  #   t = 0
  #   while w >= 0:
  #     try:
  #       h, w, dt = self.sim_step(h, w)
  #     except HaltTransition as halt_info:
  #       i += 1
  #       t += halt_info.time_delta
  #       print("Halted via HaltTransition")
  #       break
  #     max_w = max(max_w, w)
  #     i += 1
  #     t += dt
  #     if i == next_i:
  #       print_info(i, self.start_h, w, max_w, h, t)
  #       next_i *= 2
  #   if w < 0:
  #     print("Halted via w < 0")
  #   print_info(i, self.start_h, w, max_w, h, t)

  def print_info(self) -> None:
    print(f"{self.result!s}  ({process_memory() // 10**6:_}MB {time.process_time():_.0f}s)")


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
  mod_time = mpz(11)

  def sim_step(self, h: mpz, w: int) -> StepResult:
    k, r = divmod(h, 3)
    if r == 0:
      if w == 0:
        return StepResult(Config.halt([0, 2 * k + 1, 0]), 5 * k + 3)
      else:
        return StepResult(Config.running(4 * k + 2, w - 1), 11 * k + 7)
    elif r == 1:
      return StepResult(Config.running(4 * k + 3, w + 1), 11 * k + 9)
    else:
      return StepResult(Config.running(4 * k + 3, w), 11 * k + 9)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("start_value", type=int, nargs="?", default=1)
  parser.add_argument("start_offset", type=int, nargs="?", default=1)
  parser.add_argument("init_runtime", type=int, nargs="?", default=3, help="TM steps until start config")
  args = parser.parse_args()

  start_config = Config.running(args.start_value, args.start_offset)

  sim = MBB1(start_config, args.init_runtime)
  sim.sim_forever()
  # print()
  # sim_direct(args.start_value, args.start_offset)


if __name__ == "__main__":
  main()
