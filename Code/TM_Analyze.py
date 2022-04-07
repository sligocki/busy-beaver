#! /usr/bin/env python3
"""Analyze all TMRecords in a file and print various statistics."""

import argparse
import collections
import math
from pathlib import Path

import Halting_Lib
import IO

import io_pb2


class Stat:
  def __init__(self):
    self.count = 0
    self.total = 0
    self.max_value = 0

    # Histogram of the order of magnitudes.
    # self.log_hist[n] == # values in range [10^n, 10^(n+1))
    self.log_hist = collections.Counter()

  def add(self, value):
    if value:
      self.count += 1
      self.total += value
      self.max_value = max(self.max_value, value)
      self.log_hist[int(math.log10(value))] += 1

  def mean(self):
    if self.count:
      return self.total / self.count
    else:
      return 0.0


class TMStats:
  def __init__(self):
    self.count = 0

    self.num_unknown = 0
    self.num_halt = 0
    self.num_inf = 0
    self.num_qhalt = 0

    self.halt_steps = Stat()
    self.halt_score = Stat()
    self.inf_reason = collections.Counter()
    self.qhalt_steps = Stat()

    self.filters_run = collections.Counter()

    self.sim_num_loops = Stat()
    self.sim_log10_num_steps = Stat()
    self.sim_num_rules_proven = Stat()
    self.sim_num_proofs_failed = Stat()
    self.sim_num_rule_moves = Stat()

    self.lr_start_step = Stat()
    self.lr_period = Stat()
    self.lr_abs_offset = Stat()

    self.timings = collections.defaultdict(Stat)
    self.sizes = collections.defaultdict(Stat)

  def add_record(self, tm_record):
    self.count += 1

    # Halt status
    if not tm_record.status.halt_status.is_decided:
      self.num_unknown += 1

    elif tm_record.status.halt_status.is_halting:
      self.num_halt += 1
      num_steps = Halting_Lib.get_big_int(tm_record.status.halt_status.halt_steps)
      self.halt_steps.add(num_steps)
      score = Halting_Lib.get_big_int(tm_record.status.halt_status.halt_score)
      self.halt_score.add(score)

    else:
      self.num_inf += 1
      self.inf_reason[tm_record.status.halt_status.inf_reason] += 1

    # Quasihalt status
    if tm_record.status.quasihalt_status.is_quasihalting:
      self.num_qhalt += 1
      num_steps = Halting_Lib.get_big_int(tm_record.status.quasihalt_status.quasihalt_steps)
      self.qhalt_steps.add(num_steps)

    # Which filters were run
    for descr in tm_record.filter.DESCRIPTOR.fields:
      filter = descr.name
      if tm_record.filter.HasField(filter):
        self.filters_run[filter] += 1

    # Simulator stats
    self.sim_num_loops.add(tm_record.filter.simulator.result.num_loops)
    sim_log10_num_steps = tm_record.filter.simulator.result.log10_num_steps
    self.sim_log10_num_steps.add(sim_log10_num_steps)
    self.sim_num_rules_proven.add(tm_record.filter.simulator.result.num_rules_proven)
    self.sim_num_proofs_failed.add(tm_record.filter.simulator.result.num_proofs_failed)
    self.sim_num_rule_moves.add(tm_record.filter.simulator.result.num_rule_moves)

    self.lr_start_step.add(tm_record.filter.lin_recur.result.start_step)
    self.lr_period.add(tm_record.filter.lin_recur.result.period)
    self.lr_abs_offset.add(abs(tm_record.filter.lin_recur.result.offset))

    # Timing
    self.timings["total"].add(tm_record.elapsed_time_us)
    self.timings["simulator"].add(tm_record.filter.simulator.result.elapsed_time_us)
    self.timings["block_finder"].add(tm_record.filter.block_finder.result.elapsed_time_us)
    self.timings["reverse_engineer"].add(tm_record.filter.reverse_engineer.elapsed_time_us)
    self.timings["lin_recur"].add(tm_record.filter.lin_recur.result.elapsed_time_us)
    self.timings["ctl"].add(tm_record.filter.ctl.elapsed_time_us)

    # Serialized Size
    self.sizes["total"].add(tm_record.ByteSize())
    self.sizes["tm"].add(tm_record.tm.ByteSize())
    self.sizes["status"].add(tm_record.status.ByteSize())
    self.sizes["filter"].add(tm_record.filter.ByteSize())
    self.sizes["simulator"].add(tm_record.filter.simulator.ByteSize())
    self.sizes["block_finder"].add(tm_record.filter.block_finder.ByteSize())
    self.sizes["lin_recur"].add(tm_record.filter.lin_recur.ByteSize())
    self.sizes["ctl"].add(tm_record.filter.ctl.ByteSize())

  def print(self):
    print()
    print(f"Total: {self.count:_}")
    print()
    print(f"Unknown: {self.num_unknown:_} ({self.num_unknown / self.count:.3%})")
    print()
    print(f"Halt: {self.num_halt:_} ({self.num_halt / self.count:.3%})")
    print(f"  - Steps: Max {self.halt_steps.max_value:_} Mean {self.halt_steps.mean():_.1f}")
    print(f"  - Score: Max {self.halt_score.max_value:_} Mean {self.halt_score.mean():_.1f}")
    print()
    print(f"Infinite: {self.num_inf:_} ({self.num_inf / self.count:.3%})")
    for (reason, count) in sorted(self.inf_reason.items(), key=lambda x: x[1], reverse=True):
      print(f"  - {io_pb2.InfReason.Name(reason):20s} : "
            f"{count:15_}  ({count / self.num_inf:7.2%})")
    print()
    print(f"Quasihalt: {self.num_qhalt:_} ({self.num_qhalt / self.count:.3%})")
    if self.qhalt_steps.max_value > 0:
      print(f"  - Steps: Max 10^{math.log10(self.qhalt_steps.max_value):.1f}")
    print()

    print("Filters Run:")
    for (filter, num_run) in sorted(self.filters_run.items(), key=lambda x: x[1], reverse=True):
      print(f"  - {filter:20s} : {num_run:15_d}  ({num_run / self.count:7.2%})")
    print()

    print("Lin Recur:")
    print(f"  - start_step  : Mean {self.lr_start_step.mean():_.0f}  "
          f"Max {self.lr_start_step.max_value:_}  "
          f"(Set in {self.lr_start_step.count / self.count:4.0%})")
    print(f"  - period      : Mean {self.lr_period.mean():_.0f}  "
          f"Max {self.lr_period.max_value:_}  "
          f"(Set in {self.lr_period.count / self.count:4.0%})")
    print(f"  - abs(offset) : Mean {self.lr_abs_offset.mean():_.0f}  "
          f"Max {self.lr_abs_offset.max_value:_}  "
          f"(Set in {self.lr_abs_offset.count / self.count:4.0%})")
    print()

    print("Simulator:")
    print(f"  - num_loops : Mean {self.sim_num_loops.mean():9_.0f}  Max {self.sim_num_loops.max_value:9_d}  (Set in {self.sim_num_loops.count / self.count:4.0%})")
    # self.print_hist(self.sim_num_loops.log_hist)
    # print()
    print(f"  - log10(num_steps) : Mean {self.sim_log10_num_steps.mean():9_.0f}  Max {self.sim_log10_num_steps.max_value:9_d}  (Set in {self.sim_log10_num_steps.count / self.count:4.0%})")
    print(f"  - num_rules_proven : Mean {self.sim_num_rules_proven.mean():9_.0f}  Max {self.sim_num_rules_proven.max_value:9_d}  (Set in {self.sim_num_rules_proven.count / self.count:4.0%})")
    print(f"  - num_proofs_failed : Mean {self.sim_num_proofs_failed.mean():9_.0f}  Max {self.sim_num_proofs_failed.max_value:9_d}  (Set in {self.sim_num_proofs_failed.count / self.count:4.0%})")
    print(f"  - num_rule_moves : Mean {self.sim_num_rule_moves.mean():9_.0f}  Max {self.sim_num_rule_moves.max_value:9_d}  (Set in {self.sim_num_rule_moves.count / self.count:4.0%})")
    print()

    print("Timings:")
    # Note: These are the mean timings for each filter over all TMs
    # (even ones that never ran).
    mean_timings = sorted([(timing.total / self.count, filter)
                           for (filter, timing) in self.timings.items()],
                          reverse=True)
    for (mean_time_us, filter) in mean_timings:
      print(f"  - {filter:16s} : Mean(all) {mean_time_us:7_.0f} µs  "
            f"Mean(run) {self.timings[filter].mean():7_.0f} µs  "
            f"Max {self.timings[filter].max_value:7_.0f} µs  "
            f"(Set in {self.timings[filter].count / self.count:4.0%})")
    print()

    print("Serialized Sizes:")
    # Note: These are the mean space for each message over all TMs
    # (even ones without this message set).
    mean_sizes = sorted([(size.total / self.count, message)
                         for (message, size) in self.sizes.items()],
                        reverse=True)
    for (mean_size_bytes, message) in mean_sizes:
      # TODO: Add Percentages
      print(f"  - {message:16s} : Mean(all) {mean_size_bytes:7_.1f} B   "
            f"Mean(set) {self.sizes[message].mean():7_.1f} B   "
            f"Max {self.sizes[message].max_value:7_.1f} B   "
            f"(Set in {self.sizes[message].count / self.count:4.0%})")
    print()

  def print_hist(self, hist):
    cum_total = 0
    total = sum(hist.values())
    # Only show up to the millions bucket.
    max_n = min(max(hist.keys()), 6)
    for n in range(max_n + 1):
      val = hist[n]
      cum_total += val
      print(f"     {10**n:9_} - {10**(n+1)-1:9_} : {val:9_} ({val / total:4.0%})  Cumulative: {cum_total:9_} ({cum_total / total:4.0%})")
    if cum_total < total:
      val = total - cum_total
      cum_total += val
      print(f"     > {10**(max_n+1):<20_}: {val:9_} ({val / total:4.0%})  Cumulative: {cum_total:9_} ({cum_total / total:4.0%})")


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm_file", type=Path, nargs="+")
  parser.add_argument("--print-freq", type=int, default=1_000_000)
  args = parser.parse_args()

  stats = TMStats()
  for filename in args.tm_file:
    try:
      with open(filename, "rb") as infile:
        reader = IO.Proto.Reader(infile)
        for tm_record in reader:
          stats.add_record(tm_record.proto)
          if args.print_freq and (stats.count % args.print_freq == 0):
            stats.print()
    except IO.Proto.IO_Error:
      print(f"ERROR: {filename} has unexpected EOF. Moving on.")

  stats.print()

if __name__ == "__main__":
  main()
