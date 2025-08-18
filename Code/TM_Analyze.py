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
    self.total2 = 0
    self.min_value = math.inf
    self.max_value = 0

    # # Histogram of the order of magnitudes.
    # # self.log_hist[n] == # values in range [10^n, 10^(n+1))
    # self.log_hist = collections.Counter()

  def add(self, value) -> None:
    if value:
      self.count += 1
      self.total += value
      self.total2 += value**2
      self.min_value = min(self.min_value, value)
      self.max_value = max(self.max_value, value)
      # self.log_hist[int(math.log10(value))] += 1

  def mean(self) -> float:
    if self.count:
      return self.total / self.count
    else:
      return 0.0
    
  def std_dev(self) -> float:
    if self.count:
      mean_val = self.total / self.count
      mean_val2 = self.total2 / self.count
      # sigma^2 = E[X^2] - E[X]^2
      return math.sqrt(mean_val2 - mean_val**2)
    else:
      return 0.0

class BigIntStat:
  def __init__(self):
    self.count = 0
    self.max_value = 0
    self.best_tm = ""

  def add(self, value, tm: str):
    if value:
      self.count += 1
      if value > self.max_value:
        self.max_value = value
        self.best_tm = tm

  def max_str(self):
    return Halting_Lib.big_int_approx_and_full_str(self.max_value) + "   " + self.best_tm


