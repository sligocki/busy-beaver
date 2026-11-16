#!/usr/bin/env python3
"""
Dataset curation pipeline and code/behavioral coverage profiler for the
Macro Simulator regression & benchmark testing system.

Features:
1. Ingests candidate TMs from:
   - Green.py (even states -> block_size=1, odd states -> block_size=2)
   - Machines/* (champions, bb, bbi, beep, lin_recur_period, Lafitte.Papazian)
   - top_level_TMs.txt
   - holdouts/ (BB6_holdouts_608, 3x3_holdout_6, BB2x5_Rocq_holdouts_37,
     BLC_holdouts, 2x6_holdouts_412086.txt.zip, 7x2_holdouts_15743264.txt.zip)
   - holdouts/BB2..BB5_verified_enumeration_augmented.csv[.gz]
2. Resolves and verifies a fixed block_size for every TM so that Block_Finder
   does not run during benchmarks, and guarantees all included Halters halt
   with their assigned block_size.
3. Profiles per-TM code coverage (lines + branches in Macro/ and math modules)
   using Python 3.14's sys.monitoring alongside behavioral Proof_System tags.
4. Uses weighted greedy k-set-cover + stratified sampling to select diverse,
   non-redundant 'fast' and 'full' benchmark suites.
"""

from __future__ import annotations

import argparse
import collections
import csv
from dataclasses import dataclass
import json
import math
import optparse
import os
from pathlib import Path
import random
import re
import sys
import time
from typing import Any

from Benchmark import (
  CONFIG_PRESETS,
  DATASETS_DIR,
  ROOT_DIR,
  load_dataset,
  run_single_tm,
)
import Green
import IO
import io_pb2
from Macro import Block_Finder, Simulator, Turing_Machine


# Modules in Code/ whose line and branch execution we track for coverage diversity.
TARGET_COVERAGE_MODULES = frozenset(
  {
    "Simulator.py",
    "Proof_System.py",
    "Tape.py",
    "Turing_Machine.py",
    "Rule_Func.py",
    "Algebraic_Expression.py",
    "Exp_Int.py",
    "Iterated_Expression.py",
    "NatExpr.py",
    "Big_Interval.py",
  }
)

# Explicit block_size overrides for TMs where Block_Finder heuristics are suboptimal.
KNOWN_BLOCK_SIZES: dict[str, int] = {
  "Machines/7x2-a11-Pavel": 6,
  "1RB0RA_1LC1LF_1RD0LB_1RA1LE_1RZ0LC_1RG1LD_0RG0RF": 6,
  "Machines/7x2-a19": 6,
  "1RB0RG_1RC1RB_0RD1RZ_0LE0LD_0LF1LE_1RA1LF_1LC0RB": 6,
  "Machines/7x2-Wythagoras": 6,
  "Machines/2x6-t70": 2,
  "1RB2LA1RA4LA5RA0LB_1LA3RA2RB1RZ3RB4LA": 2,
  "Machines/2x6-e9866": 2,
  "Machines/2x6-p3": 4,
  "Machines/2x6-t24": 2,
  "Machines/2x6-t91": 4,
  "Machines/2x5-e38033": 2,
  "Machines/3x3-e17": 1,
  "Machines/3x3-Surprise": 8,
  "Machines/3x4-a14": 2,
  "1RB3LB1RZ2RA_2LC3RB1LC2RA_3RB1LB3LC2RC": 2,
  "Machines/3x4-t2048": 2,
  "Machines/4x3-e12068": 2,
  "Machines/4x3-e14072": 2,
  "Machines/4x3-e1426": 2,
  "Machines/6x2-e1762": 2,
  "Machines/6x2-e2879": 4,
  "Machines/6x2-e36534-Pavel": 6,
  "Machines/6x2-e646M-Pavel": 2,
  "Machines/6x2-e78913": 4,
  "Machines/6x2-q": 3,
  "Machines/6x2-r": 2,
  "Machines/6x2-t5": 3,
  "Machines/6x2-t15-Pavel": 3,
  "Machines/Lafitte.Papazian.complex:0": 1,
  "Machines/Lafitte.Papazian.complex:1": 1,
  "Machines/Lafitte.Papazian.complex:3": 1,
  "Machines/Lafitte.Papazian.complex:7": 2,
  "Machines/Lafitte.Papazian.peculiar:0": 4,
  "Machines/Lafitte.Papazian.peculiar:1": 2,
}

# Known exact halting total_loops for known halters (or None if > 1,000,000 loops).
# Fast halters (<= ~250k loops / <= ~2.5s) use a max_loops budget above their halt_loops
# so they halt during normal benchmark runs; ultra-long halters (> 250k loops) keep
# category="halt" and halt_loops recorded, while running with a fast milestone budget
# (baseline_status="unknown") during normal benchmarks.
KNOWN_HALT_LOOPS: dict[str, int | None] = {
  "Green-6": 54,
  "Green-7": 278,
  "Green-8": 144,
  "Green-9": 1_641,
  "Green-10": 333,
  "Green-11": 5_156,
  "Green-12": 720,
  "Green-13": 22_302,
  "Green-14": 1_848,
  "Green-15": 124_304,
  "Green-16": 4_818,
  "Green-17": None,  # > 210,000 loops
  "Green-18": 12_606,
  "Green-19": None,  # > 210,000 loops
  "Green-20": 33_006,
  "Machines/2x5-e704": 29_518,
  "Machines/2x6-e9866": 787,
  "Machines/2x6-p3": 10_695,
  "Machines/2x6-t70": 10_498,
  "Machines/2x6-t91": 35_011,
  "Machines/3x3-Surprise": 18_039,
  "Machines/3x3-e17": 1_156,
  "Machines/3x4-t2048": 883,
  "Machines/4x3-e12068": 499_536,
  "Machines/4x3-e14072": 583_281,
  "Machines/4x3-e1426": 75_726,
  "Machines/6x2-e1762": 49_563,
  "Machines/6x2-e2879": 207_138,
  "Machines/6x2-e36534-Pavel": 3_401,
  "Machines/6x2-e646M-Pavel": 312,
  "Machines/6x2-e78913": 1_570,
  "Machines/6x2-n": 14_798,
  "Machines/6x2-p": 8_628,
  "Machines/6x2-q": 796,
  "Machines/6x2-r": 69_008,
  "Machines/6x2-t15-Pavel": 2_110,
  "Machines/6x2-t5": 1_545,
  "Machines/7x2-Wythagoras": 8_166,
  "Machines/2x5-e38033": None,  # > 350,000 loops
  "Machines/2x6-t24": None,  # > 22,000 loops (>7.5s ExpInt tower evaluation)
  "Machines/3x4-a14": None,  # > 100,000 loops
  "Machines/7x2-a11-Pavel": None,  # > 200,000 loops
  "Machines/7x2-a19": None,  # > 200,000 loops
}

