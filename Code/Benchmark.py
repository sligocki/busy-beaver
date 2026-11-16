#!/usr/bin/env python3
"""
Large-scale regression and benchmark runner for the Macro Simulator.

Evaluates configurations and git snapshots across three pillars:
1. Correctness: No Halt <-> Inf flips, ground-truth violations, or score mismatches.
2. Coverage: Decidability counts (Halt / Inf by reason), newly decided TMs, and regressions.
3. Runtime & Progress:
   - Decided TMs: Pure simulation runtime, post-eval (BigInterval) runtime, and total_loops.
   - Undecided TMs: Runtime/loops to reach a pre-recorded target_max_span milestone,
     plus comparison of final max_span reached at max_loops.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import dataclasses
from dataclasses import dataclass
import datetime
import gzip
import json
import math
import optparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from typing import Any

from Big_Interval import BigInterval, Knuth10
import Exp_Int
import IO
import io_pb2
from Macro import Simulator, Turing_Machine
from NatExpr import approx_str, big_interval_str, to_BigInterval
from Time_Limit import TimeLimit


ROOT_DIR = Path(__file__).resolve().parent.parent
BENCH_DIR = ROOT_DIR / "benchmarks"
DATASETS_DIR = BENCH_DIR / "datasets"
RESULTS_DIR = BENCH_DIR / "results"


@dataclass(frozen=True)
class BenchConfig:
  """Configuration for a Macro Simulator benchmark run.

  Prover hierarchy (each level enables all previous levels):
    0: prover=False
    1: prover=True (Level 1 Diff Rules)
    2: prover=True, recursive=True (+ Meta-Diff Rules)
    3: prover=True, recursive=True, exp_linear_rules=True (+ Iterated/Linear Rules)
    4: prover=True, recursive=True, exp_linear_rules=True, exp_meta_linear_rules=True (+ Meta-Iterated Rules)
  """

  name: str
  prover_level: int = 1
  backsymbol: bool = True
  limited_rules: bool = True
  exp_const_blocks: bool = False
  only_record_configs: bool = False
  use_big_interval: bool = True
  compute_steps: bool = False

  def __post_init__(self):
    assert 0 <= self.prover_level <= 4, f"Invalid prover_level: {self.prover_level}"

  @property
  def prover(self) -> bool:
    return self.prover_level >= 1

  @property
  def recursive(self) -> bool:
    return self.prover_level >= 2

  @property
  def exp_linear_rules(self) -> bool:
    return self.prover_level >= 3

  @property
  def exp_meta_linear_rules(self) -> bool:
    return self.prover_level >= 4

  def to_options(self) -> optparse.Values:
    options = Simulator.create_default_options()
    options.backsymbol = self.backsymbol
    options.prover = self.prover
    options.limited_rules = self.limited_rules if self.prover else False
    options.recursive = self.recursive
    options.exp_linear_rules = self.exp_linear_rules
    options.exp_meta_linear_rules = self.exp_meta_linear_rules
    options.exp_const_blocks = self.exp_const_blocks if self.prover else False
    options.only_record_configs = self.only_record_configs if self.prover else False
    options.use_big_interval = self.use_big_interval
    options.compute_steps = self.compute_steps and not self.exp_linear_rules
    options.verbose_simulator = False
    options.verbose_prover = False
    options.html_format = False
    options.full_reps = False
    return options

  def to_dict(self) -> dict[str, Any]:
    return dataclasses.asdict(self)

  @classmethod
  def from_dict(cls, d: dict[str, Any]) -> BenchConfig:
    return cls(**d)


CONFIG_PRESETS: dict[str, BenchConfig] = {
  # Baseline extremes
  "all_off": BenchConfig(
    name="all_off",
    prover_level=0,
    backsymbol=False,
    limited_rules=False,
    exp_const_blocks=False,
    only_record_configs=False,
    use_big_interval=False,
  ),
  "default": BenchConfig(
    name="default",
    prover_level=1,
    backsymbol=True,
    limited_rules=True,
    exp_const_blocks=False,
    only_record_configs=False,
    use_big_interval=True,
  ),
  "all_on": BenchConfig(
    name="all_on",
    prover_level=4,
    backsymbol=True,
    limited_rules=True,
    exp_const_blocks=True,
    only_record_configs=True,
    use_big_interval=True,
  ),
  # Cumulative Prover Hierarchy Ladder (modifiers fixed at backsymbol=True, limited_rules=True)
  "prover_0_off": BenchConfig(
    name="prover_0_off",
    prover_level=0,
    backsymbol=True,
    limited_rules=False,
  ),
  "prover_1_diff": BenchConfig(
    name="prover_1_diff",
    prover_level=1,
    backsymbol=True,
    limited_rules=True,
  ),
  "prover_2_rec": BenchConfig(
    name="prover_2_rec",
    prover_level=2,
    backsymbol=True,
    limited_rules=True,
  ),
  "prover_3_linear": BenchConfig(
    name="prover_3_linear",
    prover_level=3,
    backsymbol=True,
    limited_rules=True,
  ),
  "prover_4_meta_linear": BenchConfig(
    name="prover_4_meta_linear",
    prover_level=4,
    backsymbol=True,
    limited_rules=True,
  ),
  # Single-feature / modifier additions
  "only_backsymbol": BenchConfig(
    name="only_backsymbol",
    prover_level=0,
    backsymbol=True,
    limited_rules=False,
  ),
  "only_base_prover": BenchConfig(
    name="only_base_prover",
    prover_level=1,
    backsymbol=False,
    limited_rules=False,
  ),
  "plus_const_blocks": BenchConfig(
    name="plus_const_blocks",
    prover_level=4,
    backsymbol=True,
    limited_rules=True,
    exp_const_blocks=True,
    only_record_configs=False,
  ),
  "plus_only_record": BenchConfig(
    name="plus_only_record",
    prover_level=4,
    backsymbol=True,
    limited_rules=True,
    exp_const_blocks=False,
    only_record_configs=True,
  ),
  # Leave-one-out Ablations from all_on
  "ablate_backsymbol": BenchConfig(
    name="ablate_backsymbol",
    prover_level=4,
    backsymbol=False,
    limited_rules=True,
    exp_const_blocks=True,
    only_record_configs=True,
    use_big_interval=True,
  ),
  "ablate_limited_rules": BenchConfig(
    name="ablate_limited_rules",
    prover_level=4,
    backsymbol=True,
    limited_rules=False,
    exp_const_blocks=True,
    only_record_configs=True,
    use_big_interval=True,
  ),
  "ablate_const_blocks": BenchConfig(
    name="ablate_const_blocks",
    prover_level=4,
    backsymbol=True,
    limited_rules=True,
    exp_const_blocks=False,
    only_record_configs=True,
    use_big_interval=True,
  ),
  "ablate_only_record": BenchConfig(
    name="ablate_only_record",
    prover_level=4,
    backsymbol=True,
    limited_rules=True,
    exp_const_blocks=True,
    only_record_configs=False,
    use_big_interval=True,
  ),
  "ablate_big_interval": BenchConfig(
    name="ablate_big_interval",
    prover_level=4,
    backsymbol=True,
    limited_rules=True,
    exp_const_blocks=True,
    only_record_configs=True,
    use_big_interval=False,
  ),
}

PRESET_GROUPS: dict[str, list[str]] = {
  "core": ["all_off", "default", "prover_2_rec", "prover_3_linear", "prover_4_meta_linear", "all_on"],
  "ladder": ["prover_0_off", "prover_1_diff", "prover_2_rec", "prover_3_linear", "prover_4_meta_linear"],
  "modifiers": [
    "all_off",
    "only_backsymbol",
    "only_base_prover",
    "prover_4_meta_linear",
    "plus_const_blocks",
    "plus_only_record",
    "all_on",
  ],
  "ablation": [
    "all_on",
    "ablate_backsymbol",
    "ablate_limited_rules",
    "ablate_const_blocks",
    "ablate_only_record",
    "ablate_big_interval",
  ],
  "all": list(CONFIG_PRESETS.keys()),
}


def encode_knuth10_interval(val, use_big_interval: bool = True) -> dict[str, Any]:
  """Serialize a numeric/NatExpr value into exact int (if small), Knuth10 bounds, and display string."""
  if val is None:
    return {"exact": None, "bi": None, "str": "N/A"}

  exact_int = Exp_Int.try_eval(val)
  if exact_int is not None and abs(int(exact_int)) < 10**300:
    exact_int = int(exact_int)
    if use_big_interval:
      bi = BigInterval(exact_int)
      return {
        "exact": exact_int,
        "bi": [list(bi.lower.args), list(bi.upper.args)],
        "str": big_interval_str(exact_int),
      }
    return {
      "exact": exact_int,
      "bi": [[exact_int], [exact_int]],
      "str": str(exact_int),
    }

  if use_big_interval:
    try:
      bi = to_BigInterval(val)
      return {
        "exact": None,
        "bi": [list(bi.lower.args), list(bi.upper.args)],
        "str": big_interval_str(val),
      }
    except Exception:
      pass

  # Fallback when use_big_interval is False or to_BigInterval is unsupported
  if exact_int is not None:
    k_low = Knuth10.lower_bound_from_int(int(exact_int))
    k_high = Knuth10.upper_bound_from_int(int(exact_int))
    return {
      "exact": None,
      "bi": [list(k_low.args), list(k_high.args)],
      "str": approx_str(val),
    }
  return {
    "exact": None,
    "bi": None,
    "str": approx_str(val),
  }


def knuth10_ge(val_expr, target_args: list[int]) -> bool:
  """Check if val_expr >= Knuth10(*target_args) quickly."""
  target_k = Knuth10(*target_args)
  if len(target_k.args) == 1:
    target_int = target_k.args[0]
    exact = Exp_Int.try_eval(val_expr)
    if exact is not None:
      return int(exact) >= target_int
    # If try_eval is None, val_expr is >= 10^1000, while len(target_k.args) == 1 means < 10^1000.
    return True
  try:
    bi = to_BigInterval(val_expr)
    return bi.lower >= target_k
  except Exception:
    return False


def compare_encoded_values(enc_a: dict[str, Any], enc_b: dict[str, Any]) -> int | None:
  """Compare two encoded values: returns -1 if a < b, 0 if equal/overlapping, 1 if a > b, None if unknown."""
  if enc_a.get("exact") is not None and enc_b.get("exact") is not None:
    va = int(enc_a["exact"])
    vb = int(enc_b["exact"])
    return (va > vb) - (va < vb)

  bi_a = enc_a.get("bi")
  bi_b = enc_b.get("bi")
  if bi_a and bi_b:
    low_a, high_a = Knuth10(*bi_a[0]), Knuth10(*bi_a[1])
    low_b, high_b = Knuth10(*bi_b[0]), Knuth10(*bi_b[1])
    if high_a < low_b:
      return -1
    if high_b < low_a:
      return 1
    return 0
  return None


def scores_consistent(enc_a: dict[str, Any], enc_b: dict[str, Any]) -> bool:
  """Check whether two halting scores are consistent (identical exact value or overlapping BigIntervals)."""
  if enc_a.get("exact") is not None and enc_b.get("exact") is not None:
    return int(enc_a["exact"]) == int(enc_b["exact"])
  cmp_res = compare_encoded_values(enc_a, enc_b)
  if cmp_res is not None:
    return cmp_res == 0
  # If one or both runs lack BigInterval bounds (e.g. --no-big-interval or pre-BigInterval git commits),
  # only compare strings if neither is a BigInterval "[low, high]" range string.
  str_a = enc_a.get("str", "")
  str_b = enc_b.get("str", "")
  if str_a.startswith("[") != str_b.startswith("["):
    return True
  return str_a == str_b


def run_single_tm(
  entry: dict[str, Any],
  config_dict: dict[str, Any],
  undecided_mode: str = "both",
  max_loops_override: int | None = None,
  time_limit_sec: float = 15.0,
) -> dict[str, Any]:
  """Simulate a single dataset TM entry under the given BenchConfig."""
  config = BenchConfig.from_dict(config_dict)
  options = config.to_options()

  tm_str = entry["tm"]
  block_size = int(entry.get("block_size", 1))
  max_loops = int(max_loops_override if max_loops_override is not None else entry.get("max_loops", 10_000))
  tape_limit = int(entry.get("tape_limit", 50))
  max_steps_in_block = int(entry.get("max_steps_in_block", 100_000))
  max_steps_in_backsymbol = int(entry.get("max_steps_in_backsymbol", 1_000))
  target_span_args = entry.get("target_max_span_bi")

  options.block_size = block_size
  options.max_loops = max_loops
  options.tape_limit = tape_limit

  base_tm = IO.parse_tm(tm_str)
  time_limit = TimeLimit()
  base_tm.time_limit = time_limit

  machine: Turing_Machine.Turing_Machine = base_tm
  if block_size != 1:
    machine = Turing_Machine.Block_Macro_Machine(machine, block_size, max_sim_steps_per_symbol=max_steps_in_block)
  if config.backsymbol:
    machine = Turing_Machine.Backsymbol_Macro_Machine(machine, max_sim_steps_per_symbol=max_steps_in_backsymbol)

  sim = Simulator.Simulator(machine, options)

  milestone_reached = False
  milestone_loops: int | None = None
  milestone_time_us: int | None = None
  stop_at_milestone = False

  start_sim = time.perf_counter()

  if target_span_args is not None:
    if knuth10_ge(sim.get_max_span(), target_span_args):
      milestone_reached = True
      milestone_loops = 0
      milestone_time_us = 0

    def _on_record(s: Simulator.Simulator):
      nonlocal milestone_reached, milestone_loops, milestone_time_us, stop_at_milestone
      if not milestone_reached and knuth10_ge(s.get_max_span(), target_span_args):
        milestone_reached = True
        milestone_loops = s.total_loops
        milestone_time_us = int((time.perf_counter() - start_sim) * 1e6)
        if undecided_mode == "milestone" and (
          entry.get("baseline_status") == "unknown" or entry.get("category") in ("holdout", "unknown")
        ):
          stop_at_milestone = True

    sim.on_record_span = _on_record

  threw_exception = False
  exception_str = ""
  timed_out = False

  time_limit.start(time_limit_sec)
  try:
    while (
      (max_loops == 0 or sim.total_loops < max_loops)
      and sim.op_state == Turing_Machine.RUNNING
      and sim.tape.compressed_size() <= tape_limit
      and not stop_at_milestone
    ):
      sim.step(max_loops=max_loops)
      if machine.time_limit.timed_out:
        timed_out = True
        break
  except Exception as e:
    threw_exception = True
    exception_str = f"{type(e).__name__}: {e}"
  finally:
    time_limit.cancel()

  sim_time_us = int((time.perf_counter() - start_sim) * 1e6)

  # Post-simulation evaluation (halt_score & max_span)
  eval_start = time.perf_counter()
  status = "unknown"
  reason = ""
  score_encoded = {"exact": None, "bi": None, "str": "N/A"}

  if threw_exception:
    status = "unknown"
    reason = "threw_exception"
  elif sim.op_state in (Turing_Machine.HALT, Turing_Machine.UNDEFINED):
    status = "halt"
    reason = "HALT" if sim.op_state == Turing_Machine.HALT else "UNDEFINED"
    try:
      nonzeros = sim.get_nonzeros()
      score_encoded = encode_knuth10_interval(nonzeros, use_big_interval=config.use_big_interval)
    except Exp_Int.ExpIntGaveUp as e:
      status = "unknown"
      reason = f"over_expression_too_complex:{e}"
    except Exception as e:
      threw_exception = True
      exception_str = f"get_nonzeros {type(e).__name__}: {e}"
      status = "unknown"
      reason = "threw_exception"
  elif sim.op_state == Turing_Machine.INF_REPEAT:
    status = "inf"
    reason = io_pb2.InfReason.Name(sim.inf_reason)
  elif timed_out:
    status = "unknown"
    reason = "over_time"
  elif stop_at_milestone:
    status = "unknown"
    reason = "reached_milestone"
  elif sim.tape.compressed_size() > tape_limit:
    status = "unknown"
    reason = "over_tape"
  elif sim.op_state in (Turing_Machine.RUNNING, Turing_Machine.OVER_LOOPS):
    status = "unknown"
    reason = "over_loops"
  elif sim.op_state == Turing_Machine.OVER_STEPS_IN_MACRO:
    status = "unknown"
    reason = "over_steps_in_macro"
  elif sim.op_state == Turing_Machine.EXPRESSION_TOO_COMPLEX:
    status = "unknown"
    reason = "over_expression_too_complex"
  else:
    status = "unknown"
    reason = str(sim.op_state)

  try:
    max_span_encoded = encode_knuth10_interval(sim.get_max_span(), use_big_interval=config.use_big_interval)
  except Exception:
    max_span_encoded = {"exact": None, "bi": None, "str": "error"}

  eval_time_us = int((time.perf_counter() - eval_start) * 1e6)

  rules_by_level: dict[int, int] = {}
  if sim.prover and sim.prover.num_rules_by_level:
    rules_by_level = {int(k): int(v) for k, v in sim.prover.num_rules_by_level.items() if v > 0}
  max_level = max(rules_by_level.keys(), default=0)

  return {
    "tm": tm_str,
    "name": entry.get("name", tm_str),
    "category": entry.get("category", "unknown"),
    "block_size": block_size,
    "config": config.name,
    "status": status,
    "reason": reason,
    "sim_time_us": sim_time_us,
    "eval_time_us": eval_time_us,
    "total_time_us": sim_time_us + eval_time_us,
    "outer_loops": sim.num_loops,
    "prover_loops": sim.prover.num_loops if sim.prover else 0,
    "total_loops": sim.total_loops,
    "num_macro_moves": sim.num_macro_moves,
    "num_chain_moves": sim.num_chain_moves,
    "num_rule_moves": sim.num_rule_moves,
    "num_rules_proven": sim.prover.num_rules if sim.prover else 0,
    "num_meta_diff_rules": sim.prover.num_meta_diff_rules if sim.prover else 0,
    "num_linear_rules": sim.prover.num_linear_rules if sim.prover else 0,
    "num_exponential_rules": sim.prover.num_exponential_rules if sim.prover else 0,
    "num_gen_rules": sim.prover.num_gen_rules if sim.prover else 0,
    "num_collatz_rules": sim.prover.num_collatz_rules if sim.prover else 0,
    "num_failed_proofs": sim.prover.num_failed_proofs if sim.prover else 0,
    "rules_by_level": rules_by_level,
    "max_rule_level": max_level,
    "halt_score": score_encoded,
    "max_span": max_span_encoded,
    "milestone_reached": milestone_reached,
    "milestone_loops": milestone_loops,
    "milestone_time_us": milestone_time_us,
    "threw_exception": threw_exception,
    "exception_str": exception_str,
  }


def _worker_run_tm(args_tuple):
  return run_single_tm(*args_tuple)


def load_dataset(dataset_arg: str | Path) -> tuple[Path, list[dict[str, Any]]]:
  """Load a JSONL dataset by preset name ('fast', 'full') or file path."""
  p = Path(dataset_arg)
  if not p.exists():
    candidate = DATASETS_DIR / f"{dataset_arg}.jsonl"
    if candidate.exists():
      p = candidate
    else:
      raise FileNotFoundError(f"Dataset not found: {dataset_arg} (checked {p} and {candidate})")

  entries = []
  open_fn = gzip.open if p.suffix == ".gz" else open
  with open_fn(p, "rt", encoding="utf-8") as f:
    for line in f:
      line = line.strip()
      if line:
        entries.append(json.loads(line))
  return p, entries


def save_run_results(
  out_path: Path,
  metadata: dict[str, Any],
  results: list[dict[str, Any]],
) -> None:
  out_path.parent.mkdir(parents=True, exist_ok=True)
  open_fn = gzip.open if out_path.suffix == ".gz" else open
  with open_fn(out_path, "wt", encoding="utf-8") as f:
    f.write(json.dumps({"_meta": metadata}) + "\n")
    for r in results:
      f.write(json.dumps(r) + "\n")


def load_run_results(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
  open_fn = gzip.open if path.suffix == ".gz" else open
  meta: dict[str, Any] = {}
  results: list[dict[str, Any]] = []
  with open_fn(path, "rt", encoding="utf-8") as f:
    for line in f:
      line = line.strip()
      if not line:
        continue
      obj = json.loads(line)
      if "_meta" in obj:
        meta = obj["_meta"]
      else:
        results.append(obj)
  return meta, results


def get_git_sha(repo_dir: Path = ROOT_DIR) -> str:
  try:
    res = subprocess.run(
      ["git", "rev-parse", "--short", "HEAD"],
      cwd=repo_dir,
      capture_output=True,
      text=True,
      check=True,
    )
    return res.stdout.strip()
  except Exception:
    return "unknown"


def run_benchmark_config(
  entries: list[dict[str, Any]],
  config: BenchConfig,
  dataset_name: str,
  undecided_mode: str = "both",
  max_loops_override: int | None = None,
  time_limit_sec: float = 15.0,
  jobs: int = 1,
  out_path: Path | None = None,
  quiet: bool = False,
) -> tuple[Path, dict[str, Any], list[dict[str, Any]]]:
  """Run a benchmark configuration across all dataset entries."""
  start_wall = time.time()
  config_dict = config.to_dict()
  tasks = [(entry, config_dict, undecided_mode, max_loops_override, time_limit_sec) for entry in entries]

  results_by_idx: dict[int, dict[str, Any]] = {}
  if jobs <= 1:
    for i, task in enumerate(tasks):
      results_by_idx[i] = _worker_run_tm(task)
      if not quiet and (i + 1) % max(1, len(tasks) // 10) == 0:
        print(f"  [{config.name}] {i + 1}/{len(tasks)} TMs completed ({time.time() - start_wall:.1f}s)")
  else:
    with ProcessPoolExecutor(max_workers=jobs) as pool:
      fut_to_idx = {pool.submit(_worker_run_tm, task): i for i, task in enumerate(tasks)}
      done_count = 0
      for fut in as_completed(fut_to_idx):
        idx = fut_to_idx[fut]
        results_by_idx[idx] = fut.result()
        done_count += 1
        if not quiet and done_count % max(1, len(tasks) // 10) == 0:
          print(f"  [{config.name}] {done_count}/{len(tasks)} TMs completed ({time.time() - start_wall:.1f}s)")

  ordered_results = [results_by_idx[i] for i in range(len(tasks))]
  wall_sec = time.time() - start_wall

  git_sha = get_git_sha()
  timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
  if out_path is None:
    out_path = RESULTS_DIR / f"{timestamp}_{git_sha}_{dataset_name}_{config.name}.jsonl.gz"

  metadata = {
    "config": config_dict,
    "config_name": config.name,
    "dataset": dataset_name,
    "num_tms": len(ordered_results),
    "git_sha": git_sha,
    "undecided_mode": undecided_mode,
    "time_limit_sec": time_limit_sec,
    "wall_time_sec": wall_sec,
    "timestamp": timestamp,
  }
  save_run_results(out_path, metadata, ordered_results)
  if not quiet:
    print(f"Saved {len(ordered_results)} results to {out_path} ({wall_sec:.2f}s wall)")
  return out_path, metadata, ordered_results


# Standalone adapter script executed inside temporary git worktrees so older commits
# (even those predating Benchmark.py or Simulator.get_max_span) can run the dataset.
_SNAPSHOT_WORKER_SCRIPT = """
import gzip
import json
import optparse
import os
from pathlib import Path
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

