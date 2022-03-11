"""Analyze all TMRecords in a file and print various statistics."""

import argparse
import collections
from pathlib import Path

import Halting_Lib
import IO_proto

import io_pb2


class Stat:
  def __init__(self):
    self.count = 0
    self.total = 0
    self.max_value = 0

  def add(self, value):
    if value:
      self.count += 1
      self.total += value
      self.max_value = max(self.max_value, value)

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

    self.halt_steps = Stat()
    self.halt_score = Stat()
    self.inf_reason = collections.Counter()

    self.timings = {
      "simulator": Stat(),
      "block_finder": Stat(),
      "lin_recur": Stat(),
      "ctl": Stat(),
    }

    self.sizes = {
      "total": Stat(),
      "tm": Stat(),
      "status": Stat(),
      "filter": Stat(),
      "simulator": Stat(),
      "block_finder": Stat(),
      "lin_recur": Stat(),
      "ctl": Stat(),
    }

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
      self.inf_reason[tm_record.status.halt_status.reason] += 1

    # Timing
    self.timings["simulator"].add(tm_record.filter.simulator.result.elapsed_time_sec)
    self.timings["block_finder"].add(tm_record.filter.block_finder.result.elapsed_time_sec)
    self.timings["lin_recur"].add(tm_record.filter.lin_recur.result.elapsed_time_sec)
    self.timings["ctl"].add(tm_record.filter.ctl.elapsed_time_sec)

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
            f"{count:15_} ({count / self.num_inf:7.2%})")
    print()

    print("Timings:")
    # Note: These are the mean timings for each filter over all TMs
    # (even ones that never ran).
    mean_timings = sorted([(timing.total / self.count, filter)
                           for (filter, timing) in self.timings.items()],
                          reverse=True)
    for (mean_time_s, filter) in mean_timings:
      x = 1_000_000
      print(f"  - {filter:16s} : Mean(all) {mean_time_s * x:7_.0f} µs  "
            f"Mean(run) {self.timings[filter].mean() * x:7_.0f} µs  "
            f"Max {self.timings[filter].max_value * x:7_.0f} µs  "
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


def analyze(tm_filename):
  stats = TMStats()
  with open(tm_filename, "rb") as infile:
    reader = IO_proto.Reader(infile)
    for tm_record in reader:
      stats.add_record(tm_record)
      if stats.count % 1_000_000 == 0:
        stats.print()

  stats.print()

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm_file", type=Path)
  args = parser.parse_args()

  analyze(args.tm_file)

if __name__ == "__main__":
  main()