# Known special per-TM parameter overrides (e.g. max_steps_in_backsymbol or max_loops).
KNOWN_PARAM_OVERRIDES: dict[str, dict[str, int]] = {
  "Green-13": {"max_loops": 25_000, "tape_limit": 100},
  "Green-15": {"max_loops": 130_000, "tape_limit": 100},
  "Green-20": {"max_loops": 36_000, "tape_limit": 100},
  "Machines/3x4-a14": {"max_steps_in_backsymbol": 250, "max_loops": 25_000},
  "1RB3LB1RZ2RA_2LC3RB1LC2RA_3RB1LB3LC2RC": {"max_steps_in_backsymbol": 250, "max_loops": 25_000},
  "Machines/2x5-e704": {"max_loops": 35_000},
  "Machines/2x6-p3": {"max_loops": 15_000},
  "Machines/2x6-t70": {"max_loops": 15_000},
  "Machines/2x6-t91": {"max_loops": 40_000, "tape_limit": 100},
  "Machines/3x3-Surprise": {"max_loops": 25_000},
  "Machines/4x3-e1426": {"max_loops": 80_000, "tape_limit": 150},
  "Machines/6x2-e1762": {"max_loops": 55_000, "tape_limit": 150},
  "Machines/6x2-e2879": {"max_loops": 220_000, "tape_limit": 250},
  "Machines/6x2-n": {"max_loops": 20_000},
  "Machines/6x2-r": {"max_loops": 75_000},
  "Machines/7x2-Wythagoras": {"max_loops": 12_000},
  # Ultra-long halters kept at fast milestone loop budgets so they don't bottleneck the suite:
  "Machines/4x3-e12068": {"max_loops": 20_000, "tape_limit": 150},
  "Machines/4x3-e14072": {"max_loops": 20_000, "tape_limit": 150},
  "Machines/2x5-e38033": {"max_loops": 10_000, "tape_limit": 100},
  "Machines/2x6-t24": {"max_loops": 2_500, "tape_limit": 100},
  "Machines/7x2-a11-Pavel": {"max_loops": 30_000, "tape_limit": 100},
  "Machines/7x2-a19": {"max_loops": 30_000, "tape_limit": 100},
}

# Ground-truth categories ("halt", "inf", "holdout") for Machines/*
KNOWN_MACHINES_CATEGORIES: dict[str, str] = {
  "Machines/2x2-Counter": "inf",
  "Machines/2x2-Tree": "inf",
  "Machines/2x3-Wolfram_Prize": "inf",
  "Machines/2x5-Hydra": "holdout",
  "Machines/2x5-e38033": "halt",
  "Machines/2x6-t24": "halt",
  "Machines/2x6-t91": "halt",
  "Machines/3x2-LR-9-10": "inf",
  "Machines/3x3-Bigfoot": "holdout",
  "Machines/3x4-a14": "halt",
  "Machines/4x2-LR-158491-17620": "inf",
  "Machines/4x2-LR-28812-5588": "inf",
  "Machines/4x2-LR-7170-29117": "inf",
  "Machines/4x2-LR-73906-88381": "inf",
  "Machines/4x3-e12068": "halt",
  "Machines/4x3-e14072": "halt",
  "Machines/5x2-Chaos": "inf",
  "Machines/6x2-Antihydra": "holdout",
  "Machines/6x2-e2879": "halt",
  "Machines/7x2-Wythagoras": "halt",
  "Machines/7x2-a11-Pavel": "halt",
  "Machines/7x2-a19": "halt",
  "Machines/Lafitte.Papazian.complex:0": "halt",
  "Machines/Lafitte.Papazian.complex:1": "inf",
  "Machines/Lafitte.Papazian.complex:2": "inf",
  "Machines/Lafitte.Papazian.complex:3": "inf",
  "Machines/Lafitte.Papazian.complex:4": "inf",
  "Machines/Lafitte.Papazian.complex:5": "inf",
  "Machines/Lafitte.Papazian.complex:6": "inf",
  "Machines/Lafitte.Papazian.complex:7": "inf",
  "Machines/Lafitte.Papazian.peculiar:0": "inf",
  "Machines/Lafitte.Papazian.peculiar:1": "inf",
  "Machines/Lafitte.Papazian.peculiar:2": "inf",
}

# Set of known halters that are intentionally configured with a milestone loop budget
# smaller than their full halting loop count (so baseline_status == "unknown" is expected).
MILESTONE_HALTERS: frozenset[str] = frozenset(
  {
    "Green-17",
    "Green-19",
    "Machines/2x5-e38033",
    "Machines/2x6-t24",
    "Machines/3x4-a14",
    "Machines/4x3-e12068",
    "Machines/4x3-e14072",
    "Machines/7x2-a11-Pavel",
    "Machines/7x2-a19",
  }
)


STD_TM_RE = re.compile(r"^[0-9LRS_A-Z-]+$")


def is_valid_std_tm(s: str) -> bool:
  if not s or "_" not in s or not STD_TM_RE.match(s):
    return False
  try:
    IO.parse_tm(s)
    return True
  except Exception:
    return False


@dataclass
class CandidateTM:
  tm: str
  name: str
  source: str
  category: str  # "halt" | "inf" | "holdout" | "unknown"
  mandatory: bool = False
  block_size: int | None = None
  max_loops: int = 10_000
  tape_limit: int = 50
  max_steps_in_block: int = 100_000
  max_steps_in_backsymbol: int = 1_000