code_dir = sys.argv[1]
dataset_path = sys.argv[2]
config_json = sys.argv[3]
out_path = sys.argv[4]
undecided_mode = sys.argv[5]
time_limit_sec = float(sys.argv[6])
jobs = int(sys.argv[7])
git_ref = sys.argv[8]

sys.path.insert(0, code_dir)

import IO
import io_pb2
from Macro import Simulator, Turing_Machine
from Time_Limit import TimeLimit

try:
  from Big_Interval import BigInterval, Knuth10
  from NatExpr import approx_str, big_interval_str, to_BigInterval
  HAS_BIG_INTERVAL = True
except ImportError:
  HAS_BIG_INTERVAL = False

import Exp_Int

config = json.loads(config_json)

def encode_val(val, use_bi):
  if val is None:
    return {"exact": None, "bi": None, "str": "N/A"}
  exact = Exp_Int.try_eval(val) if hasattr(Exp_Int, "try_eval") else (val if isinstance(val, int) else None)
  if exact is not None and abs(int(exact)) < 10**300:
    exact = int(exact)
    if HAS_BIG_INTERVAL and use_bi:
      bi = BigInterval(exact)
      return {"exact": exact, "bi": [list(bi.lower.args), list(bi.upper.args)], "str": str(exact)}
    return {"exact": exact, "bi": [[exact], [exact]], "str": str(exact)}
  if HAS_BIG_INTERVAL and use_bi:
    try:
      bi = to_BigInterval(val)
      return {"exact": None, "bi": [list(bi.lower.args), list(bi.upper.args)], "str": big_interval_str(val)}
    except Exception:
      pass
  s = val.approx_str() if hasattr(val, "approx_str") else str(val)
  return {"exact": None, "bi": None, "str": s}