class TMStats:
  def __init__(self, options):
    self.options = options

    self.count = 0

    self.num_unknown = 0
    self.num_halt = 0
    self.num_inf = 0
    self.num_qhalt = 0

    self.halt_steps = BigIntStat()
    self.halt_score = BigIntStat()
    self.unknown_reason = collections.Counter()
    self.inf_reason = collections.Counter()
    self.qhalt_steps = BigIntStat()

    self.filters_run = collections.Counter()

    self.sim_num_loops = Stat()
    self.sim_log10_num_steps = Stat()
    self.sim_num_rules_proven = Stat()
    self.sim_num_finite_linear_rules_proven = Stat()
    self.sim_num_exponential_rules_proven = Stat()
    self.sim_num_gen_rules_proven = Stat()
    self.sim_num_collatz_rules = Stat()
    self.sim_num_proofs_failed = Stat()
    self.sim_num_rule_moves = Stat()

    self.lr_start_step = Stat()
    self.lr_period = Stat()
    self.lr_abs_offset = Stat()

    self.bt_max_steps = Stat()
    self.bt_max_width = Stat()

    self.cg_block_size = Stat()
    self.cg_num_steps = Stat()
    self.cg_num_configs = Stat()
    self.cg_num_edges = Stat()
    self.cg_num_iters = Stat()
    self.cg_found_inf_loop = Stat()

    self.timings_s = collections.defaultdict(Stat)
    self.sizes = collections.defaultdict(Stat)

  def add_record(self, tm_record: IO.TM_Record):
    self.count += 1
    proto = tm_record.proto

    # Halt status
    if not proto.status.halt_status.is_decided:
      self.num_unknown += 1
      self.unknown_reason[proto.filter.simulator.result.unknown_info.WhichOneof("reason")] += 1

    elif proto.status.halt_status.is_halting:
      self.num_halt += 1
      num_steps = Halting_Lib.get_big_int(proto.status.halt_status.halt_steps)
      self.halt_steps.add(num_steps, tm_record.ttable_str())
      score = Halting_Lib.get_big_int(proto.status.halt_status.halt_score)
      self.halt_score.add(score, tm_record.ttable_str())

    else:
      self.num_inf += 1
      self.inf_reason[proto.status.halt_status.inf_reason] += 1

    # Quasihalt status
    if self.options.beep and proto.status.quasihalt_status.is_quasihalting:
      self.num_qhalt += 1
      num_steps = Halting_Lib.get_big_int(proto.status.quasihalt_status.quasihalt_steps)
      self.qhalt_steps.add(num_steps, tm_record.ttable_str())

    # Which filters were run
    for descr in proto.filter.DESCRIPTOR.fields:
      filter = descr.name
      if proto.filter.HasField(filter):
        self.filters_run[filter] += 1

    if self.options.filter_details:
      # Simulator stats
      self.sim_num_loops.add(proto.filter.simulator.result.num_loops)
      sim_log10_num_steps = proto.filter.simulator.result.log10_num_steps
      self.sim_log10_num_steps.add(sim_log10_num_steps)
      self.sim_num_rules_proven.add(proto.filter.simulator.result.num_rules_proven)
      self.sim_num_finite_linear_rules_proven.add(proto.filter.simulator.result.num_finite_linear_rules_proven)
      self.sim_num_exponential_rules_proven.add(proto.filter.simulator.result.num_exponential_rules_proven)
      self.sim_num_gen_rules_proven.add(proto.filter.simulator.result.num_gen_rules_proven)
      self.sim_num_collatz_rules.add(proto.filter.simulator.result.num_collatz_rules)
      self.sim_num_proofs_failed.add(proto.filter.simulator.result.num_proofs_failed)
      self.sim_num_rule_moves.add(proto.filter.simulator.result.num_rule_moves)

      self.lr_start_step.add(proto.filter.lin_recur.result.start_step)
      self.lr_period.add(proto.filter.lin_recur.result.period)
      self.lr_abs_offset.add(abs(proto.filter.lin_recur.result.offset))

      if proto.filter.backtrack.result.success:
        self.bt_max_steps.add(proto.filter.backtrack.result.max_steps)
        self.bt_max_width.add(proto.filter.backtrack.result.max_width)

      if proto.filter.cps.result.block_size:
        self.cg_block_size.add(proto.filter.cps.result.block_size)
        self.cg_num_steps.add(proto.filter.cps.result.num_steps)
        self.cg_num_configs.add(proto.filter.cps.result.num_configs)
        self.cg_num_edges.add(proto.filter.cps.result.num_edges)
        self.cg_num_iters.add(proto.filter.cps.result.num_iters)
        self.cg_found_inf_loop.add(proto.filter.cps.result.found_inf_loop)

    if self.options.time:
      # Timing
      self.timings_s["total"].add(proto.elapsed_time_us / 1e6)
      self.timings_s["simulator"].add(proto.filter.simulator.result.elapsed_time_us / 1e6)
      self.timings_s["block_finder"].add(proto.filter.block_finder.result.elapsed_time_us / 1e6)
      self.timings_s["reverse_engineer"].add(proto.filter.reverse_engineer.elapsed_time_us / 1e6)
      self.timings_s["lin_recur"].add(proto.filter.lin_recur.result.elapsed_time_us / 1e6)
      self.timings_s["ctl"].add((
        proto.filter.ctl.ctl_as.result.elapsed_time_us +
        proto.filter.ctl.ctl_as_b.result.elapsed_time_us +
        proto.filter.ctl.ctl_a_bs.result.elapsed_time_us +
        proto.filter.ctl.ctl_as_b_c.result.elapsed_time_us
        ) / 1e6)
      self.timings_s["backtrack"].add(proto.filter.backtrack.result.elapsed_time_us / 1e6)
      self.timings_s["cps"].add(proto.filter.cps.result.elapsed_time_us / 1e6)

    if self.options.size:
      # Serialized Size
      self.sizes["total"].add(proto.ByteSize())
      self.sizes["tm"].add(proto.tm.ByteSize())
      self.sizes["status"].add(proto.status.ByteSize())
      self.sizes["filter"].add(proto.filter.ByteSize())

      self.sizes["simulator"].add(proto.filter.simulator.ByteSize())
      self.sizes["block_finder"].add(proto.filter.block_finder.ByteSize())
      self.sizes["lin_recur"].add(proto.filter.lin_recur.ByteSize())
      self.sizes["ctl"].add(proto.filter.ctl.ByteSize())
      self.sizes["backtrack"].add(proto.filter.backtrack.ByteSize())
      self.sizes["cps"].add(proto.filter.cps.ByteSize())

  def print(self):
    print()
    print(f"Total: {self.count:_}")
    print()
    print(f"Unknown: {self.num_unknown:_} ({self.num_unknown / self.count:.3%})")
    for (reason, count) in sorted(self.unknown_reason.items(), key=lambda x: x[1], reverse=True):
      print(f"  - {str(reason):20s} : "
            f"{count:15_}  ({count / self.num_unknown:7.2%})")
    print()
    print(f"Halt: {self.num_halt:_} ({self.num_halt / self.count:.3%})")
    print(f"  - Steps: Max {self.halt_steps.max_str()}")
    print(f"  - Score: Max {self.halt_score.max_str()}")
    print()
    print(f"Infinite: {self.num_inf:_} ({self.num_inf / self.count:.3%})")
    for (reason, count) in sorted(self.inf_reason.items(), key=lambda x: x[1], reverse=True):
      print(f"  - {io_pb2.InfReason.Name(reason):20s} : "
            f"{count:15_}  ({count / self.num_inf:7.2%})")
    print()

    if self.options.beep and self.num_qhalt:
      print(f"Quasihalt: {self.num_qhalt:_} ({self.num_qhalt / self.count:.3%})")
      print(f"  - Steps: Max {self.qhalt_steps.max_str()}")
      print()

    print("Filters Run:")
    for (filter, num_run) in sorted(self.filters_run.items(), key=lambda x: x[1], reverse=True):
      print(f"  - {filter:20s} : {num_run:15_d}  ({num_run / self.count:7.2%})")
    print()

    if self.options.filter_details:
      if self.sim_num_loops.count:
        print("Simulator:")
        print(f"  - num_loops             : Mean {self.sim_num_loops.mean():9_.0f}  Max {self.sim_num_loops.max_value:9_d}")
        # self.print_hist(self.sim_num_loops.log_hist)
        # print()
        print(f"  - log10(num_steps)      : Mean {self.sim_log10_num_steps.mean():9_.0f}  Max {self.sim_log10_num_steps.max_value:9_.0f}  Min {self.sim_log10_num_steps.min_value:9_.0f}")
        print(f"  - num_rules_proven      : Mean {self.sim_num_rules_proven.mean():9_.0f}  Max {self.sim_num_rules_proven.max_value:9_d}  (Set in {self.sim_num_rules_proven.count / self.count:7.2%})")
        print(f"  - num_linear_rules      : Mean {self.sim_num_finite_linear_rules_proven.mean():9_.0f}  Max {self.sim_num_finite_linear_rules_proven.max_value:9_d}  (Set in {self.sim_num_finite_linear_rules_proven.count / self.count:7.2%})")
        print(f"  - num_exponential_rules : Mean {self.sim_num_exponential_rules_proven.mean():9_.0f}  Max {self.sim_num_exponential_rules_proven.max_value:9_d}  (Set in {self.sim_num_exponential_rules_proven.count / self.count:7.2%})")
        print(f"  - num_gen_rules         : Mean {self.sim_num_gen_rules_proven.mean():9_.0f}  Max {self.sim_num_gen_rules_proven.max_value:9_d}  (Set in {self.sim_num_gen_rules_proven.count / self.count:7.2%})")
        print(f"  - num_collatz_rules     : Mean {self.sim_num_collatz_rules.mean():9_.0f}  Max {self.sim_num_collatz_rules.max_value:9_d}  (Set in {self.sim_num_collatz_rules.count / self.count:7.2%})")
        print(f"  - num_proofs_failed     : Mean {self.sim_num_proofs_failed.mean():9_.0f}  Max {self.sim_num_proofs_failed.max_value:9_d}  (Set in {self.sim_num_proofs_failed.count / self.count:7.2%})")
        print(f"  - num_rule_moves        : Mean {self.sim_num_rule_moves.mean():9_.0f}  Max {self.sim_num_rule_moves.max_value:9_d}  (Set in {self.sim_num_rule_moves.count / self.count:7.2%})")
        print()

      if self.lr_period.count:
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

      if self.bt_max_steps.count:
        print("Backtrack:")
        print(f"  - max_steps  : Mean {self.bt_max_steps.mean():_.2f}  "
              f"Max {self.bt_max_steps.max_value:_}  "
              f"(Set in {self.bt_max_steps.count / self.count:4.0%})")
        print(f"  - max_width  : Mean {self.bt_max_width.mean():_.2f}  "
              f"Max {self.bt_max_width.max_value:_}  "
              f"(Set in {self.bt_max_width.count / self.count:4.0%})")
        print()

      if self.cg_num_configs.count:
        print("CPS:")
        print(f"  - block_size     : Mean {self.cg_block_size.mean():11_.2f}  "
              f"StdDev {self.cg_block_size.std_dev():11_.2f}  "
              f"Max {self.cg_block_size.max_value:11_}")
        print(f"  - num_steps      : Mean {self.cg_num_steps.mean():11_.0f}  "
              f"StdDev {self.cg_num_steps.std_dev():11_.0f}  "
              f"Max {self.cg_num_steps.max_value:11_}")
        print(f"  - num_configs    : Mean {self.cg_num_configs.mean():11_.2f}  "
              f"StdDev {self.cg_num_configs.std_dev():11_.2f}  "
              f"Max {self.cg_num_configs.max_value:11_}")
        print(f"  - num_edges      : Mean {self.cg_num_edges.mean():11_.2f}  "
              f"StdDev {self.cg_num_edges.std_dev():11_.2f}  "
              f"Max {self.cg_num_edges.max_value:11_}")
        print(f"  - num_iters      : Mean {self.cg_num_iters.mean():11_.2f}  "
              f"StdDev {self.cg_num_iters.std_dev():11_.2f}  "
              f"Max {self.cg_num_iters.max_value:11_}")
        print(f"  - found_inf_loop : {self.cg_found_inf_loop.count:_d} ({self.cg_found_inf_loop.count / self.count:8.4%})")
        print()

    if self.options.time:
      print("Timings:")
      # Note: These are the mean timings for each filter over all TMs.
      mean_timings_s = sorted(
        [(timing.total / self.count, filter)
        for (filter, timing) in self.timings_s.items()
        if timing.count > 0],
        reverse=True)
      for (mean_time_s, filter) in mean_timings_s:
        print(f"  - {filter:16s} : Mean(all) {mean_time_s*1000:7_.3f} ms  "
              f"Mean(run) {self.timings_s[filter].mean()*1000:7_.3f} ms  "
              f"Max {self.timings_s[filter].max_value*1000:7_.3f} ms  "
              f"(Set in {self.timings_s[filter].count / self.count:4.0%})")
      print()

    if self.options.size:
      print("Serialized Sizes:")
      # Note: These are the mean space for each message over all TMs
      # (even ones without this message set).
      mean_sizes = sorted([(size.total / self.count, message)
                          for (message, size) in self.sizes.items()
                          if size.count > 0],
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
  print_default = 1_000_000

  parser = argparse.ArgumentParser()
  parser.add_argument("tm_file", type=Path, nargs="+")
  parser.add_argument("--print-freq", "-n", type=int, default=print_default,
                      help="[Default: {:_}]".format(print_default))

  parser.add_argument("--time", action="store_true", help="Print stats on timing")
  parser.add_argument("--size", action="store_true", help="Print stats on record sizes")
  parser.add_argument("--beep", action="store_true", help="Print stats on quasihalting")
  parser.add_argument("--filter-details", action="store_true",
                      help="Print stats on filter details")
  args = parser.parse_args()

  stats = TMStats(args)
  for filename in args.tm_file:
    try:
      with IO.Proto.Reader(filename) as reader:
        for tm_record in reader:
          stats.add_record(tm_record)
          if args.print_freq and (stats.count % args.print_freq == 0):
            stats.print()
    except IO.Proto.IO_Error:
      print(f"ERROR: {filename} has unexpected EOF. Moving on.")

  if stats.count > 0:
    stats.print()
  else:
    print("No Records in file")

if __name__ == "__main__":
  main()