class CoverageProfiler:
  """Lightweight per-TM line and branch coverage collector using Python 3.14 sys.monitoring."""

  def __init__(self, tool_id: int = sys.monitoring.PROFILER_ID):
    self.tool_id = tool_id
    self.features: set[tuple[Any, ...]] = set()
    self._code_to_mod: dict[Any, str | None] = {}

  def _resolve_mod(self, code) -> str | None:
    if code in self._code_to_mod:
      return self._code_to_mod[code]
    fname = getattr(code, "co_filename", "")
    bname = os.path.basename(fname)
    if bname in TARGET_COVERAGE_MODULES:
      self._code_to_mod[code] = bname
      return bname
    self._code_to_mod[code] = None
    return None

  def _on_line(self, code, line_number: int):
    mod = self._resolve_mod(code)
    if mod is not None:
      self.features.add(("line", mod, line_number))
      return sys.monitoring.DISABLE
    return sys.monitoring.DISABLE

  def _on_branch(self, code, instruction_offset: int, destination_offset: int):
    mod = self._resolve_mod(code)
    if mod is not None:
      self.features.add(("branch", mod, instruction_offset, destination_offset))
      return sys.monitoring.DISABLE
    return sys.monitoring.DISABLE

  def __enter__(self):
    self.features.clear()
    try:
      sys.monitoring.use_tool_id(self.tool_id, "bb_bench_coverage")
    except ValueError:
      sys.monitoring.free_tool_id(self.tool_id)
      sys.monitoring.use_tool_id(self.tool_id, "bb_bench_coverage")
    sys.monitoring.register_callback(self.tool_id, sys.monitoring.events.LINE, self._on_line)
    sys.monitoring.register_callback(self.tool_id, sys.monitoring.events.BRANCH, self._on_branch)
    sys.monitoring.set_events(
      self.tool_id,
      sys.monitoring.events.LINE | sys.monitoring.events.BRANCH,
    )
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    sys.monitoring.set_events(self.tool_id, 0)
    sys.monitoring.register_callback(self.tool_id, sys.monitoring.events.LINE, None)
    sys.monitoring.register_callback(self.tool_id, sys.monitoring.events.BRANCH, None)
    sys.monitoring.free_tool_id(self.tool_id)
    sys.monitoring.restart_events()


def _span_tier_tag(enc_span: dict[str, Any]) -> str:
  exact = enc_span.get("exact")
  if exact is not None:
    v = int(exact)
    if v < 100:
      return "span_<100"
    if v < 10_000:
      return "span_100..10k"
    if v < 10**6:
      return "span_10k..1M"
    return "span_1M..10^300"
  bi = enc_span.get("bi")
  if bi and bi[0]:
    low_args = bi[0]
    arrows = len(low_args) - 1
    top = low_args[-1]
    return f"span_arrow{arrows}_h{min(top, 10)}"
  return "span_unknown"


def extract_behavioral_features(cand: CandidateTM, run_res: dict[str, Any]) -> set[tuple[Any, ...]]:
  """Extract high-level Proof_System and simulator behavioral features from a run."""
  tm_obj = IO.parse_tm(cand.tm)
  dim_str = f"{tm_obj.num_states}x{tm_obj.num_symbols}"
  status = run_res["status"]
  reason = run_res["reason"]
  max_lvl = int(run_res.get("max_rule_level", 0))
  lvl_bucket = min(max_lvl, 5)
  span_tier = _span_tier_tag(run_res.get("max_span", {}))

  b_feats: set[tuple[Any, ...]] = {
    ("behav_outcome", status, reason),
    ("behav_class_outcome", dim_str, status),
    ("behav_max_level", lvl_bucket),
    ("behav_class_level", dim_str, lvl_bucket),
    ("behav_span_tier", status, span_tier),
    ("behav_source_cat", cand.source, cand.category),
  }
  if run_res.get("num_meta_diff_rules", 0) > 0:
    b_feats.add(("behav_rule_type", "meta_diff"))
  if run_res.get("num_linear_rules", 0) > 0:
    b_feats.add(("behav_rule_type", "linear"))
  if run_res.get("num_exponential_rules", 0) > 0:
    b_feats.add(("behav_rule_type", "exponential"))
  if run_res.get("num_gen_rules", 0) > 0:
    b_feats.add(("behav_rule_type", "general"))
  if run_res.get("num_collatz_rules", 0) > 0:
    b_feats.add(("behav_rule_type", "collatz"))

  for lvl_str in run_res.get("rules_by_level", {}):
    b_feats.add(("behav_ rule_level_present", min(int(lvl_str), 6)))

  return b_feats


def find_block_finder_candidates(tm: Turing_Machine.Simple_Machine) -> list[int]:
  """Run Block_Finder with fast and medium loop budgets to get candidate block sizes."""
  parser = optparse.OptionParser()
  Simulator.add_option_group(parser)
  Block_Finder.add_option_group(parser)
  opts, _ = parser.parse_args([])
  opts.verbose_block_finder = False

  cands: list[int] = []
  for bf_loops in (100, 1_000):
    bf_info = io_pb2.BlockFinderInfo()
    bf_info.parameters.compression_search_loops = bf_loops
    bf_info.parameters.mult_sim_loops = bf_loops
    bf_info.parameters.max_block_mult = 2
    bf_info.parameters.block_mult = 0
    bf_info.parameters.max_block_size = 50
    try:
      Block_Finder.block_finder(tm, opts, bf_info.parameters, bf_info.result)
      for b in (bf_info.result.best_block_size, bf_info.result.best_compression_block_size):
        if b and int(b) > 0 and int(b) not in cands:
          cands.append(int(b))
    except Exception:
      pass
  if not cands:
    cands.append(1)
  return cands


