#!/usr/bin/env python3
"""
Truth database management, coverage-guided dataset selection, and candidate evaluation
for the Macro Simulator regression & benchmark testing system.

Architecture:
1. Canonical Truth File (benchmarks/truth.jsonl):
   Stores intrinsic per-TM facts (category: halt/inf/holdout, fixed block_size,
   max_steps_in_block, max_steps_in_backsymbol, sim_decidable, decision_loops,
   max_rule_level, expected_score) independent of any benchmark time budget.
2. Suite Run Files (benchmarks/datasets/fast.jsonl, full.jsonl):
   Store subsets of truth.jsonl paired with suite-appropriate practical limits
   (max_loops, tape_limit), baseline outcomes at that limit, and target_max_span_bi
   milestones for undecided/slow TMs.
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
  TRUTH_FILE,
  load_dataset,
  load_truth,
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
  category: str  # "halt" | "inf" | "holdout" | "unknown" (auto-resolved during truth discovery)
  mandatory: bool = False
  block_size: int | None = None
  max_loops: int = 20_000
  tape_limit: int = 100
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

  def _on_branch(self, code, instruction_offset: int, destination_offset: int):
    mod = self._resolve_mod(code)
    if mod is not None:
      self.features.add(("branch", mod, instruction_offset, destination_offset))
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


def extract_behavioral_features(
  tm_str: str, source: str, category: str, run_res: dict[str, Any]
) -> set[tuple[Any, ...]]:
  """Extract high-level Proof_System and simulator behavioral features from a run."""
  tm_obj = IO.parse_tm(tm_str)
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
    ("behav_source_cat", source, category),
  }
  if run_res.get("num_meta_diff_rules", 0) > 0:
    b_feats.add(("behav_rule_type", "meta_diff"))
  if run_res.get("num_linear_rules", 0) > 0:
    b_feats.add(("behav_rule_type", "linear"))
  if run_res.get("num_collatz_rules", 0) > 0:
    b_feats.add(("behav_rule_type", "collatz"))

  for lvl_str in run_res.get("rules_by_level", {}):
    b_feats.add(("behav_rule_level_present", min(int(lvl_str), 6)))

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


def discover_truth_record(
  cand: CandidateTM,
  time_limit_sec: float = 5.0,
) -> dict[str, Any] | None:
  """Discover and verify a canonical truth.jsonl record for `cand`."""
  tm_obj = IO.parse_tm(cand.tm)

  if cand.block_size is not None:
    bs_list = [cand.block_size]
  else:
    bs_list = find_block_finder_candidates(tm_obj)
    if cand.category in ("halt", "inf") or cand.source in ("machines", "custom"):
      base_cands = list(bs_list)
      for b in base_cands:
        for mult in (2, 3, 4):
          if b * mult <= 24 and (b * mult) not in bs_list:
            bs_list.append(b * mult)
      for b in (1, 2, 3, 4, 5, 6, 8, 9, 10, 12):
        if b not in bs_list:
          bs_list.append(b)

  ref_config = CONFIG_PRESETS["prover_3_iterated"].to_dict()
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

    if cand.category != "unknown" and res["status"] in ("halt", "inf") and res["status"] != cand.category:
      print(
        f"Error: {cand.name} ({cand.tm}) was decided as '{res['status']}' (block_size={bs}), "
        f"which contradicts category='{cand.category}'"
      )
      return None

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
      if res["status"] in ("halt", "inf"):
        chosen_bs = bs
        chosen_res = res
        break
    else:
      if not res.get("threw_exception"):
        chosen_bs = bs
        chosen_res = res
        break

  if chosen_res is None:
    return None

  if cand.category != "unknown" and chosen_res["status"] in ("halt", "inf") and chosen_res["status"] != cand.category:
    print(
      f"Error: {cand.name} ({cand.tm}) was decided as '{chosen_res['status']}', "
      f"which contradicts category='{cand.category}'"
    )
    return None

  final_category = cand.category
  if final_category == "unknown":
    final_category = chosen_res["status"] if chosen_res["status"] in ("halt", "inf") else "holdout"

  sim_decidable = chosen_res["status"] in ("halt", "inf")
  expected_score_exact = None
  expected_score_bi = None
  if final_category == "halt" and chosen_res["status"] == "halt":
    expected_score_exact = chosen_res["halt_score"].get("exact")
    expected_score_bi = chosen_res["halt_score"].get("bi")

  return {
    "tm": cand.tm,
    "name": cand.name,
    "source": cand.source,
    "category": final_category,
    "mandatory": cand.mandatory,
    "block_size": chosen_bs,
    "max_steps_in_block": cand.max_steps_in_block,
    "max_steps_in_backsymbol": cand.max_steps_in_backsymbol,
    "sim_decidable": sim_decidable,
    "decision_reason": chosen_res["reason"] if sim_decidable else None,
    "decision_loops": chosen_res["total_loops"] if sim_decidable else None,
    "decision_tape_compressed": chosen_res.get("max_tape_compressed") if sim_decidable else None,
    "decision_time_us": chosen_res["sim_time_us"] if sim_decidable else None,
    "max_rule_level": chosen_res.get("max_rule_level", 0),
    "expected_score_exact": expected_score_exact,
    "expected_score_bi": expected_score_bi,
  }


def compute_suite_budget(truth_rec: dict[str, Any], suite_name: str) -> tuple[int, int]:
  """Determine practical (max_loops, tape_limit) for a TM in `fast` or `full`."""
  is_full = suite_name == "full"
  max_decidable_loops = 750_000 if is_full else 225_000
  max_decidable_time_us = 5_000_000 if is_full else 2_500_000

  dec_loops = truth_rec.get("decision_loops")
  dec_time_us = truth_rec.get("decision_time_us")
  dec_tape = truth_rec.get("decision_tape_compressed")
  source = truth_rec.get("source", "")
  max_lvl = int(truth_rec.get("max_rule_level", 0))

  default_tape = 100 if (source == "green" or max_lvl >= 3) else 50

  if truth_rec.get("sim_decidable") and dec_loops is not None:
    within_loops = int(dec_loops) <= max_decidable_loops
    within_time = dec_time_us is None or int(dec_time_us) <= max_decidable_time_us
    if within_loops and within_time:
      budget_loops = max(10_000, int(int(dec_loops) * 1.15) + 500)
      tape_lim = max(default_tape, 250 if int(dec_loops) > 100_000 else default_tape)
      if dec_tape is not None:
        tape_lim = max(tape_lim, int(dec_tape) + 25)
      return budget_loops, tape_lim

  # Milestone / undecided budget for holdouts or ultra-long halters
  if truth_rec.get("name") == "Machines/2x6-t24":
    return (5_000 if is_full else 2_500), 100
  if truth_rec.get("name") in ("Machines/7x2-a11-Pavel", "Machines/7x2-a19"):
    return 30_000, 100
  if truth_rec.get("name") == "Machines/3x4-a14":
    return 25_000, 100
  if max_lvl >= 4 or source == "green":
    return 20_000, 100
  return 10_000, default_tape


def build_suite_entry(
  truth_rec: dict[str, Any],
  suite_name: str,
  profile_coverage: bool = True,
  max_loops_override: int | None = None,
  tape_limit_override: int | None = None,
) -> tuple[dict[str, Any], set[tuple[Any, ...]]]:
  """Run a truth record under its suite-specific practical budget and collect coverage."""
  max_loops, tape_limit = compute_suite_budget(truth_rec, suite_name)
  if max_loops_override is not None:
    max_loops = max_loops_override
  if tape_limit_override is not None:
    tape_limit = tape_limit_override

  run_input = {
    **truth_rec,
    "max_loops": max_loops,
    "tape_limit": tape_limit,
    "target_max_span_bi": None,
  }
  ref_config = CONFIG_PRESETS["prover_3_iterated"].to_dict()

  if profile_coverage:
    with CoverageProfiler() as prof:
      res = run_single_tm(run_input, ref_config, undecided_mode="full", time_limit_sec=5.0)
    cov_features = set(prof.features)
  else:
    res = run_single_tm(run_input, ref_config, undecided_mode="full", time_limit_sec=5.0)
    cov_features = set()

  cov_features |= extract_behavioral_features(
    truth_rec["tm"],
    truth_rec.get("source", "unknown"),
    truth_rec["category"],
    res,
  )

  target_max_span_bi: list[int] | None = None
  if res["status"] == "unknown":
    span_bi = res.get("max_span", {}).get("bi")
    if span_bi and span_bi[0]:
      target_max_span_bi = list(span_bi[0])

  suite_entry = {
    "tm": truth_rec["tm"],
    "name": truth_rec["name"],
    "max_loops": max_loops,
    "tape_limit": tape_limit,
    "baseline_status": res["status"],
    "baseline_reason": res["reason"],
    "baseline_max_level": res.get("max_rule_level", 0),
    "baseline_loops": res["total_loops"],
    "baseline_sim_time_us": res["sim_time_us"],
    "target_max_span_bi": target_max_span_bi,
  }
  return suite_entry, cov_features


# =============================================================================
# Compatibility wrapper for unit tests & external callers
# =============================================================================


def resolve_block_size_and_profile(
  cand: CandidateTM,
  profile_coverage: bool = True,
  time_limit_sec: float = 5.0,
) -> tuple[dict[str, Any] | None, set[tuple[Any, ...]]]:
  """Discover truth for `cand` and build a merged suite entry + coverage features."""
  truth_rec = discover_truth_record(cand, time_limit_sec=time_limit_sec)
  if truth_rec is None:
    return None, set()
  if cand.category == "halt" and not truth_rec["sim_decidable"]:
    return None, set()
  suite_entry, cov_features = build_suite_entry(
    truth_rec,
    suite_name="fast",
    profile_coverage=profile_coverage,
    max_loops_override=cand.max_loops,
    tape_limit_override=cand.tape_limit,
  )
  return {**truth_rec, **suite_entry}, cov_features


# =============================================================================
# Candidate TM Source Loaders
# =============================================================================


def iter_green_candidates(max_states: int = 20) -> list[CandidateTM]:
  """Generate Green.py machines for even (-n1) and odd (-n2) states."""
  cands: list[CandidateTM] = []
  for n in range(6, max_states + 1):
    tm_str = Green.green_machine_str(n)
    block_size = 1 if (n % 2 == 0) else 2
    cands.append(
      CandidateTM(
        tm=tm_str,
        name=f"Green-{n}",
        source="green",
        category="halt",
        mandatory=True,
        block_size=block_size,
        max_loops=150_000,
        tape_limit=100,
      )
    )
  return cands


def iter_machines_dir_candidates(rng: random.Random) -> list[CandidateTM]:
  """Load TMs from Machines/* and its subdirectories."""
  machines_dir = ROOT_DIR / "Machines"
  cands: list[CandidateTM] = []

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
            cands.append(
              CandidateTM(
                tm=tok,
                name=f"Machines/{p.name}:{idx}",
                source="machines",
                category="inf",
                mandatory=True,
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
    cat = "inf" if "-LR-" in p.name else "unknown"
    cands.append(
      CandidateTM(
        tm=tok,
        name=rel_name,
        source="machines",
        category=cat,
        mandatory=True,
      )
    )

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

  bb_dir = machines_dir / "bb"
  if bb_dir.is_dir():
    for p in sorted(bb_dir.glob("*.txt")):
      with open(p, "rt", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
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

  zip_7x2 = holdouts_dir / "7x2_holdouts_15743264.txt.zip"
  if zip_7x2.exists() and sample_7x2 > 0:
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
  """Select up to `target_count` TMs maximizing code + behavioral coverage with k-redundancy."""
  if len(profiled_items) <= target_count:
    entries = [e for e, _ in profiled_items]
    all_feats = set().union(*(f for _, f in profiled_items)) if profiled_items else set()
    return entries, {"total_features": len(all_feats), "covered_features": len(all_feats)}

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
        key = (
          entry.get("category", "unknown"),
          entry.get("source", "unknown"),
          int(entry.get("baseline_max_level", 0)),
        )
        strata[key].append(i)

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
    "by_category": dict(collections.Counter(e.get("category", "unknown") for e in selected_entries)),
    "by_source": dict(collections.Counter(e.get("source", "unknown") for e in selected_entries)),
    "by_max_level": dict(collections.Counter(e.get("baseline_max_level", 0) for e in selected_entries)),
  }
  return selected_entries, stats


def write_dataset_jsonl(out_path: Path, entries: list[dict[str, Any]]) -> None:
  out_path.parent.mkdir(parents=True, exist_ok=True)
  with open(out_path, "wt", encoding="utf-8") as f:
    for e in entries:
      f.write(json.dumps(e) + "\n")


def write_truth_file(truth_by_tm: dict[str, dict[str, Any]], out_path: Path = TRUTH_FILE) -> None:
  write_dataset_jsonl(out_path, list(truth_by_tm.values()))


def _strip_to_suite_entry(merged_entry: dict[str, Any]) -> dict[str, Any]:
  """Keep only suite-specific execution budget & baseline fields in fast.jsonl/full.jsonl."""
  return {
    "tm": merged_entry["tm"],
    "name": merged_entry["name"],
    "max_loops": merged_entry["max_loops"],
    "tape_limit": merged_entry["tape_limit"],
    "baseline_status": merged_entry["baseline_status"],
    "baseline_reason": merged_entry["baseline_reason"],
    "baseline_max_level": merged_entry["baseline_max_level"],
    "baseline_loops": merged_entry["baseline_loops"],
    "baseline_sim_time_us": merged_entry["baseline_sim_time_us"],
    "target_max_span_bi": merged_entry["target_max_span_bi"],
  }


def select_datasets_from_truth(
  fast_size: int = 500,
  full_size: int = 2000,
  truth_path: Path = TRUTH_FILE,
) -> tuple[Path, Path, dict[str, Any]]:
  """Build fast.jsonl and full.jsonl by profiling truth.jsonl entries under suite budgets."""
  truth_by_tm = load_truth(truth_path)
  if not truth_by_tm:
    raise FileNotFoundError(f"Truth file is empty or missing: {truth_path}")

  print(f"Profiling {len(truth_by_tm)} truth records under 'fast' budgets...")
  t0 = time.time()
  fast_pool: list[tuple[dict[str, Any], set[tuple[Any, ...]]]] = []
  for idx, truth_rec in enumerate(truth_by_tm.values()):
    suite_e, feats = build_suite_entry(truth_rec, suite_name="fast", profile_coverage=True)
    # Attach category/source/mandatory temporarily so select_diverse_subset can stratify
    merged = {
      **suite_e,
      "category": truth_rec["category"],
      "source": truth_rec["source"],
      "mandatory": truth_rec.get("mandatory", False),
    }
    fast_pool.append((merged, feats))
    if (idx + 1) % max(1, len(truth_by_tm) // 10) == 0:
      print(f"  Profiled {idx + 1}/{len(truth_by_tm)} ({time.time() - t0:.1f}s)")

  fast_selected, fast_stats = select_diverse_subset(fast_pool, target_count=fast_size, min_k_coverage=3)
  fast_entries = [_strip_to_suite_entry(e) for e in fast_selected]

  print(f"Selecting 'full' dataset ({full_size} TMs) and computing full-suite budgets...")
  full_selected, full_stats = select_diverse_subset(fast_pool, target_count=full_size, min_k_coverage=12)
  full_entries: list[dict[str, Any]] = []
  for merged_e in full_selected:
    truth_rec = truth_by_tm[merged_e["tm"]]
    fast_budget = compute_suite_budget(truth_rec, "fast")
    full_budget = compute_suite_budget(truth_rec, "full")
    if full_budget != fast_budget:
      suite_full, _ = build_suite_entry(truth_rec, suite_name="full", profile_coverage=False)
      full_entries.append(suite_full)
    else:
      full_entries.append(_strip_to_suite_entry(merged_e))

  fast_path = DATASETS_DIR / "fast.jsonl"
  full_path = DATASETS_DIR / "full.jsonl"
  write_dataset_jsonl(fast_path, fast_entries)
  write_dataset_jsonl(full_path, full_entries)

  print(f"\nWrote 'fast' dataset ({len(fast_entries)} TMs) to {fast_path}:")
  print(json.dumps(fast_stats, indent=2))
  print(f"\nWrote 'full' dataset ({len(full_entries)} TMs) to {full_path}:")
  print(json.dumps(full_stats, indent=2))

  return fast_path, full_path, {"fast": fast_stats, "full": full_stats}


def build_datasets(
  fast_size: int = 500,
  full_size: int = 2000,
  seed: int = 42,
  max_candidates: int = 1500,
) -> tuple[Path, Path, dict[str, Any]]:
  """Ingest candidates, discover truth for any new TMs into truth.jsonl, then select suites."""
  rng = random.Random(seed)
  truth_by_tm = load_truth(TRUTH_FILE)
  print(f"Loaded {len(truth_by_tm)} existing truth records from {TRUTH_FILE}.")

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

  deduped: list[CandidateTM] = []
  seen_tm: set[str] = set(truth_by_tm.keys())
  raw_candidates.sort(key=lambda c: (not c.mandatory, c.source))
  for c in raw_candidates:
    if c.tm not in seen_tm:
      seen_tm.add(c.tm)
      deduped.append(c)

  new_budget = max(0, max_candidates - len(truth_by_tm))
  if len(deduped) > new_budget:
    mandatory = [c for c in deduped if c.mandatory]
    optional = [c for c in deduped if not c.mandatory]
    rng.shuffle(optional)
    deduped = mandatory + optional[: max(0, new_budget - len(mandatory))]

  if deduped:
    print(f"Discovering truth for {len(deduped)} new candidate TMs...")
    t0 = time.time()
    for idx, cand in enumerate(deduped):
      rec = discover_truth_record(cand, time_limit_sec=4.0)
      if rec is not None:
        truth_by_tm[rec["tm"]] = rec
      if (idx + 1) % max(1, len(deduped) // 10) == 0:
        print(f"  Discovered {idx + 1}/{len(deduped)} ({time.time() - t0:.1f}s)")
    write_truth_file(truth_by_tm, TRUTH_FILE)
    print(f"Updated {TRUTH_FILE} (total: {len(truth_by_tm)} truth records).")

  return select_datasets_from_truth(fast_size=fast_size, full_size=full_size, truth_path=TRUTH_FILE)


def _resolve_existing_category(category: str, existing: dict[str, Any] | None) -> str:
  if category != "unknown":
    return category
  if existing and existing.get("category") in ("halt", "inf"):
    return existing["category"]
  return "unknown"


def _parse_candidate_specs(
  cand_specs: list[str],
  block_size: int | None,
  category: str,
  name_override: str | None,
  max_loops: int,
  tape_limit: int,
  mandatory: bool = False,
  truth_by_tm: dict[str, dict[str, Any]] | None = None,
) -> list[CandidateTM]:
  by_name = {rec["name"]: rec for rec in truth_by_tm.values()} if truth_by_tm else {}
  candidates: list[CandidateTM] = []
  for spec in cand_specs:
    p = Path(spec)
    if spec in by_name:
      rec = by_name[spec]
      candidates.append(
        CandidateTM(
          tm=rec["tm"],
          name=name_override or rec["name"],
          source=rec.get("source", "custom"),
          category=_resolve_existing_category(category, rec),
          mandatory=mandatory or bool(rec.get("mandatory", False)),
          block_size=block_size if block_size is not None else rec.get("block_size"),
          max_loops=max_loops,
          tape_limit=tape_limit,
          max_steps_in_block=int(rec.get("max_steps_in_block", 100_000)),
          max_steps_in_backsymbol=int(rec.get("max_steps_in_backsymbol", 1_000)),
        )
      )
    elif p.is_file():
      with IO.Common.open_file(p, "rt") as f:
        for idx, line in enumerate(f):
          tok, custom_id = _extract_tm_token_from_line(line)
          if tok:
            existing = truth_by_tm.get(tok) if truth_by_tm else None
            tag = custom_id if custom_id else str(idx)
            candidates.append(
              CandidateTM(
                tm=tok,
                name=name_override or (existing["name"] if existing else f"{p.name}:{tag}"),
                source=existing.get("source", "custom") if existing else "custom",
                category=_resolve_existing_category(category, existing),
                mandatory=mandatory or (bool(existing.get("mandatory", False)) if existing else False),
                block_size=block_size if block_size is not None else (existing.get("block_size") if existing else None),
                max_loops=max_loops,
                tape_limit=tape_limit,
                max_steps_in_block=int(existing.get("max_steps_in_block", 100_000)) if existing else 100_000,
                max_steps_in_backsymbol=int(existing.get("max_steps_in_backsymbol", 1_000)) if existing else 1_000,
              )
            )
    elif is_valid_std_tm(spec):
      existing = truth_by_tm.get(spec) if truth_by_tm else None
      candidates.append(
        CandidateTM(
          tm=spec,
          name=name_override or (existing["name"] if existing else spec),
          source=existing.get("source", "custom") if existing else "custom",
          category=_resolve_existing_category(category, existing),
          mandatory=mandatory or (bool(existing.get("mandatory", False)) if existing else False),
          block_size=block_size if block_size is not None else (existing.get("block_size") if existing else None),
          max_loops=max_loops,
          tape_limit=tape_limit,
          max_steps_in_block=int(existing.get("max_steps_in_block", 100_000)) if existing else 100_000,
          max_steps_in_backsymbol=int(existing.get("max_steps_in_backsymbol", 1_000)) if existing else 1_000,
        )
      )
    else:
      print(f"Warning: Skipping unrecognized TM, name, or file '{spec}'")
  return candidates


def add_truth_command(
  cand_specs: list[str],
  block_size: int | None = None,
  category: str = "unknown",
  name_override: str | None = None,
  max_loops: int = 1_000_000,
  tape_limit: int = 200,
  time_limit_sec: float = 30.0,
  mandatory: bool = False,
) -> list[dict[str, Any]]:
  """Step 1: Discover/verify ground truth for candidate TM(s) and save to benchmarks/truth.jsonl."""
  truth_by_tm = load_truth(TRUTH_FILE)
  candidates = _parse_candidate_specs(
    cand_specs,
    block_size,
    category,
    name_override,
    max_loops,
    tape_limit,
    mandatory,
    truth_by_tm=truth_by_tm,
  )
  added_or_updated: list[dict[str, Any]] = []

  for cand in candidates:
    rec = discover_truth_record(cand, time_limit_sec=time_limit_sec)
    if rec is None:
      print(f"- {cand.name} ({cand.tm}): FAILED truth discovery")
      continue
    action = "Updated" if cand.tm in truth_by_tm else "Added"
    truth_by_tm[cand.tm] = rec
    added_or_updated.append(rec)
    print(
      f"- {action} truth for {rec['name']} ({rec['tm']}): "
      f"category={rec['category']}, block_size={rec['block_size']}, "
      f"sim_decidable={rec['sim_decidable']}, decision_loops={rec['decision_loops']}, "
      f"max_rule_level=L{rec['max_rule_level']}"
    )

  if added_or_updated:
    write_truth_file(truth_by_tm, TRUTH_FILE)
    print(f"Saved {len(truth_by_tm)} total records to {TRUTH_FILE}.")
  return added_or_updated


def evaluate_candidates_against_dataset(
  dataset_arg: str,
  cand_specs: list[str],
  add_to_dataset: bool = False,
  force_add: bool = False,
  save_truth: bool = False,
  block_size: int | None = None,
  category: str = "unknown",
  name_override: str | None = None,
  max_loops: int | None = None,
  tape_limit: int | None = None,
) -> list[dict[str, Any]]:
  """Step 2: Evaluate candidate TM(s) against a suite dataset's coverage & practical budget."""
  ds_path, existing_entries = load_dataset(dataset_arg)
  suite_name = "full" if "full" in ds_path.stem else "fast"
  truth_by_tm = load_truth(TRUTH_FILE)
  existing_tms = {e["tm"] for e in existing_entries}
  ref_config = CONFIG_PRESETS["prover_3_iterated"].to_dict()

  print(f"Profiling existing dataset '{ds_path.name}' ({len(existing_entries)} TMs) to build baseline coverage map...")
  baseline_counts: collections.Counter = collections.Counter()
  for e in existing_entries:
    with CoverageProfiler() as prof:
      res = run_single_tm(e, ref_config, undecided_mode="full", time_limit_sec=2.0)
    feats = set(prof.features) | extract_behavioral_features(
      e["tm"], e.get("source", "existing"), e.get("category", "unknown"), res
    )
    for f in feats:
      baseline_counts[f] += 1

  candidates = _parse_candidate_specs(
    cand_specs,
    block_size,
    category,
    name_override,
    max_loops if max_loops is not None else 20_000,
    tape_limit if tape_limit is not None else 100,
  )

  reports: list[dict[str, Any]] = []
  added_suite_entries: list[dict[str, Any]] = []
  truth_dirty = False

  print(f"\nEvaluating {len(candidates)} candidate TM(s) for '{suite_name}'...\n")
  for cand in candidates:
    already_in = cand.tm in existing_tms
    if cand.tm in truth_by_tm and block_size is None and category == "unknown":
      truth_rec = truth_by_tm[cand.tm]
    else:
      truth_rec = discover_truth_record(cand, time_limit_sec=5.0)
      if truth_rec is None:
        print(f"- {cand.name} ({cand.tm}): FAILED to resolve block_size")
        continue
      if save_truth or add_to_dataset or force_add:
        truth_by_tm[cand.tm] = truth_rec
        truth_dirty = True

    suite_entry, feats = build_suite_entry(
      truth_rec,
      suite_name=suite_name,
      profile_coverage=True,
      max_loops_override=max_loops,
      tape_limit_override=tape_limit,
    )

    new_lines = [f for f in feats if f[0] == "line" and baseline_counts[f] == 0]
    new_branches = [f for f in feats if f[0] == "branch" and baseline_counts[f] == 0]
    new_behav = [f for f in feats if str(f[0]).startswith("behav_") and baseline_counts[f] == 0]
    rare_feats = [f for f in feats if 0 < baseline_counts[f] < 3]

    max_lvl = suite_entry.get("baseline_max_level", 0)
    if already_in and not force_add:
      verdict = "SKIP (already in dataset)"
    elif new_lines or new_branches or new_behav:
      verdict = "RECOMMEND ADD (covers brand-new code/behavior)"
    elif len(rare_feats) >= 5 or max_lvl >= 3:
      verdict = "RECOMMEND ADD (reinforces rare paths / L3+ rules)"
    else:
      verdict = "SKIP (redundant with existing TMs; pass --force-add to add anyway)"

    print(
      f"- {truth_rec['name']} ({cand.tm})\n"
      f"  Truth: category={truth_rec['category']} | block_size={truth_rec['block_size']} | "
      f"sim_decidable={truth_rec['sim_decidable']} (decision_loops={truth_rec['decision_loops']})\n"
      f"  Suite ({suite_name}) budget: max_loops={suite_entry['max_loops']} | "
      f"tape_limit={suite_entry['tape_limit']} -> "
      f"{suite_entry['baseline_status']} ({suite_entry['baseline_reason']}), "
      f"L{max_lvl}, {suite_entry['baseline_loops']} loops, {suite_entry['baseline_sim_time_us'] / 1000:.1f}ms\n"
      f"  Coverage delta: +{len(new_lines)} new lines, +{len(new_branches)} new branches, "
      f"+{len(new_behav)} new behavioral tags, +{len(rare_feats)} rare features (<3 hits)\n"
      f"  Verdict: {verdict}\n"
    )

    reports.append(
      {
        "truth": truth_rec,
        "entry": {**truth_rec, **suite_entry},
        "already_in_dataset": already_in,
        "new_lines": len(new_lines),
        "new_branches": len(new_branches),
        "new_behav": len(new_behav),
        "rare_feats": len(rare_feats),
        "verdict": verdict,
      }
    )

    should_add = force_add or (add_to_dataset and not already_in and verdict.startswith("RECOMMEND ADD"))
    if should_add:
      if already_in:
        existing_entries = [e for e in existing_entries if e["tm"] != cand.tm]
      existing_entries.append(suite_entry)
      existing_tms.add(cand.tm)
      added_suite_entries.append(suite_entry)
      for f in feats:
        baseline_counts[f] += 1

  if truth_dirty:
    write_truth_file(truth_by_tm, TRUTH_FILE)
    print(f"Updated truth records in {TRUTH_FILE}.")

  if added_suite_entries:
    slim_entries = [_strip_to_suite_entry(e) for e in existing_entries]
    write_dataset_jsonl(ds_path, slim_entries)
    print(f"Saved {len(added_suite_entries)} TM(s) to {ds_path} (total: {len(slim_entries)} TMs).")

  return reports


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description="Truth database & curated Macro Simulator dataset manager")
  sub = parser.add_subparsers(dest="subcommand", required=True)

  p_build = sub.add_parser("build", help="Discover any new truth records and rebuild fast.jsonl and full.jsonl")
  p_build.add_argument("--fast-size", type=int, default=500, help="Target TM count for fast.jsonl [default: 500]")
  p_build.add_argument("--full-size", type=int, default=2000, help="Target TM count for full.jsonl [default: 2000]")
  p_build.add_argument("--max-candidates", type=int, default=2200, help="Max total truth pool size [default: 2200]")
  p_build.add_argument("--seed", type=int, default=42)

  p_select = sub.add_parser("select", help="Rebuild fast.jsonl and full.jsonl from existing benchmarks/truth.jsonl")
  p_select.add_argument("--fast-size", type=int, default=500)
  p_select.add_argument("--full-size", type=int, default=2000)

  p_truth = sub.add_parser("add-truth", help="Step 1: Discover and record ground truth for TM(s) in truth.jsonl")
  p_truth.add_argument("-n", "--block-size", type=int, default=None, help="Explicit fixed block_size (e.g. -n 4)")
  p_truth.add_argument("--category", choices=["halt", "inf", "holdout", "unknown"], default="unknown")
  p_truth.add_argument("--name", default=None, help="Optional human-readable name")
  p_truth.add_argument("--max-loops", type=int, default=1_000_000, help="Discovery max_loops [default: 1000000]")
  p_truth.add_argument("--tape-limit", type=int, default=200, help="Discovery tape_limit [default: 200]")
  p_truth.add_argument("--time-limit", type=float, default=30.0, help="Discovery timeout in seconds [default: 30.0]")
  p_truth.add_argument("--mandatory", action="store_true", help="Mark as mandatory anchor TM")
  p_truth.add_argument("candidates", nargs="+", help="TM name(s) in truth.jsonl (e.g. Green-17), TM strings, or files")

  p_eval = sub.add_parser(
    "eval-candidate",
    help="Step 2: Evaluate candidate TM(s) against a suite dataset and optionally add them",
  )
  p_eval.add_argument("--dataset", default="fast", help="Dataset name ('fast', 'full') or path [default: fast]")
  p_eval.add_argument("-n", "--block-size", type=int, default=None, help="Explicit fixed block_size (e.g. -n 4)")
  p_eval.add_argument("--category", choices=["halt", "inf", "holdout", "unknown"], default="unknown")
  p_eval.add_argument("--name", default=None, help="Optional human-readable name for the TM")
  p_eval.add_argument("--max-loops", type=int, default=None, help="Override suite max_loops")
  p_eval.add_argument("--tape-limit", type=int, default=None, help="Override suite tape_limit")
  p_eval.add_argument("--save-truth", action="store_true", help="Also save discovered truth record to truth.jsonl")
  p_eval.add_argument("--add", action="store_true", help="Append recommended TMs to the dataset file")
  p_eval.add_argument("--force-add", action="store_true", help="Append/update TM regardless of recommendation")
  p_eval.add_argument("candidates", nargs="+", help="One or more TM strings or file paths")

  p_stats = sub.add_parser("stats", help="Print breakdown of truth.jsonl or a suite dataset ('fast', 'full')")
  p_stats.add_argument("dataset", help="'truth', 'fast', 'full', or path to .jsonl")

  args = parser.parse_args(argv)
  if args.subcommand == "build":
    build_datasets(
      fast_size=args.fast_size,
      full_size=args.full_size,
      seed=args.seed,
      max_candidates=args.max_candidates,
    )
    return 0
  elif args.subcommand == "select":
    select_datasets_from_truth(fast_size=args.fast_size, full_size=args.full_size)
    return 0
  elif args.subcommand == "add-truth":
    added_or_updated = add_truth_command(
      args.candidates,
      block_size=args.block_size,
      category=args.category,
      name_override=args.name,
      max_loops=args.max_loops,
      tape_limit=args.tape_limit,
      time_limit_sec=args.time_limit,
      mandatory=args.mandatory,
    )
    return 0 if added_or_updated else 1
  elif args.subcommand == "eval-candidate":
    evaluate_candidates_against_dataset(
      args.dataset,
      args.candidates,
      add_to_dataset=args.add,
      force_add=args.force_add,
      save_truth=args.save_truth,
      block_size=args.block_size,
      category=args.category,
      name_override=args.name,
      max_loops=args.max_loops,
      tape_limit=args.tape_limit,
    )
    return 0
  elif args.subcommand == "stats":
    if args.dataset == "truth":
      truth_by_tm = load_truth(TRUTH_FILE)
      entries = list(truth_by_tm.values())
      print(f"Truth DB: {TRUTH_FILE} ({len(entries)} TMs)")
      print("  By category:", dict(collections.Counter(e["category"] for e in entries)))
      print("  By sim_decidable:", dict(collections.Counter(e["sim_decidable"] for e in entries)))
      print("  By source:  ", dict(collections.Counter(e["source"] for e in entries)))
      print("  By block_size:", dict(collections.Counter(e["block_size"] for e in entries)))
      print("  By max_rule_level:", dict(collections.Counter(e.get("max_rule_level", 0) for e in entries)))
    else:
      path, entries = load_dataset(args.dataset)
      print(f"Dataset: {path} ({len(entries)} TMs)")
      print("  By category:", dict(collections.Counter(e.get("category", "unknown") for e in entries)))
      print("  By baseline_status:", dict(collections.Counter(e.get("baseline_status", "unknown") for e in entries)))
      print("  By source:  ", dict(collections.Counter(e.get("source", "unknown") for e in entries)))
      print("  By block_size:", dict(collections.Counter(e.get("block_size", 1) for e in entries)))
      print("  By baseline_max_level:", dict(collections.Counter(e.get("baseline_max_level", 0) for e in entries)))
    return 0
  return 0


if __name__ == "__main__":
  sys.exit(main())