def get_sim_span(sim, block_size):
  if hasattr(sim, "get_max_span"):
    return sim.get_max_span()
  if hasattr(sim, "get_span"):
    return sim.get_span()
  return block_size * sum(
    b.num for b in (sim.tape.tape[0] + sim.tape.tape[1]) if b.num != Turing_Machine.INF
  )

def check_milestone(span_val, target_args):
  if not target_args:
    return False
  if len(target_args) == 1:
    if hasattr(Exp_Int, "try_eval"):
      ex = Exp_Int.try_eval(span_val)
    else:
      ex = span_val if isinstance(span_val, int) else None
    if ex is not None:
      return int(ex) >= target_args[0]
    return True
  if HAS_BIG_INTERVAL:
    try:
      bi = to_BigInterval(span_val)
      return bi.lower >= Knuth10(*target_args)
    except Exception:
      return False
  return False

def run_one(entry):
  options = Simulator.create_default_options()
  prover_level = int(config.get("prover_level", 1))
  options.backsymbol = bool(config.get("backsymbol", True))
  options.prover = prover_level >= 1
  options.limited_rules = bool(config.get("limited_rules", True)) if options.prover else False
  options.recursive = prover_level >= 2
  options.exp_linear_rules = prover_level >= 3
  options.exp_meta_linear_rules = prover_level >= 4
  options.exp_const_blocks = bool(config.get("exp_const_blocks", False)) if options.prover else False
  options.only_record_configs = bool(config.get("only_record_configs", False)) if options.prover else False
  options.use_big_interval = bool(config.get("use_big_interval", True))
  options.compute_steps = False
  options.verbose_simulator = False
  options.verbose_prover = False
  options.html_format = False
  options.full_reps = False

  tm_str = entry["tm"]
  block_size = int(entry.get("block_size", 1))
  max_loops = int(entry.get("max_loops", 10000))
  tape_limit = int(entry.get("tape_limit", 50))
  max_steps_in_block = int(entry.get("max_steps_in_block", 100000))
  max_steps_in_backsymbol = int(entry.get("max_steps_in_backsymbol", 1000))
  target_span_args = entry.get("target_max_span_bi")

  base_tm = IO.parse_tm(tm_str)
  time_limit = TimeLimit()
  base_tm.time_limit = time_limit

  machine = base_tm
  if block_size != 1:
    machine = Turing_Machine.Block_Macro_Machine(machine, block_size, max_sim_steps_per_symbol=max_steps_in_block)
  if options.backsymbol:
    machine = Turing_Machine.Backsymbol_Macro_Machine(machine, max_sim_steps_per_symbol=max_steps_in_backsymbol)

  sim = Simulator.Simulator(machine, options)
  has_native_max_span = hasattr(sim, "get_max_span")
  tracked_max_span = 0

  milestone_reached = False
  milestone_loops = None
  milestone_time_us = None
  stop_at_milestone = False
  start_sim = time.perf_counter()

  threw_exception = False
  exception_str = ""
  timed_out = False

  def get_total_loops(s):
    if hasattr(s, "total_loops"):
      return s.total_loops
    return s.num_loops + (s.prover.num_loops if getattr(s, "prover", None) else 0)

  time_limit.start(time_limit_sec)
  try:
    while (
      (max_loops == 0 or get_total_loops(sim) < max_loops)
      and sim.op_state == Turing_Machine.RUNNING
      and sim.tape.compressed_size() <= tape_limit
      and not stop_at_milestone
    ):
      try:
        sim.step(max_loops=max_loops)
      except TypeError:
        sim.step()
      if not has_native_max_span:
        cur_sp = get_sim_span(sim, block_size)
        if cur_sp > tracked_max_span:
          tracked_max_span = cur_sp
      else:
        tracked_max_span = sim.get_max_span()

      if target_span_args and not milestone_reached:
        if check_milestone(tracked_max_span, target_span_args):
          milestone_reached = True
          milestone_loops = get_total_loops(sim)
          milestone_time_us = int((time.perf_counter() - start_sim) * 1e6)
          if undecided_mode == "milestone" and (
            entry.get("baseline_status") == "unknown" or entry.get("category") in ("holdout", "unknown")
          ):
            stop_at_milestone = True
      if machine.time_limit.timed_out:
        timed_out = True
        break
  except Exception as e:
    threw_exception = True
    exception_str = f"{type(e).__name__}: {e}"
  finally:
    time_limit.cancel()

  sim_time_us = int((time.perf_counter() - start_sim) * 1e6)
  eval_start = time.perf_counter()

  status = "unknown"
  reason = ""
  score_encoded = {"exact": None, "bi": None, "str": "N/A"}
  if threw_exception:
    status = "unknown"
    reason = "threw_exception"
  elif sim.op_state in (Turing_Machine.HALT, Turing_Machine.UNDEFINED):
    status = "halt"
    reason = "HALT" if sim.op_state == Turing_Machine.HALT else "UNDEFINED"
    try:
      score_encoded = encode_val(sim.get_nonzeros(), options.use_big_interval)
    except Exception:
      status = "unknown"
      reason = "threw_exception"
  elif sim.op_state == Turing_Machine.INF_REPEAT:
    status = "inf"
    reason = io_pb2.InfReason.Name(sim.inf_reason)
  elif timed_out:
    status = "unknown"
    reason = "over_time"
  elif stop_at_milestone:
    status = "unknown"
    reason = "reached_milestone"
  elif sim.tape.compressed_size() > tape_limit:
    status = "unknown"
    reason = "over_tape"
  else:
    status = "unknown"
    reason = "over_loops"

  final_span_val = sim.get_max_span() if has_native_max_span else tracked_max_span
  max_span_encoded = encode_val(final_span_val, options.use_big_interval)
  eval_time_us = int((time.perf_counter() - eval_start) * 1e6)

  rules_by_level = {}
  if getattr(sim, "prover", None) and hasattr(sim.prover, "num_rules_by_level"):
    rules_by_level = {int(k): int(v) for k, v in sim.prover.num_rules_by_level.items() if v > 0}

  return {
    "tm": tm_str,
    "name": entry.get("name", tm_str),
    "category": entry.get("category", "unknown"),
    "block_size": block_size,
    "config": f"{config['name']}@{git_ref}",
    "status": status,
    "reason": reason,
    "sim_time_us": sim_time_us,
    "eval_time_us": eval_time_us,
    "total_time_us": sim_time_us + eval_time_us,
    "outer_loops": sim.num_loops,
    "prover_loops": sim.prover.num_loops if getattr(sim, "prover", None) else 0,
    "total_loops": get_total_loops(sim),
    "num_macro_moves": sim.num_macro_moves,
    "num_chain_moves": sim.num_chain_moves,
    "num_rule_moves": sim.num_rule_moves,
    "num_rules_proven": sim.prover.num_rules if getattr(sim, "prover", None) else 0,
    "rules_by_level": rules_by_level,
    "max_rule_level": max(rules_by_level.keys(), default=0),
    "halt_score": score_encoded,
    "max_span": max_span_encoded,
    "milestone_reached": milestone_reached,
    "milestone_loops": milestone_loops,
    "milestone_time_us": milestone_time_us,
    "threw_exception": threw_exception,
    "exception_str": exception_str,
  }