def resolve_block_size_and_profile(
  cand: CandidateTM,
  profile_coverage: bool = True,
  time_limit_sec: float = 5.0,
) -> tuple[dict[str, Any] | None, set[tuple[Any, ...]]]:
  """Determine a verified fixed block_size for `cand`, run baseline simulation, and collect coverage.

  For Halters (`cand.category == "halt"`), if the initial block_size fails to halt,
  sweeps alternative block sizes (and both `prover_4_meta_linear` and `all_on`)
  to guarantee that the chosen `block_size` actually halts the machine.
  """
  if cand.name in KNOWN_PARAM_OVERRIDES:
    overrides = KNOWN_PARAM_OVERRIDES[cand.name]
    cand.max_loops = overrides.get("max_loops", cand.max_loops)
    cand.tape_limit = overrides.get("tape_limit", cand.tape_limit)
    cand.max_steps_in_backsymbol = overrides.get("max_steps_in_backsymbol", cand.max_steps_in_backsymbol)
  elif cand.tm in KNOWN_PARAM_OVERRIDES:
    overrides = KNOWN_PARAM_OVERRIDES[cand.tm]
    cand.max_loops = overrides.get("max_loops", cand.max_loops)
    cand.tape_limit = overrides.get("tape_limit", cand.tape_limit)
    cand.max_steps_in_backsymbol = overrides.get("max_steps_in_backsymbol", cand.max_steps_in_backsymbol)

  tm_obj = IO.parse_tm(cand.tm)

  # 1. Determine candidate block sizes
  if cand.block_size is not None:
    bs_list = [cand.block_size]
  elif cand.name in KNOWN_BLOCK_SIZES:
    bs_list = [KNOWN_BLOCK_SIZES[cand.name]]
  elif cand.tm in KNOWN_BLOCK_SIZES:
    bs_list = [KNOWN_BLOCK_SIZES[cand.tm]]
  else:
    bs_list = find_block_finder_candidates(tm_obj)

  # If this is a known halter/inf or custom/champion, prepare fallback block sizes in case Block_Finder's pick fails
  if cand.block_size is None and (cand.category in ("halt", "inf") or cand.source in ("machines", "custom")):
    base_cands = list(bs_list)
    for b in base_cands:
      for mult in (2, 3, 4):
        if b * mult <= 24 and (b * mult) not in bs_list:
          bs_list.append(b * mult)
    for b in (1, 2, 3, 4, 5, 6, 8, 9, 10, 12):
      if b not in bs_list:
        bs_list.append(b)

  # We use prover_4_meta_linear (full config logging) as our primary reference config
  # because only_record_configs can skip mid-tape rules on some machines.
  ref_config = CONFIG_PRESETS["prover_4_meta_linear"].to_dict()

  chosen_bs = bs_list[0]
  chosen_res: dict[str, Any] | None = None

  for i, bs in enumerate(bs_list):
    entry_try = {
      "tm": cand.tm,
      "name": cand.name,
      "category": cand.category,
      "block_size": bs,
      "max_loops": cand.max_loops,
      "tape_limit": cand.tape_limit,
      "max_steps_in_block": cand.max_steps_in_block,
      "max_steps_in_backsymbol": cand.max_steps_in_backsymbol,
      "target_max_span_bi": None,
    }
    res = run_single_tm(
      entry_try,
      ref_config,
      undecided_mode="full",
      time_limit_sec=time_limit_sec if i == 0 else min(time_limit_sec, 2.5),
    )
    if chosen_res is None and not res.get("threw_exception"):
      chosen_bs = bs
      chosen_res = res

    if cand.category == "halt":
      if res["status"] == "halt":
        chosen_bs = bs
        chosen_res = res
        break
    elif cand.category == "inf":
      if res["status"] == "inf":
        chosen_bs = bs
        chosen_res = res
        break
    elif cand.source in ("machines", "custom") and cand.category == "unknown":
      # When evaluating a custom or champion TM without an explicit block_size,
      # prefer a block_size that decides (halt/inf) the machine if one exists.
      if res["status"] in ("halt", "inf"):
        chosen_bs = bs
        chosen_res = res
        break
    else:
      # For holdouts/unknowns, accept the first non-exception block_size from Block_Finder
      if not res.get("threw_exception"):
        chosen_bs = bs
        chosen_res = res
        break

  if chosen_res is None:
    return None, set()

  # Hard guarantee: if category == "halt" (and not an intentional ultra-long milestone halter),
  # it MUST halt with chosen_bs!
  is_milestone_halter = cand.name in MILESTONE_HALTERS or cand.tm in MILESTONE_HALTERS
  if cand.category == "halt" and not is_milestone_halter and chosen_res["status"] != "halt":
    return None, set()

  # Ensure every TM is categorized into strictly ("halt", "inf", "holdout") — never "unknown"
  final_category = cand.category
  if final_category == "unknown":
    if chosen_res["status"] in ("halt", "inf"):
      final_category = chosen_res["status"]
    else:
      final_category = "holdout"

  # Collect coverage under CoverageProfiler on the chosen block_size
  cov_features: set[tuple[Any, ...]] = set()
  if profile_coverage:
    entry_final = {
      "tm": cand.tm,
      "name": cand.name,
      "category": final_category,
      "block_size": chosen_bs,
      "max_loops": min(cand.max_loops, 20_000),
      "tape_limit": cand.tape_limit,
      "max_steps_in_block": cand.max_steps_in_block,
      "max_steps_in_backsymbol": cand.max_steps_in_backsymbol,
      "target_max_span_bi": None,
    }
    with CoverageProfiler() as prof:
      _ = run_single_tm(entry_final, ref_config, undecided_mode="full", time_limit_sec=3.0)
    cov_features = set(prof.features)

  cov_features |= extract_behavioral_features(cand, chosen_res)

  # Build dataset entry
  target_max_span_bi: list[int] | None = None
  if chosen_res["status"] == "unknown":
    span_bi = chosen_res.get("max_span", {}).get("bi")
    if span_bi and span_bi[0]:
      target_max_span_bi = list(span_bi[0])

  expected_score_exact = None
  expected_score_bi = None
  halt_loops: int | None = KNOWN_HALT_LOOPS.get(cand.name, KNOWN_HALT_LOOPS.get(cand.tm))
  if final_category == "halt" and chosen_res["status"] == "halt":
    expected_score_exact = chosen_res["halt_score"].get("exact")
    expected_score_bi = chosen_res["halt_score"].get("bi")
    halt_loops = chosen_res["total_loops"]

  dataset_entry = {
    "tm": cand.tm,
    "name": cand.name,
    "source": cand.source,
    "category": final_category,
    "mandatory": cand.mandatory,
    "block_size": chosen_bs,
    "max_loops": cand.max_loops,
    "tape_limit": cand.tape_limit,
    "max_steps_in_block": cand.max_steps_in_block,
    "max_steps_in_backsymbol": cand.max_steps_in_backsymbol,
    "halt_loops": halt_loops,
    "expected_score_exact": expected_score_exact,
    "expected_score_bi": expected_score_bi,
    "target_max_span_bi": target_max_span_bi,
    "baseline_status": chosen_res["status"],
    "baseline_reason": chosen_res["reason"],
    "baseline_max_level": chosen_res.get("max_rule_level", 0),
    "baseline_sim_time_us": chosen_res["sim_time_us"],
    "baseline_loops": chosen_res["total_loops"],
  }
  return dataset_entry, cov_features


# =============================================================================
# Candidate TM Source Loaders
# =============================================================================


def iter_green_candidates(max_states: int = 20) -> list[CandidateTM]:
  """Generate Green.py machines for even (-n1) and odd (-n2) states."""
  cands: list[CandidateTM] = []
  for n in range(6, max_states + 1):
    tm_str = Green.green_machine_str(n)
    is_even = n % 2 == 0
    block_size = 1 if is_even else 2
    cands.append(
      CandidateTM(
        tm=tm_str,
        name=f"Green-{n}",
        source="green",
        category="halt",
        mandatory=True,
        block_size=block_size,
        max_loops=20_000,
        tape_limit=100,
      )
    )
  return cands


