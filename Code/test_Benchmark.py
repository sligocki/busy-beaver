#!/usr/bin/env python3
"""
Unit tests for Benchmark.py, Benchmark_Dataset.py, and Simulator max-span tracking.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from Benchmark import (
  CONFIG_PRESETS,
  PRESET_GROUPS,
  BenchConfig,
  compare_runs,
  encode_knuth10_interval,
  load_dataset,
  load_run_results,
  run_benchmark_config,
  run_single_tm,
)
from Benchmark_Dataset import (
  CandidateTM,
  iter_green_candidates,
  resolve_block_size_and_profile,
  select_diverse_subset,
  write_dataset_jsonl,
)
import IO
from Macro import Simulator, Turing_Machine
from Macro.Proof_System import ProverLevel


class BenchmarkTest(unittest.TestCase):
  def test_prover_level_hierarchy(self):
    # Level 0: prover off
    c0 = BenchConfig(name="lvl0", prover_level=ProverLevel.NONE)
    self.assertFalse(c0.prover)
    self.assertFalse(c0.recursive)
    self.assertFalse(c0.exp_linear_rules)
    self.assertFalse(c0.exp_meta_linear_rules)

    # Level 1: base prover only
    c1 = BenchConfig(name="lvl1", prover_level=ProverLevel.BASE)
    self.assertTrue(c1.prover)
    self.assertFalse(c1.recursive)
    self.assertFalse(c1.exp_linear_rules)
    self.assertFalse(c1.exp_meta_linear_rules)

    # Level 2: prover + recursive + exp_linear_rules (EXP)
    c2 = BenchConfig(name="lvl2", prover_level=ProverLevel.EXP)
    self.assertTrue(c2.prover)
    self.assertTrue(c2.recursive)
    self.assertTrue(c2.exp_linear_rules)
    self.assertFalse(c2.exp_meta_linear_rules)

    # Level 3: prover + recursive + exp_linear_rules + exp_meta_linear_rules (ITERATED)
    c3 = BenchConfig(name="lvl3", prover_level=ProverLevel.ITERATED)
    self.assertTrue(c3.prover)
    self.assertTrue(c3.recursive)
    self.assertTrue(c3.exp_linear_rules)
    self.assertTrue(c3.exp_meta_linear_rules)

    # Check preset groups reference valid presets
    for group_name, preset_names in PRESET_GROUPS.items():
      self.assertTrue(len(preset_names) > 0, group_name)
      for p in preset_names:
        self.assertIn(p, CONFIG_PRESETS)

  def test_simulator_max_span_and_backsymbol_invariance(self):
    # Verify that get_max_span() tracks peak span even when only_record_configs=False,
    # and is invariant between backsymbol=True and backsymbol=False.
    tm_str = "1RB1LB_1LA1RZ"  # 2x2-6-4: halts at step 6 with score 4, span 4
    for backsymbol in (False, True):
      cfg = BenchConfig(name="test", prover_level=ProverLevel.NONE, backsymbol=backsymbol, only_record_configs=False)
      opts = cfg.to_options()
      tm = IO.parse_tm(tm_str)
      if backsymbol:
        tm = Turing_Machine.Backsymbol_Macro_Machine(tm)
      sim = Simulator.Simulator(tm, opts)
      records_seen = []
      sim.on_record_span = lambda s: records_seen.append(int(s.get_max_span()))
      sim.loop_run(50)
      self.assertEqual(sim.op_state, Turing_Machine.HALT)
      self.assertEqual(int(sim.get_max_span()), 4)
      self.assertTrue(len(records_seen) > 0)
      self.assertEqual(records_seen[-1], 4)

    # Also test with block_size=2
    tm_str_3x2 = "1RB1RZ_1LB0RC_1LC1LA"  # 3x2-14-6
    spans = []
    for backsymbol in (False, True):
      cfg = BenchConfig(name="test_b2", prover_level=ProverLevel.BASE, backsymbol=backsymbol)
      opts = cfg.to_options()
      m = Turing_Machine.Block_Macro_Machine(IO.parse_tm(tm_str_3x2), 2)
      if backsymbol:
        m = Turing_Machine.Backsymbol_Macro_Machine(m)
      sim = Simulator.Simulator(m, opts)
      sim.loop_run(50)
      self.assertEqual(sim.op_state, Turing_Machine.HALT)
      spans.append(int(sim.get_max_span()))
    self.assertEqual(spans[0], spans[1])

  def test_milestone_callback_and_undecided_modes(self):
    # Counter machine grows tape log2(steps) without halting
    with open(Path(__file__).resolve().parent.parent / "Machines" / "2x2-Counter", "rt") as f:
      counter_tm = f.readline().strip().split()[0]

    entry = {
      "tm": counter_tm,
      "name": "2x2-Counter",
      "category": "holdout",
      "block_size": 1,
      "max_loops": 200,
      "tape_limit": 50,
      "target_max_span_bi": [6],  # Reach span >= 6 (happens around loop 25)
    }
    # With prover_0_none, it won't prove infinity and will run as undecided
    cfg_off = CONFIG_PRESETS["prover_0_none"].to_dict()

    res_milestone = run_single_tm(entry, cfg_off, undecided_mode="milestone")
    self.assertEqual(res_milestone["status"], "unknown")
    self.assertEqual(res_milestone["reason"], "reached_milestone")
    self.assertTrue(res_milestone["milestone_reached"])
    self.assertIsNotNone(res_milestone["milestone_loops"])
    self.assertLess(res_milestone["total_loops"], 200)

    res_both = run_single_tm(entry, cfg_off, undecided_mode="both")
    self.assertEqual(res_both["status"], "unknown")
    self.assertEqual(res_both["reason"], "over_loops")
    self.assertTrue(res_both["milestone_reached"])
    self.assertEqual(res_both["milestone_loops"], res_milestone["milestone_loops"])
    self.assertEqual(res_both["total_loops"], 200)

  def test_resolve_block_size_guarantees_halting(self):
    # 2x6-t70 fails to halt in 15,000 loops with block_size=1 (which Block_Finder picks),
    # but halts at loop 10,498 with block_size=2.
    cand = CandidateTM(
      tm="1RB2LA1RA4LA5RA0LB_1LA3RA2RB1RZ3RB4LA",
      name="2x6-t70-test",
      source="test",
      category="halt",
      block_size=None,  # Force Block_Finder + fallback sweep
      max_loops=15_000,
    )
    entry, feats = resolve_block_size_and_profile(cand, profile_coverage=True, time_limit_sec=5.0)
    self.assertIsNotNone(entry)
    self.assertEqual(entry["block_size"], 2)
    self.assertEqual(entry["baseline_status"], "halt")
    self.assertGreater(len(feats), 20)

  def test_coverage_profiler_and_greedy_set_cover(self):
    cands = iter_green_candidates(max_states=9)[:4]  # Green 6, 7, 8, 9
    profiled = []
    for c in cands:
      c.mandatory = False
      entry, feats = resolve_block_size_and_profile(c, profile_coverage=True, time_limit_sec=2.0)
      self.assertIsNotNone(entry)
      has_line = any(f[0] == "line" for f in feats)
      has_branch = any(f[0] == "branch" for f in feats)
      has_behav = any(str(f[0]).startswith("behav_") for f in feats)
      self.assertTrue(has_line)
      self.assertTrue(has_branch)
      self.assertTrue(has_behav)
      profiled.append((entry, feats))

    selected, stats = select_diverse_subset(profiled, target_count=2, min_k_coverage=1)
    self.assertEqual(len(selected), 2)
    self.assertGreater(stats["covered_features"], 0)

  def test_compare_runs_correctness_and_coverage(self):
    base_meta = {"config_name": "default", "git_sha": "abc1234"}
    base_results = [
      {
        "tm": "TM_HALT_1",
        "name": "Halt-1",
        "category": "halt",
        "status": "halt",
        "reason": "HALT",
        "sim_time_us": 1000,
        "eval_time_us": 50,
        "total_loops": 100,
        "max_rule_level": 1,
        "halt_score": encode_knuth10_interval(42),
        "max_span": encode_knuth10_interval(10),
        "milestone_reached": False,
        "milestone_loops": None,
        "milestone_time_us": None,
        "threw_exception": False,
      },
      {
        "tm": "TM_HOLDOUT_1",
        "name": "Holdout-1",
        "category": "holdout",
        "status": "unknown",
        "reason": "over_loops",
        "sim_time_us": 5000,
        "eval_time_us": 50,
        "total_loops": 1000,
        "max_rule_level": 2,
        "halt_score": encode_knuth10_interval(None),
        "max_span": encode_knuth10_interval(500),
        "milestone_reached": True,
        "milestone_loops": 400,
        "milestone_time_us": 2000,
        "threw_exception": False,
      },
    ]

    # Valid candidate run: faster and decides a holdout TM (celebrated coverage improvement!)
    good_meta = {"config_name": "all_on", "git_sha": "abc1234"}
    good_results = [
      {
        **base_results[0],
        "sim_time_us": 500,
      },
      {
        **base_results[1],
        "status": "inf",
        "reason": "INF_PROOF_SYSTEM",
      },
    ]
    summary_ok, report_ok = compare_runs(base_meta, base_results, [(good_meta, good_results)])
    self.assertTrue(summary_ok["correctness_passed"])
    self.assertIn("0 correctness errors", report_ok)
    self.assertEqual(summary_ok["coverage"]["all_on"]["newly_decided"], ["Holdout-1"])
    self.assertIn("Newly Decided TMs", report_ok)

    # Bad candidate run: flips Halt -> Inf
    bad_meta = {"config_name": "buggy", "git_sha": "def5678"}
    bad_results = [
      {
        **base_results[0],
        "status": "inf",
        "reason": "INF_PROOF_SYSTEM",
      },
      {
        **base_results[1],
      },
    ]
    summary_bad, _ = compare_runs(base_meta, base_results, [(bad_meta, bad_results)])
    self.assertFalse(summary_bad["correctness_passed"])
    self.assertGreaterEqual(len(summary_bad["correctness_errors"]), 2)

  def test_end_to_end_dataset_and_benchmark_io(self):
    with tempfile.TemporaryDirectory() as tmp:
      tmp_dir = Path(tmp)
      ds_path = tmp_dir / "tiny.jsonl"
      truth_path = tmp_dir / "truth.jsonl"
      out_path = tmp_dir / "res.jsonl.gz"

      truth_entries = [
        {
          "tm": "1RB1LB_1LA1RZ",
          "name": "2x2-6-4",
          "source": "test",
          "category": "halt",
          "block_size": 1,
          "max_steps_in_block": 100_000,
          "max_steps_in_backsymbol": 1_000,
          "sim_decidable": True,
          "decision_loops": 4,
          "expected_score_exact": 4,
        }
      ]
      suite_entries = [
        {
          "tm": "1RB1LB_1LA1RZ",
          "name": "2x2-6-4",
          "max_loops": 100,
          "tape_limit": 50,
          "target_max_span_bi": None,
        }
      ]
      write_dataset_jsonl(truth_path, truth_entries)
      write_dataset_jsonl(ds_path, suite_entries)
      loaded_path, loaded_entries = load_dataset(ds_path, truth_path=truth_path)
      self.assertEqual(loaded_path, ds_path)
      self.assertEqual(len(loaded_entries), 1)
      self.assertEqual(loaded_entries[0]["category"], "halt")
      self.assertEqual(loaded_entries[0]["block_size"], 1)

      _, meta, results = run_benchmark_config(
        entries=loaded_entries,
        config=CONFIG_PRESETS["default"],
        dataset_name="tiny",
        jobs=1,
        out_path=out_path,
        quiet=True,
      )
      self.assertEqual(len(results), 1)
      self.assertEqual(results[0]["status"], "halt")
      self.assertEqual(results[0]["halt_score"]["exact"], 4)

      rmeta, rres = load_run_results(out_path)
      self.assertEqual(rmeta["config_name"], "default")
      self.assertEqual(len(rres), 1)

  def test_compare_lists_lost_decisions_with_exception(self):
    base_meta = {"config_name": "base", "git_sha": "abc1234"}
    cand_meta = {"config_name": "cand", "git_sha": "def5678"}
    base_rec = {
      "tm": "1RB1LB_1LA1RZ",
      "name": "2x2-6-4",
      "category": "inf",
      "status": "inf",
      "reason": "INF_PROOF_SYSTEM",
      "sim_time_us": 100,
      "eval_time_us": 10,
      "total_loops": 50,
      "max_rule_level": 2,
      "halt_score": encode_knuth10_interval(None),
      "max_span": encode_knuth10_interval(10),
      "milestone_reached": False,
      "milestone_loops": None,
      "milestone_time_us": None,
      "threw_exception": False,
      "exception_str": "",
    }
    cand_rec = {
      **base_rec,
      "status": "unknown",
      "reason": "threw_exception",
      "sim_time_us": 200,
      "total_loops": 30,
      "max_rule_level": 1,
      "threw_exception": True,
      "exception_str": "ValueError: boom",
    }
    _, report = compare_runs(base_meta, [base_rec], [(cand_meta, [cand_rec])])
    self.assertIn("### Lost Decisions (vs Baseline)", report)
    self.assertIn("**[cand]** `2x2-6-4`", report)
    self.assertIn("exception: ValueError: boom", report)

  def test_loop_multiplier_scales_max_loops(self):
    with open(Path(__file__).resolve().parent.parent / "Machines" / "2x2-Counter", "rt") as f:
      counter_tm = f.readline().strip().split()[0]

    entry = {
      "tm": counter_tm,
      "name": "2x2-Counter",
      "category": "holdout",
      "block_size": 1,
      "max_loops": 20,
      "tape_limit": 50,
    }
    cfg = CONFIG_PRESETS["prover_0_none"].to_dict()
    res_1x = run_single_tm(entry, cfg, undecided_mode="full", loop_multiplier=1.0)
    res_5x = run_single_tm(entry, cfg, undecided_mode="full", loop_multiplier=5.0)
    self.assertEqual(res_1x["status"], "unknown")
    self.assertEqual(res_5x["status"], "unknown")
    self.assertEqual(res_1x["total_loops"], 20)
    self.assertEqual(res_5x["total_loops"], 100)

  def test_matrix_invalid_baseline_config_raises(self):
    import Benchmark

    with self.assertRaises(ValueError):
      Benchmark.main(
        [
          "matrix",
          "--dataset",
          "fast",
          "--baseline-config",
          "prover_3_iterated,ablate_const_blocks",
          "--config",
          "prover_3_iterated",
        ]
      )

  def test_parse_candidate_specs_pb_file(self):
    import Benchmark_Dataset
    import IO
    from IO import TM_Record

    with tempfile.TemporaryDirectory() as tmpdir:
      pb_path = Path(tmpdir) / "sample.pb"
      tm_str = "1RB1LB_1LA1RZ"
      rec = TM_Record.TM_Record()
      TM_Record.write_tm(IO.parse_tm(tm_str), rec.proto.tm)
      rec.proto.filter.simulator.parameters.block_size = 3
      rec.proto.status.halt_status.is_decided = True
      rec.proto.status.halt_status.is_halting = True
      with IO.Proto.Writer(pb_path) as writer:
        writer.write_record(rec)

      cands = Benchmark_Dataset._parse_candidate_specs(
        [str(pb_path)],
        block_size=None,
        category="unknown",
        name_override=None,
        max_loops=1000,
        tape_limit=50,
      )
      self.assertEqual(len(cands), 1)
      self.assertEqual(cands[0].tm, tm_str)
      self.assertEqual(cands[0].name, "sample.pb:0")
      self.assertEqual(cands[0].source, "custom")
      self.assertEqual(cands[0].block_size, 3)
      self.assertEqual(cands[0].category, "halt")

      # Explicit CLI block_size, category, name, and source override protobuf metadata.
      cands_override = Benchmark_Dataset._parse_candidate_specs(
        [str(pb_path)],
        block_size=4,
        category="inf",
        name_override="custom-name",
        max_loops=1000,
        tape_limit=50,
        source_override="exceptions",
      )
      self.assertEqual(cands_override[0].name, "custom-name")
      self.assertEqual(cands_override[0].source, "exceptions")
      self.assertEqual(cands_override[0].block_size, 4)
      self.assertEqual(cands_override[0].category, "inf")

  def test_compare_reports_wide_intervals_improvements_and_regressions(self):
    from Big_Interval import BigInterval, Knuth10

    base_meta = {"config_name": "base", "git_sha": "abc1234"}
    cand_meta = {"config_name": "cand", "git_sha": "def5678"}

    tight_enc = encode_knuth10_interval(BigInterval(Knuth10(3010, 1), Knuth10(3012, 1)))
    wide_zero_enc = encode_knuth10_interval(BigInterval(Knuth10(0), Knuth10(442057658763040, 7)))
    wide_arrow_enc = encode_knuth10_interval(
      BigInterval(Knuth10(2161856886993690, 0, 1, 7), Knuth10(2161856886993945, 0, 1, 0, 1))
    )

    def _rec(tm, name, halt_score, max_span):
      return {
        "tm": tm,
        "name": name,
        "category": "halt",
        "status": "halt",
        "reason": "HALT",
        "sim_time_us": 100,
        "eval_time_us": 10,
        "total_loops": 50,
        "max_rule_level": 2,
        "halt_score": halt_score,
        "max_span": max_span,
        "milestone_reached": False,
        "milestone_loops": None,
        "milestone_time_us": None,
        "threw_exception": False,
        "exception_str": "",
      }

    # TM1: fixed wide interval (wide in base -> tight in cand)
    # TM2: regressed wide interval (tight in base -> wide in cand)
    base_results = [
      _rec("TM1", "Fixed-TM", wide_zero_enc, wide_zero_enc),
      _rec("TM2", "Regressed-TM", tight_enc, tight_enc),
    ]
    cand_results = [
      _rec("TM1", "Fixed-TM", tight_enc, tight_enc),
      _rec("TM2", "Regressed-TM", wide_arrow_enc, wide_arrow_enc),
    ]
    summary, report = compare_runs(base_meta, base_results, [(cand_meta, cand_results)])
    self.assertIn("## 4. BigInterval Quality (Wide Interval Warnings)", report)
    self.assertIn("### Fixed Wide Intervals (Improvements vs Baseline)", report)
    self.assertIn("### Newly Wide Intervals (Regressions vs Baseline)", report)
    self.assertEqual(summary["wide_intervals"]["base"]["wide_tms"], 1)
    self.assertEqual(summary["wide_intervals"]["base"]["zero_lower"], 1)
    self.assertEqual(summary["wide_intervals"]["cand"]["wide_tms"], 1)
    self.assertEqual(summary["wide_intervals"]["cand"]["zero_lower"], 0)
    self.assertEqual(summary["wide_intervals"]["cand"]["fixed_wide"], ["Fixed-TM"])
    self.assertEqual(summary["wide_intervals"]["cand"]["new_wide"], ["Regressed-TM"])


if __name__ == "__main__":
  unittest.main()