if __name__ == "__main__":
  open_fn = gzip.open if dataset_path.endswith(".gz") else open
  with open_fn(dataset_path, "rt", encoding="utf-8") as f:
    entries = [json.loads(line) for line in f if line.strip()]
  t0 = time.time()
  results = [None] * len(entries)
  if jobs <= 1:
    for i, e in enumerate(entries):
      results[i] = run_one(e)
  else:
    with ProcessPoolExecutor(max_workers=jobs) as pool:
      futs = {pool.submit(run_one, e): i for i, e in enumerate(entries)}
      for fut in as_completed(futs):
        results[futs[fut]] = fut.result()
  meta = {
    "config": config,
    "config_name": f"{config['name']}@{git_ref}",
    "git_sha": git_ref,
    "num_tms": len(results),
    "wall_time_sec": time.time() - t0,
  }
  out_open = gzip.open if out_path.endswith(".gz") else open
  with out_open(out_path, "wt", encoding="utf-8") as f:
    f.write(json.dumps({"_meta": meta}) + "\\n")
    for r in results:
      f.write(json.dumps(r) + "\\n")
"""


def run_git_snapshot(
  git_ref: str,
  dataset_path: Path,
  config: BenchConfig,
  undecided_mode: str = "both",
  time_limit_sec: float = 15.0,
  jobs: int = 1,
  out_path: Path | None = None,
) -> tuple[Path, dict[str, Any], list[dict[str, Any]]]:
  """Run a benchmark configuration against an older git commit/tag via a temporary git worktree."""
  rev_proc = subprocess.run(
    ["git", "rev-parse", "--short", git_ref],
    cwd=ROOT_DIR,
    capture_output=True,
    text=True,
    check=True,
  )
  short_sha = rev_proc.stdout.strip()
  timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
  dataset_name = dataset_path.stem.removesuffix(".jsonl")
  if out_path is None:
    out_path = RESULTS_DIR / f"{timestamp}_{short_sha}_{dataset_name}_{config.name}.jsonl.gz"
  out_path.parent.mkdir(parents=True, exist_ok=True)

  tmpdir = Path(tempfile.mkdtemp(prefix=f"bb_bench_{short_sha}_", dir="/tmp"))
  worktree_dir = tmpdir / "worktree"
  worktree_dir.mkdir(parents=True, exist_ok=True)
  worker_file = tmpdir / "snapshot_worker.py"
  tar_file = tmpdir / "snapshot.tar"
  try:
    with open(tar_file, "wb") as tf:
      subprocess.run(
        ["git", "archive", "--format=tar", short_sha, "Code"],
        cwd=ROOT_DIR,
        check=True,
        stdout=tf,
      )
    with tarfile.open(tar_file, "r") as tar:
      tar.extractall(path=worktree_dir, filter="data")
    worker_file.write_text(_SNAPSHOT_WORKER_SCRIPT, encoding="utf-8")
    cmd = [
      sys.executable,
      str(worker_file),
      str(worktree_dir / "Code"),
      str(dataset_path.resolve()),
      json.dumps(config.to_dict()),
      str(out_path.resolve()),
      undecided_mode,
      str(time_limit_sec),
      str(jobs),
      short_sha,
    ]
    subprocess.run(cmd, check=True)
  finally:
    shutil.rmtree(tmpdir, ignore_errors=True)

  meta, results = load_run_results(out_path)
  return out_path, meta, results


def _geomean(values: list[float]) -> float:
  if not values:
    return 0.0
  log_sum = sum(math.log(max(v, 1.0)) for v in values)
  return math.exp(log_sum / len(values))


def compare_runs(
  baseline_meta: dict[str, Any],
  baseline_results: list[dict[str, Any]],
  candidates: list[tuple[dict[str, Any], list[dict[str, Any]]]],
) -> tuple[dict[str, Any], str]:
  """Compare one or more candidate runs against a baseline run across all 3 pillars.

  Returns (structured_summary_dict, markdown_report).
  """
  base_name = baseline_meta.get("config_name", "baseline")
  base_by_tm = {r["tm"]: r for r in baseline_results}

  all_runs = [(base_name, baseline_meta, base_by_tm)]
  for c_meta, c_res in candidates:
    c_name = c_meta.get("config_name", "candidate")
    all_runs.append((c_name, c_meta, {r["tm"]: r for r in c_res}))

  lines: list[str] = []
  lines.append("# Macro Simulator Benchmark & Regression Report\n")
  lines.append(f"- **Baseline**: `{base_name}` (git: `{baseline_meta.get('git_sha', 'unknown')}`)")
  lines.append(f"- **Total TMs**: `{len(baseline_results):_}`\n")

  # =========================================================================
  # PILLAR 1: CORRECTNESS
  # =========================================================================
  lines.append("## 1. Correctness Checks\n")
  correctness_errors: list[str] = []

  for run_name, _, run_map in all_runs:
    for tm_str, res in run_map.items():
      base_res = base_by_tm.get(tm_str)
      cat = res.get("category", "unknown")
      status = res["status"]

      # 1a. Exceptions
      if res.get("threw_exception"):
        correctness_errors.append(f"[{run_name}] Exception on {res['name']} ({tm_str}): {res.get('exception_str')}")

      # 1b. Ground-truth category contradiction
      if cat == "halt" and status == "inf":
        correctness_errors.append(
          f"[{run_name}] Ground-truth HALT machine {res['name']} ({tm_str}) proved INF ({res['reason']})!"
        )
      elif cat == "inf" and status == "halt":
        correctness_errors.append(f"[{run_name}] Ground-truth INF machine {res['name']} ({tm_str}) decided HALT!")

      # 1c. Cross-run contradiction against baseline (Halt <-> Inf or halt_score mismatch)
      if base_res and run_name != base_name:
        b_status = base_res["status"]
        if (b_status == "halt" and status == "inf") or (b_status == "inf" and status == "halt"):
          correctness_errors.append(
            f"[{run_name} vs {base_name}] Decision flip on {res['name']} ({tm_str}): "
            f"{base_name}={b_status} vs {run_name}={status} ({res['reason']})"
          )
        elif b_status == "halt" and status == "halt":
          if not scores_consistent(base_res["halt_score"], res["halt_score"]):
            correctness_errors.append(
              f"[{run_name} vs {base_name}] Halt score mismatch on {res['name']} ({tm_str}): "
              f"{base_name}={base_res['halt_score'].get('str')} vs {run_name}={res['halt_score'].get('str')}"
            )

  if not correctness_errors:
    lines.append(
      "PASS: **0 correctness errors** "
      "(no `Halt <-> Inf` flips, ground-truth contradictions, score mismatches, or exceptions).\n"
    )
  else:
    lines.append(f"FAIL: **{len(correctness_errors)} correctness errors detected!**\n")
    for err in correctness_errors[:50]:
      lines.append(f"- {err}")
    if len(correctness_errors) > 50:
      lines.append(f"- ... and {len(correctness_errors) - 50} more errors.")
    lines.append("")

  # =========================================================================
  # PILLAR 2: COVERAGE (DECIDABILITY & RULE LEVELS)
  # =========================================================================
  lines.append("## 2. Coverage (Decidability)\n")
  lines.append(
    "| Configuration | Decided Total | Halt | Inf Total | Inf: Proof | "
    "Inf: Chain | Inf: Macro | Undecided | +New vs Base | -Lost vs Base | Max Rule Lvl |"
  )
  lines.append("| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")

  coverage_summary: dict[str, Any] = {}
  newly_decided_details: list[str] = []
  for run_name, _, run_map in all_runs:
    n_halt = sum(1 for r in run_map.values() if r["status"] == "halt")
    n_inf = sum(1 for r in run_map.values() if r["status"] == "inf")
    n_inf_proof = sum(1 for r in run_map.values() if r["status"] == "inf" and r["reason"] == "INF_PROOF_SYSTEM")
    n_inf_chain = sum(1 for r in run_map.values() if r["status"] == "inf" and r["reason"] == "INF_CHAIN_STEP")
    n_inf_macro = sum(1 for r in run_map.values() if r["status"] == "inf" and r["reason"] == "INF_MACRO_STEP")
    n_unk = sum(1 for r in run_map.values() if r["status"] == "unknown")
    max_lvl = max((r.get("max_rule_level", 0) for r in run_map.values()), default=0)

    newly_decided = []
    lost_decisions = []
    for tm_str, r in run_map.items():
      br = base_by_tm.get(tm_str)
      if not br:
        continue
      b_dec = br["status"] in ("halt", "inf")
      c_dec = r["status"] in ("halt", "inf")
      if c_dec and not b_dec:
        newly_decided.append(r["name"])
        newly_decided_details.append(
          f"- **[{run_name}]** `{r['name']}` (`{tm_str}`, category=`{r.get('category')}`) -> "
          f"**{r['status'].upper()}** (`{r['reason']}`, loops={r['total_loops']:_}, L{r.get('max_rule_level', 0)})"
        )
      elif b_dec and not c_dec:
        lost_decisions.append(r["name"])

    coverage_summary[run_name] = {
      "decided": n_halt + n_inf,
      "halt": n_halt,
      "inf": n_inf,
      "unknown": n_unk,
      "newly_decided": newly_decided,
      "lost_decisions": lost_decisions,
    }

    lines.append(
      f"| `{run_name}` | **{n_halt + n_inf:_}** | {n_halt:_} | {n_inf:_} | "
      f"{n_inf_proof:_} | {n_inf_chain:_} | {n_inf_macro:_} | {n_unk:_} | "
      f"+{len(newly_decided):_} | -{len(lost_decisions):_} | L{max_lvl} |"
    )
  lines.append("")
  if newly_decided_details:
    lines.append("### Newly Decided TMs (vs Baseline)\n")
    for detail in newly_decided_details[:30]:
      lines.append(detail)
    if len(newly_decided_details) > 30:
      lines.append(f"- ... and {len(newly_decided_details) - 30} more newly decided TMs.")
    lines.append("")

  # =========================================================================
  # PILLAR 3: RUNTIME & UNDECIDED PROGRESS
  # =========================================================================
  lines.append("## 3. Runtime & Progress\n")
  lines.append("### 3a. Decided TMs Runtime (vs Baseline Common Decided)\n")
  lines.append(
    "| Configuration | Common Decided | Sim Time (s) | Eval Time (s) | "
    "Geomean Sim (ms) | Speedup vs Base | Total Loops (`sim+prover`) |"
  )
  lines.append("| :--- | ---: | ---: | ---: | ---: | ---: | ---: |")

  for run_name, _, run_map in all_runs:
    common_tms = [
      tm_str
      for tm_str, br in base_by_tm.items()
      if br["status"] in ("halt", "inf") and run_map.get(tm_str, {}).get("status") in ("halt", "inf")
    ]
    if not common_tms:
      lines.append(f"| `{run_name}` | 0 | N/A | N/A | N/A | N/A | N/A |")
      continue

    base_sim_us = sum(base_by_tm[t]["sim_time_us"] for t in common_tms)
    cand_sim_us = sum(run_map[t]["sim_time_us"] for t in common_tms)
    cand_eval_us = sum(run_map[t]["eval_time_us"] for t in common_tms)
    cand_geomean_ms = _geomean([run_map[t]["sim_time_us"] for t in common_tms]) / 1000.0
    cand_loops = sum(run_map[t]["total_loops"] for t in common_tms)
    speedup = (base_sim_us / cand_sim_us) if cand_sim_us > 0 else 1.0

    lines.append(
      f"| `{run_name}` | {len(common_tms):_} | {cand_sim_us / 1e6:.2f}s | {cand_eval_us / 1e6:.2f}s | "
      f"{cand_geomean_ms:.2f}ms | {speedup:.2f}x | {cand_loops:_} |"
    )
  lines.append("")

  lines.append("### 3b. Undecided TMs Progress & Milestone Runtime\n")
  lines.append(
    "| Configuration | Undecided Count | Reached Target Span | "
    "Common Milestone Time (s) | Common Milestone Loops | Final Max-Span vs Base (`> / = / <`) |"
  )
  lines.append("| :--- | ---: | ---: | ---: | ---: | :---: |")

  for run_name, _, run_map in all_runs:
    unk_tms = [
      tm_str
      for tm_str, br in base_by_tm.items()
      if br["status"] == "unknown" and run_map.get(tm_str, {}).get("status") == "unknown"
    ]
    if not unk_tms:
      lines.append(f"| `{run_name}` | 0 | N/A | N/A | N/A | N/A |")
      continue

    reached = [t for t in unk_tms if run_map[t].get("milestone_reached")]
    common_ms = [t for t in unk_tms if base_by_tm[t].get("milestone_reached") and run_map[t].get("milestone_reached")]
    ms_time_s = sum(run_map[t]["milestone_time_us"] or 0 for t in common_ms) / 1e6
    ms_loops = sum(run_map[t]["milestone_loops"] or 0 for t in common_ms)

    span_gt = 0
    span_eq = 0
    span_lt = 0
    for t in unk_tms:
      cmp_val = compare_encoded_values(run_map[t]["max_span"], base_by_tm[t]["max_span"])
      if cmp_val is not None:
        if cmp_val > 0:
          span_gt += 1
        elif cmp_val < 0:
          span_lt += 1
        else:
          span_eq += 1

    pct = (100.0 * len(reached) / len(unk_tms)) if unk_tms else 0.0
    lines.append(
      f"| `{run_name}` | {len(unk_tms):_} | {len(reached):_}/{len(unk_tms):_} ({pct:.1f}%) | "
      f"{ms_time_s:.2f}s (n={len(common_ms)}) | {ms_loops:_} | "
      f"+{span_gt} / ={span_eq} / -{span_lt} |"
    )
  lines.append("")

  report_md = "\n".join(lines)
  summary = {
    "correctness_passed": len(correctness_errors) == 0,
    "correctness_errors": correctness_errors,
    "coverage": coverage_summary,
  }
  return summary, report_md


def _resolve_config_names(configs_arg: str | None, group_arg: str | None) -> list[BenchConfig]:
  names: list[str] = []
  if group_arg:
    for g in group_arg.split(","):
      g = g.strip()
      if g not in PRESET_GROUPS:
        raise ValueError(f"Unknown preset group '{g}'. Choices: {list(PRESET_GROUPS.keys())}")
      for n in PRESET_GROUPS[g]:
        if n not in names:
          names.append(n)
  if configs_arg:
    for n in configs_arg.split(","):
      n = n.strip()
      if n not in CONFIG_PRESETS:
        raise ValueError(f"Unknown config preset '{n}'. Choices: {list(CONFIG_PRESETS.keys())}")
      if n not in names:
        names.append(n)
  if not names:
    names = ["default", "all_on"]
  return [CONFIG_PRESETS[n] for n in names]


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description="Macro Simulator Regression & Benchmark System")
  subparsers = parser.add_subparsers(dest="subcommand", required=True)

  default_jobs = max(1, (os.cpu_count() or 2) - 1)
  # Subcommand: run
  p_run = subparsers.add_parser("run", help="Run benchmark configurations or git snapshots on a dataset")
  p_run.add_argument("--dataset", default="fast", help="Dataset name ('fast', 'full') or path to .jsonl")
  p_run.add_argument("--config", help=f"Comma-separated config names: {list(CONFIG_PRESETS.keys())}")
  p_run.add_argument("--preset-group", help=f"Preset group: {list(PRESET_GROUPS.keys())}")
  p_run.add_argument("--git-ref", help="Optional git commit/tag/branch to benchmark via git worktree")
  p_run.add_argument("--undecided-mode", choices=["both", "milestone", "full"], default="both")
  p_run.add_argument("--max-loops", type=int, default=None, help="Override per-TM max_loops")
  p_run.add_argument("--time-limit", type=float, default=15.0, help="Per-TM timeout in seconds [default: 15.0]")
  p_run.add_argument("-j", "--jobs", type=int, default=default_jobs, help="Parallel worker processes")
  p_run.add_argument("--out", type=Path, help="Explicit output .jsonl.gz path (when running a single config)")

  # Subcommand: compare
  p_cmp = subparsers.add_parser("compare", help="Compare saved benchmark result files")
  p_cmp.add_argument("baseline", type=Path, help="Baseline result .jsonl[.gz] file")
  p_cmp.add_argument("candidates", nargs="+", type=Path, help="Candidate result .jsonl[.gz] file(s)")
  p_cmp.add_argument("--markdown", type=Path, help="Optional path to save Markdown report")

  # Subcommand: matrix
  p_mat = subparsers.add_parser("matrix", help="Run multiple configs/snapshots and compare side-by-side")
  p_mat.add_argument("--dataset", default="fast", help="Dataset name ('fast', 'full') or path to .jsonl")
  p_mat.add_argument("--config", help="Comma-separated config names")
  p_mat.add_argument(
    "--preset-group", default="core", help=f"Preset group [default: core]: {list(PRESET_GROUPS.keys())}"
  )
  p_mat.add_argument("--git-refs", help="Optional comma-separated git refs to include in comparison")
  p_mat.add_argument("--baseline-config", default=None, help="Which config to use as baseline (defaults to first)")
  p_mat.add_argument("--undecided-mode", choices=["both", "milestone", "full"], default="both")
  p_mat.add_argument("--max-loops", type=int, default=None, help="Override per-TM max_loops")
  p_mat.add_argument("--time-limit", type=float, default=15.0, help="Per-TM timeout in seconds")
  p_mat.add_argument("-j", "--jobs", type=int, default=default_jobs, help="Parallel worker processes")
  p_mat.add_argument("--markdown", type=Path, help="Optional path to save Markdown report")

  args = parser.parse_args(argv)

  if args.subcommand == "run":
    dataset_path, entries = load_dataset(args.dataset)
    dataset_name = dataset_path.stem.removesuffix(".jsonl")
    configs = _resolve_config_names(args.config, args.preset_group)
    for cfg in configs:
      if args.git_ref:
        run_git_snapshot(
          git_ref=args.git_ref,
          dataset_path=dataset_path,
          config=cfg,
          undecided_mode=args.undecided_mode,
          time_limit_sec=args.time_limit,
          jobs=args.jobs,
          out_path=args.out if len(configs) == 1 else None,
        )
      else:
        run_benchmark_config(
          entries=entries,
          config=cfg,
          dataset_name=dataset_name,
          undecided_mode=args.undecided_mode,
          max_loops_override=args.max_loops,
          time_limit_sec=args.time_limit,
          jobs=args.jobs,
          out_path=args.out if len(configs) == 1 else None,
        )
    return 0

  elif args.subcommand == "compare":
    base_meta, base_res = load_run_results(args.baseline)
    cands = [load_run_results(p) for p in args.candidates]
    summary, report_md = compare_runs(base_meta, base_res, cands)
    print(report_md)
    if args.markdown:
      args.markdown.parent.mkdir(parents=True, exist_ok=True)
      args.markdown.write_text(report_md, encoding="utf-8")
    return 0 if summary["correctness_passed"] else 1

  elif args.subcommand == "matrix":
    dataset_path, entries = load_dataset(args.dataset)
    dataset_name = dataset_path.stem.removesuffix(".jsonl")
    configs = _resolve_config_names(args.config, args.preset_group)

    runs: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    for cfg in configs:
      print(f"Running config '{cfg.name}' on {len(entries)} TMs (jobs={args.jobs})...")
      _, meta, res = run_benchmark_config(
        entries=entries,
        config=cfg,
        dataset_name=dataset_name,
        undecided_mode=args.undecided_mode,
        max_loops_override=args.max_loops,
        time_limit_sec=args.time_limit,
        jobs=args.jobs,
      )
      runs.append((meta, res))

    if args.git_refs:
      snap_cfg = configs[-1]
      for ref in args.git_refs.split(","):
        ref = ref.strip()
        if ref:
          print(f"Running git snapshot '{ref}' with config '{snap_cfg.name}'...")
          _, meta, res = run_git_snapshot(
            git_ref=ref,
            dataset_path=dataset_path,
            config=snap_cfg,
            undecided_mode=args.undecided_mode,
            time_limit_sec=args.time_limit,
            jobs=args.jobs,
          )
          runs.append((meta, res))

    base_idx = 0
    if args.baseline_config:
      for i, (m, _) in enumerate(runs):
        if m.get("config_name") == args.baseline_config:
          base_idx = i
          break

    base_meta, base_res = runs[base_idx]
    cand_runs = [r for i, r in enumerate(runs) if i != base_idx]
    summary, report_md = compare_runs(base_meta, base_res, cand_runs)
    print("\n" + report_md)
    if args.markdown:
      args.markdown.parent.mkdir(parents=True, exist_ok=True)
      args.markdown.write_text(report_md, encoding="utf-8")
      print(f"Saved Markdown report to {args.markdown}")
    return 0 if summary["correctness_passed"] else 1

  return 0


if __name__ == "__main__":
  sys.exit(main())