def iter_machines_dir_candidates(rng: random.Random) -> list[CandidateTM]:
  """Load TMs from Machines/* and its subdirectories."""
  machines_dir = ROOT_DIR / "Machines"
  cands: list[CandidateTM] = []

  # 1. Top-level champion files in Machines/
  for p in sorted(machines_dir.iterdir()):
    if not p.is_file():
      continue
    if p.name in ("Goodstein.csv", "GTM64.old_format", "5x2-skelet-orig", "5x2-skelet") or p.name.endswith("-Green"):
      continue
    if p.name.startswith("Lafitte.Papazian"):
      with open(p, "rt", encoding="utf-8") as f:
        for idx, line in enumerate(f):
          tok = line.strip().split()[0] if line.strip() else ""
          if is_valid_std_tm(tok):
            lp_name = f"Machines/{p.name}:{idx}"
            cands.append(
              CandidateTM(
                tm=tok,
                name=lp_name,
                source="machines",
                category=KNOWN_MACHINES_CATEGORIES.get(lp_name, "holdout"),
                mandatory=True,
                block_size=KNOWN_BLOCK_SIZES.get(lp_name),
              )
            )
      continue
    if "Collatz" in p.name:
      continue

    with open(p, "rt", encoding="utf-8") as f:
      first_line = f.readline().strip()
    tok = first_line.split()[0] if first_line else ""
    if not is_valid_std_tm(tok):
      continue

    rel_name = f"Machines/{p.name}"
    cat = KNOWN_MACHINES_CATEGORIES.get(rel_name, "halt")
    cands.append(
      CandidateTM(
        tm=tok,
        name=rel_name,
        source="machines",
        category=cat,
        mandatory=True,
        block_size=KNOWN_BLOCK_SIZES.get(rel_name),
      )
    )

  # 2. Subdirectory: Machines/lin_recur_period/*
  lr_dir = machines_dir / "lin_recur_period"
  if lr_dir.is_dir():
    for p in sorted(lr_dir.iterdir()):
      if p.is_file():
        with open(p, "rt", encoding="utf-8") as f:
          for idx, line in enumerate(f):
            tok = line.strip().split()[0] if line.strip() else ""
            if is_valid_std_tm(tok):
              cands.append(
                CandidateTM(
                  tm=tok,
                  name=f"Machines/lin_recur_period/{p.name}:{idx}",
                  source="machines_lr",
                  category="inf",
                )
              )

  # 3. Subdirectory: Machines/bb/*.txt (Halters)
  bb_dir = machines_dir / "bb"
  if bb_dir.is_dir():
    for p in sorted(bb_dir.glob("*.txt")):
      with open(p, "rt", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
      # Take top 25 + random 25 from each file
      selected = lines[:25]
      if len(lines) > 25:
        selected += rng.sample(lines[25:], min(25, len(lines) - 25))
      for idx, line in enumerate(selected):
        tok = line.split()[0]
        if is_valid_std_tm(tok):
          cands.append(
            CandidateTM(
              tm=tok,
              name=f"Machines/bb/{p.stem}:{idx}",
              source="machines_bb",
              category="halt",
            )
          )

  return cands


def iter_top_level_candidates(max_count: int = 400, rng: random.Random | None = None) -> list[CandidateTM]:
  """Load complex TMs from top_level_TMs.txt."""
  path = ROOT_DIR / "top_level_TMs.txt"
  if not path.exists():
    return []
  with open(path, "rt", encoding="utf-8") as f:
    lines = [line.strip().split()[0] for line in f if line.strip()]
  valid = [(i, t) for i, t in enumerate(lines) if is_valid_std_tm(t)]
  if max_count and len(valid) > max_count and rng is not None:
    # Keep first 100 + sample rest
    valid = valid[:100] + rng.sample(valid[100:], max_count - 100)
  return [
    CandidateTM(
      tm=t,
      name=f"top_level:{i}",
      source="top_level",
      category="unknown",
      max_loops=10_000,
    )
    for i, t in valid
  ]


def _extract_tm_token_from_line(line: str) -> tuple[str | None, str]:
  """Handle both '1RB...' and '279 1RB...' (as in BB6_holdouts_608.txt)."""
  parts = line.strip().split()
  if not parts:
    return None, ""
  if is_valid_std_tm(parts[0]):
    return parts[0], ""
  if len(parts) >= 2 and is_valid_std_tm(parts[1]):
    return parts[1], parts[0]
  return None, ""


def iter_holdout_candidates(
  rng: random.Random,
  sample_2x6: int = 300,
  sample_7x2: int = 400,
) -> list[CandidateTM]:
  """Load TMs from holdouts/ files (small files in full, zipped large files sampled)."""
  holdouts_dir = ROOT_DIR / "holdouts"
  cands: list[CandidateTM] = []

  small_files = [
    ("3x3_holdout_6.txt", True),
    ("BB2x5_Rocq_holdouts_37.txt", True),
    ("BB6_holdouts_608.txt", False),
    ("BLC_holdouts.txt", False),
  ]
  for fname, is_mandatory in small_files:
    fpath = holdouts_dir / fname
    if not fpath.exists():
      continue
    with IO.Common.open_file(fpath, "rt") as f:
      for idx, line in enumerate(f):
        tm_tok, custom_id = _extract_tm_token_from_line(line)
        if tm_tok:
          tag = custom_id if custom_id else str(idx)
          cands.append(
            CandidateTM(
              tm=tm_tok,
              name=f"{fname.removesuffix('.txt')}:{tag}",
              source="holdout",
              category="holdout",
              mandatory=is_mandatory,
            )
          )

  # Reservoir / stride sampling from 2x6_holdouts_412086.txt.zip
  zip_2x6 = holdouts_dir / "2x6_holdouts_412086.txt.zip"
  if zip_2x6.exists() and sample_2x6 > 0:
    stride = max(1, 412_086 // sample_2x6)
    with IO.Common.open_file(zip_2x6, "rt") as f:
      for idx, line in enumerate(f):
        if idx % stride == 0:
          tm_tok, _ = _extract_tm_token_from_line(line)
          if tm_tok:
            cands.append(
              CandidateTM(
                tm=tm_tok,
                name=f"2x6_holdout:{idx}",
                source="holdout_2x6",
                category="holdout",
              )
            )
            if len([c for c in cands if c.source == "holdout_2x6"]) >= sample_2x6:
              break

  # Stride sampling from 7x2_holdouts_15743264.txt.zip (read prefix stream fast)
  zip_7x2 = holdouts_dir / "7x2_holdouts_15743264.txt.zip"
  if zip_7x2.exists() and sample_7x2 > 0:
    # Read first 200,000 lines with stride so dataset build takes seconds, not minutes
    stride = max(1, 200_000 // sample_7x2)
    with IO.Common.open_file(zip_7x2, "rt") as f:
      for idx, line in enumerate(f):
        if idx >= 200_000:
          break
        if idx % stride == 0:
          tm_tok, _ = _extract_tm_token_from_line(line)
          if tm_tok:
            cands.append(
              CandidateTM(
                tm=tm_tok,
                name=f"7x2_holdout:{idx}",
                source="holdout_7x2",
                category="holdout",
              )
            )
  return cands


def iter_verified_csv_candidates(
  max_per_decider: int = 40,
  max_high_halters: int = 150,
  max_rows_scan: int = 250_000,
) -> list[CandidateTM]:
  """Stream verified enumeration CSVs in holdouts/ to sample diverse Halters and Inf TMs by decider."""
  holdouts_dir = ROOT_DIR / "holdouts"
  csv_files = [
    "BB2_verified_enumeration_augmented.csv",
    "BB3_verified_enumeration_augmented.csv",
    "BB2x3_verified_enumeration_augmented.csv",
    "BB4_verified_enumeration_augmented.csv",
    "BB2x4_verified_enumeration_augmented.csv",
    "BB5_verified_enumeration_augmented.csv.gz",
  ]
  by_decider: dict[tuple[str, str, str], list[CandidateTM]] = collections.defaultdict(list)
  high_halters: list[tuple[int, CandidateTM]] = []

  for fname in csv_files:
    fpath = holdouts_dir / fname
    if not fpath.exists():
      continue
    prefix = fname.split("_")[0]
    with IO.Common.open_file(fpath, "rt") as f:
      reader = csv.DictReader(f)
      for idx, row in enumerate(reader):
        if idx >= max_rows_scan:
          break
        status = row.get("status", "").strip()
        if status not in ("halt", "nonhalt"):
          continue
        tm_str = row.get("machine_with_halt_transition", "").strip() or row.get("machine", "").strip()
        if not is_valid_std_tm(tm_str):
          continue
        decider = row.get("decider", "unknown").strip()
        cat = "halt" if status == "halt" else "inf"
        cand = CandidateTM(
          tm=tm_str,
          name=f"{prefix}:{idx}:{decider[:18]}",
          source=f"verified_{prefix}",
          category=cat,
        )
        if cat == "halt":
          steps = int(row.get("steps") or 0)
          if steps >= 500 and len(high_halters) < max_high_halters * 4:
            high_halters.append((steps, cand))
        key = (prefix, cat, decider)
        if len(by_decider[key]) < max_per_decider:
          by_decider[key].append(cand)

  high_halters.sort(key=lambda x: x[0], reverse=True)
  result: list[CandidateTM] = [c for _, c in high_halters[:max_high_halters]]
  seen_tms = {c.tm for c in result}
  for group in by_decider.values():
    for c in group:
      if c.tm not in seen_tms:
        seen_tms.add(c.tm)
        result.append(c)
  return result


# =============================================================================
# Greedy Set-Cover & Stratified Diversity Selection
# =============================================================================


def select_diverse_subset(
  profiled_items: list[tuple[dict[str, Any], set[tuple[Any, ...]]]],
  target_count: int,
  min_k_coverage: int = 3,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
  """Select up to `target_count` TMs maximizing code + behavioral coverage with k-redundancy.

  1. Includes all mandatory TMs first.
  2. Runs weighted greedy k-set-cover where rare features and behavioral features
     receive higher weights, normalized by sqrt(sim_time).
  3. Fills any remaining budget up to `target_count` via round-robin stratified sampling
     across (category, source, baseline_max_level).
  """
  if len(profiled_items) <= target_count:
    entries = [e for e, _ in profiled_items]
    all_feats = set().union(*(f for _, f in profiled_items)) if profiled_items else set()
    return entries, {"total_features": len(all_feats), "covered_features": len(all_feats)}

  # Compute global feature frequencies for inverse-frequency rarity weighting
  feat_freq: collections.Counter = collections.Counter()
  for _, feats in profiled_items:
    for f in feats:
      feat_freq[f] += 1

  feat_weight: dict[tuple[Any, ...], float] = {}
  for f, freq in feat_freq.items():
    is_behav = str(f[0]).startswith("behav_")
    base_w = 15.0 if is_behav else 1.0
    feat_weight[f] = base_w * (1.0 + 1.0 / max(1, freq))

  cov_counts: collections.Counter = collections.Counter()
  selected_indices: set[int] = set()
  selected_entries: list[dict[str, Any]] = []

  # Step 1: Add mandatory items
  for i, (entry, feats) in enumerate(profiled_items):
    if entry.get("mandatory"):
      selected_indices.add(i)
      selected_entries.append(entry)
      for f in feats:
        cov_counts[f] += 1

  # Step 2: Weighted greedy k-set-cover
  while len(selected_entries) < target_count:
    best_idx = -1
    best_score = 0.0
    for i, (entry, feats) in enumerate(profiled_items):
      if i in selected_indices:
        continue
      gain = sum(feat_weight[f] for f in feats if cov_counts[f] < min_k_coverage)
      if gain <= 0.0:
        continue
      time_ms = max(0.5, entry.get("baseline_sim_time_us", 1000) / 1000.0)
      score = gain / math.sqrt(time_ms)
      if score > best_score:
        best_score = score
        best_idx = i

    if best_idx == -1:
      break

    selected_indices.add(best_idx)
    entry, feats = profiled_items[best_idx]
    selected_entries.append(entry)
    for f in feats:
      cov_counts[f] += 1

  # Step 3: Stratified round-robin fill across (category, source, max_level)
  if len(selected_entries) < target_count:
    strata: dict[tuple[str, str, int], list[int]] = collections.defaultdict(list)
    for i, (entry, _) in enumerate(profiled_items):
      if i not in selected_indices:
        key = (entry["category"], entry["source"], int(entry.get("baseline_max_level", 0)))
        strata[key].append(i)

    # Sort each stratum to prefer higher rule levels and complex runs
    for key in strata:
      strata[key].sort(key=lambda idx: profiled_items[idx][0].get("baseline_loops", 0), reverse=True)

    stratum_keys = sorted(strata.keys())
    added = True
    while len(selected_entries) < target_count and added:
      added = False
      for k in stratum_keys:
        if strata[k] and len(selected_entries) < target_count:
          idx = strata[k].pop(0)
          selected_indices.add(idx)
          e, feats = profiled_items[idx]
          selected_entries.append(e)
          for f in feats:
            cov_counts[f] += 1
          added = True

  total_lines = sum(1 for f in feat_freq if f[0] == "line")
  covered_lines = sum(1 for f in cov_counts if f[0] == "line" and cov_counts[f] > 0)
  total_branches = sum(1 for f in feat_freq if f[0] == "branch")
  covered_branches = sum(1 for f in cov_counts if f[0] == "branch" and cov_counts[f] > 0)
  total_behav = sum(1 for f in feat_freq if str(f[0]).startswith("behav_"))
  covered_behav = sum(1 for f in cov_counts if str(f[0]).startswith("behav_") and cov_counts[f] > 0)

  stats = {
    "selected_count": len(selected_entries),
    "candidate_pool_size": len(profiled_items),
    "total_features": len(feat_freq),
    "covered_features": len(cov_counts),
    "lines_covered": f"{covered_lines}/{total_lines}",
    "branches_covered": f"{covered_branches}/{total_branches}",
    "behavioral_buckets_covered": f"{covered_behav}/{total_behav}",
    "by_category": dict(collections.Counter(e["category"] for e in selected_entries)),
    "by_source": dict(collections.Counter(e["source"] for e in selected_entries)),
    "by_max_level": dict(collections.Counter(e.get("baseline_max_level", 0) for e in selected_entries)),
  }
  return selected_entries, stats


def write_dataset_jsonl(out_path: Path, entries: list[dict[str, Any]]) -> None:
  out_path.parent.mkdir(parents=True, exist_ok=True)
  with open(out_path, "wt", encoding="utf-8") as f:
    for e in entries:
      f.write(json.dumps(e) + "\n")


def build_datasets(
  fast_size: int = 500,
  full_size: int = 3000,
  seed: int = 42,
  max_candidates: int = 1500,
) -> tuple[Path, Path, dict[str, Any]]:
  """Build both 'fast' and 'full' curated benchmark datasets."""
  rng = random.Random(seed)
  print("Collecting candidate TMs from all sources...")

  raw_candidates: list[CandidateTM] = []
  raw_candidates.extend(iter_green_candidates(max_states=20))
  raw_candidates.extend(iter_machines_dir_candidates(rng))
  raw_candidates.extend(iter_top_level_candidates(max_count=max(200, max_candidates // 4), rng=rng))
  raw_candidates.extend(
    iter_holdout_candidates(
      rng,
      sample_2x6=max(100, max_candidates // 6),
      sample_7x2=max(150, max_candidates // 5),
    )
  )
  raw_candidates.extend(
    iter_verified_csv_candidates(
      max_per_decider=max(10, max_candidates // 40),
      max_high_halters=max(50, max_candidates // 10),
    )
  )

  # Deduplicate by TM ttable string (preserving mandatory flag and earliest source)
  deduped: list[CandidateTM] = []
  seen_tm: set[str] = set()
  # Put mandatory candidates first
  raw_candidates.sort(key=lambda c: (not c.mandatory, c.source))
  for c in raw_candidates:
    if c.tm not in seen_tm:
      seen_tm.add(c.tm)
      deduped.append(c)

  if len(deduped) > max_candidates:
    mandatory = [c for c in deduped if c.mandatory]
    optional = [c for c in deduped if not c.mandatory]
    rng.shuffle(optional)
    deduped = mandatory + optional[: max(0, max_candidates - len(mandatory))]

  print(f"Profiling {len(deduped)} unique candidate TMs (resolving fixed block_size + sys.monitoring coverage)...")
  profiled: list[tuple[dict[str, Any], set[tuple[Any, ...]]]] = []
  skipped_halters: list[str] = []
  t0 = time.time()

  for idx, cand in enumerate(deduped):
    entry, feats = resolve_block_size_and_profile(cand, profile_coverage=True, time_limit_sec=4.0)
    if entry is None:
      if cand.category == "halt":
        skipped_halters.append(cand.name)
      continue
    profiled.append((entry, feats))
    if (idx + 1) % max(1, len(deduped) // 10) == 0:
      print(f"  Profiled {idx + 1}/{len(deduped)} candidates ({len(profiled)} valid, {time.time() - t0:.1f}s)")

  if skipped_halters:
    print(f"Note: Skipped {len(skipped_halters)} halters that exceeded curation loop/time cap: {skipped_halters[:10]}")

  fast_entries, fast_stats = select_diverse_subset(profiled, target_count=fast_size, min_k_coverage=3)
  full_entries, full_stats = select_diverse_subset(profiled, target_count=full_size, min_k_coverage=12)

  fast_path = DATASETS_DIR / "fast.jsonl"
  full_path = DATASETS_DIR / "full.jsonl"
  write_dataset_jsonl(fast_path, fast_entries)
  write_dataset_jsonl(full_path, full_entries)

  print(f"\nWrote 'fast' dataset ({len(fast_entries)} TMs) to {fast_path}:")
  print(json.dumps(fast_stats, indent=2))
  print(f"\nWrote 'full' dataset ({len(full_entries)} TMs) to {full_path}:")
  print(json.dumps(full_stats, indent=2))

  return fast_path, full_path, {"fast": fast_stats, "full": full_stats}


def evaluate_candidates_against_dataset(
  dataset_arg: str,
  cand_specs: list[str],
  add_to_dataset: bool = False,
  force_Add: bool = False,
  block_size: int | None = None,
  category: str = "unknown",
  name_override: str | None = None,
  max_loops: int = 20_000,
  tape_limit: int = 50,
) -> list[dict[str, Any]]:
  """Evaluate one or more candidate TMs (or files of TMs) against an existing dataset's coverage.

  Reports for each candidate:
  - Its resolved block_size, status, reason, max_rule_level, and sim_time_us.
  - How many NEW code lines, branches, and behavioral features it covers that the
    existing dataset never hits (or hits < 3 times).
  - A recommendation ("ADD: new coverage", "ADD: high rule level", or "SKIP: redundant").
  """
  ds_path, existing_entries = load_dataset(dataset_arg)
  existing_tms = {e["tm"] for e in existing_entries}
  ref_config = CONFIG_PRESETS["prover_4_meta_linear"].to_dict()

  print(f"Profiling existing dataset '{ds_path.name}' ({len(existing_entries)} TMs) to build baseline coverage map...")
  baseline_counts: collections.Counter = collections.Counter()
  for e in existing_entries:
    cand_e = CandidateTM(
      tm=e["tm"],
      name=e["name"],
      source=e.get("source", "existing"),
      category=e.get("category", "unknown"),
      block_size=e["block_size"],
      max_loops=min(int(e.get("max_loops", 10_000)), 20_000),
      tape_limit=int(e.get("tape_limit", 50)),
    )
    with CoverageProfiler() as prof:
      res = run_single_tm(e, ref_config, undecided_mode="full", time_limit_sec=2.0)
    feats = set(prof.features) | extract_behavioral_features(cand_e, res)
    for f in feats:
      baseline_counts[f] += 1

  # Parse candidate specs (can be a TM string or a file path)
  candidates: list[CandidateTM] = []
  for spec in cand_specs:
    p = Path(spec)
    if p.is_file():
      with IO.Common.open_file(p, "rt") as f:
        for idx, line in enumerate(f):
          tok, custom_id = _extract_tm_token_from_line(line)
          if tok:
            tag = custom_id if custom_id else str(idx)
            candidates.append(
              CandidateTM(
                tm=tok,
                name=f"{p.name}:{tag}",
                source="custom",
                category=category,
                block_size=block_size,
                max_loops=max_loops,
                tape_limit=tape_limit,
              )
            )
    elif is_valid_std_tm(spec):
      candidates.append(
        CandidateTM(
          tm=spec,
          name=name_override if (name_override and len(cand_specs) == 1) else spec,
          source="custom",
          category=category,
          block_size=block_size,
          max_loops=max_loops,
          tape_limit=tape_limit,
        )
      )
    else:
      print(f"Warning: Skipping unrecognized TM or file '{spec}'")

  reports: list[dict[str, Any]] = []
  added_entries: list[dict[str, Any]] = []

  print(f"\nEvaluating {len(candidates)} candidate TM(s)...\n")
  for cand in candidates:
    already_in = cand.tm in existing_tms
    entry, feats = resolve_block_size_and_profile(cand, profile_coverage=True, time_limit_sec=5.0)
    if entry is None:
      print(f"- {cand.name} ({cand.tm}): FAILED to resolve block_size")
      continue

    new_lines = [f for f in feats if f[0] == "line" and baseline_counts[f] == 0]
    new_branches = [f for f in feats if f[0] == "branch" and baseline_counts[f] == 0]
    new_behav = [f for f in feats if str(f[0]).startswith("behav_") and baseline_counts[f] == 0]
    rare_feats = [f for f in feats if 0 < baseline_counts[f] < 3]

    max_lvl = entry.get("baseline_max_level", 0)
    if already_in and not force_Add:
      verdict = "SKIP (already in dataset)"
    elif new_lines or new_branches or new_behav:
      verdict = "RECOMMEND ADD (covers brand-new code/behavior)"
    elif len(rare_feats) >= 5 or max_lvl >= 3:
      verdict = "RECOMMEND ADD (reinforces rare paths / L3+ rules)"
    else:
      verdict = "SKIP (redundant with existing TMs; pass --force-add to add anyway)"

    print(
      f"- {cand.name} ({cand.tm})\n"
      f"  Status: {entry['baseline_status']} ({entry['baseline_reason']}) | "
      f"category={entry['category']} | block_size={entry['block_size']} | max_level=L{max_lvl} | "
      f"loops={entry['baseline_loops']} | time={entry['baseline_sim_time_us'] / 1000:.1f}ms\n"
      f"  Coverage delta: +{len(new_lines)} new lines, +{len(new_branches)} new branches, "
      f"+{len(new_behav)} new behavioral tags, +{len(rare_feats)} rare features (<3 hits)\n"
      f"  Verdict: {verdict}\n"
    )

    rep = {
      "entry": entry,
      "already_in_dataset": already_in,
      "new_lines": len(new_lines),
      "new_branches": len(new_branches),
      "new_behav": len(new_behav),
      "rare_feats": len(rare_feats),
      "verdict": verdict,
    }
    reports.append(rep)

    should_add = force_Add or (add_to_dataset and not already_in and verdict.startswith("RECOMMEND ADD"))
    if should_add:
      if already_in:
        existing_entries = [e for e in existing_entries if e["tm"] != cand.tm]
      existing_entries.append(entry)
      existing_tms.add(cand.tm)
      added_entries.append(entry)
      for f in feats:
        baseline_counts[f] += 1

  if added_entries:
    write_dataset_jsonl(ds_path, existing_entries)
    print(f"Saved {len(added_entries)} TM(s) to {ds_path} (total: {len(existing_entries)} TMs).")

  return reports


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description="Build and analyze curated Macro Simulator benchmark datasets")
  sub = parser.add_subparsers(dest="subcommand", required=True)

  p_build = sub.add_parser("build", help="Curate and build fast.jsonl and full.jsonl datasets")
  p_build.add_argument("--fast-size", type=int, default=500, help="Target TM count for fast.jsonl [default: 500]")
  p_build.add_argument("--full-size", type=int, default=2500, help="Target TM count for full.jsonl [default: 2500]")
  p_build.add_argument(
    "--max-candidates", type=int, default=1500, help="Candidate pool size to profile [default: 1500]"
  )
  p_build.add_argument("--seed", type=int, default=42)

  p_stats = sub.add_parser("stats", help="Print breakdown of an existing dataset .jsonl file")
  p_stats.add_argument("dataset", help="Dataset name ('fast', 'full') or path")

  p_eval = sub.add_parser(
    "eval-candidate",
    help="Check if new candidate TM(s) add new code/behavioral coverage to a dataset (and optionally add them)",
  )
  p_eval.add_argument("--dataset", default="fast", help="Dataset name ('fast', 'full') or path [default: fast]")
  p_eval.add_argument("-n", "--block-size", type=int, default=None, help="Explicit fixed block_size (e.g. -n 4)")
  p_eval.add_argument(
    "--category",
    choices=["halt", "inf", "holdout", "unknown"],
    default="unknown",
    help="Expected ground-truth category (sweeps block sizes to satisfy halt/inf if -n is omitted)",
  )
  p_eval.add_argument("--name", default=None, help="Optional human-readable name for the TM")
  p_eval.add_argument("--max-loops", type=int, default=20_000, help="Per-TM max_loops [default: 20000]")
  p_eval.add_argument("--tape-limit", type=int, default=50, help="Per-TM tape_limit [default: 50]")
  p_eval.add_argument("--add", action="store_true", help="Append recommended TMs to the dataset file")
  p_eval.add_argument(
    "--force-add", action="store_true", help="Append (or update) TM in the dataset regardless of recommendation"
  )
  p_eval.add_argument("candidates", nargs="+", help="One or more TM strings (e.g. 1RB...) or file paths")

  args = parser.parse_args(argv)
  if args.subcommand == "build":
    build_datasets(
      fast_size=args.fast_size,
      full_size=args.full_size,
      seed=args.seed,
      max_candidates=args.max_candidates,
    )
    return 0
  elif args.subcommand == "stats":
    path, entries = load_dataset(args.dataset)
    print(f"Dataset: {path} ({len(entries)} TMs)")
    print("  By category:", dict(collections.Counter(e["category"] for e in entries)))
    print("  By source:  ", dict(collections.Counter(e["source"] for e in entries)))
    print("  By block_size:", dict(collections.Counter(e["block_size"] for e in entries)))
    print("  By baseline_max_level:", dict(collections.Counter(e.get("baseline_max_level", 0) for e in entries)))
    return 0
  elif args.subcommand == "eval-candidate":
    evaluate_candidates_against_dataset(
      args.dataset,
      args.candidates,
      add_to_dataset=args.add,
      force_Add=args.force_add,
      block_size=args.block_size,
      category=args.category,
      name_override=args.name,
      max_loops=args.max_loops,
      tape_limit=args.tape_limit,
    )
    return 0
  return 0


if __name__ == "__main__":
  sys.exit(main())
