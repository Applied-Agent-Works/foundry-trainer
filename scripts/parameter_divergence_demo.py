#!/usr/bin/env python3
"""Repeat the late/early parameter-divergence demo with exact clean audits.

Each case is deliberately one named ``CarrotParameters`` override.  The
candidate is replayed through cached baseline observations, then its first
different action restores the pre-action simulator state and runs only the
remaining suffix.  A complete candidate rerun is retained as the audit oracle.
The built-in ``pass`` opponent is chosen here because it is deterministic:
fast and clean outcomes must match exactly.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kaggriculture_eval.carrot_adapter import CARROT_ADAPTER
from kaggriculture_eval.binding import bind_target
from kaggriculture_eval.checkpoint import audit_cached, baseline_match, clean_rerun, evaluate_cached, write_baseline


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "var" / "results" / "parameter-divergence-demo")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "var" / "cache" / "parameter-divergence-demo")
    parser.add_argument(
        "--case", choices=("late", "early", "both"), default="both",
        help="Run one named demonstration case, or both (default: both).",
    )
    args = parser.parse_args()
    binding = bind_target(adapter=CARROT_ADAPTER)
    game = importlib.import_module("kaggriculture")
    if Path(game.__file__).resolve().parent != binding.root:
        raise RuntimeError("pass opponent did not resolve from the explicit target binding")
    opponent = game.agents["pass"]
    cases = {
        # Selected from this run's fresh 140-match trace sweep: seed 47 has
        # a late first change at turn 206; seed 42 changes at turn zero.
        "late": {"seed": 47, "seat": 0, "override": {"seed_opportunity_value": 80.0}},
        "early": {"seed": 42, "seat": 0, "override": {"seed_opportunity_value": 150.0}},
    }
    if args.case != "both":
        cases = {args.case: cases[args.case]}
    results = {}
    for label, case in cases.items():
        # Each baseline holds every pre-action state.  This is intentionally
        # different from the timing sweep's observation/action-only traces.
        baseline = baseline_match(binding, seed=case["seed"], seat=case["seat"], steps=720, opponent=opponent, opponent_id="target.kaggriculture.agents.pass")
        write_baseline(baseline, args.cache_dir / f"{label}-baseline.json.gz")
        # This is the performance baseline. It has the same direct `.step()`
        # executor and every gameplay control matched to the candidate audit.
        # Its one named override equals the default value, so policy behavior
        # must be unchanged. Checkpoint capture time is reported separately.
        equivalent_baseline = clean_rerun(
            binding, seed=case["seed"], seat=case["seat"], steps=720,
            override={"seed_opportunity_value": 20.0}, opponent=opponent,
        )
        if equivalent_baseline["outcome"] != baseline["outcome"]:
            raise SystemExit(f"{label} checkpoint baseline does not match equivalent direct baseline")
        result = audit_cached(binding, evaluate_cached(binding, baseline, case["override"], opponent), case["override"], opponent)
        # A mismatched audit makes the counterfactual result unusable.
        if result["audit_status"] != "passed":
            raise SystemExit(f"{label} cached result did not equal clean rerun")
        result["timing_contract"] = {
            "equivalent_baseline_direct_seconds": equivalent_baseline["elapsed_seconds"],
            "candidate_clean_seconds": result["clean_audit"]["elapsed_seconds"],
            "candidate_replay_seconds": result["replay_elapsed_seconds"],
            "candidate_suffix_seconds": result["suffix_elapsed_seconds"],
            "candidate_cached_total_seconds": result["replay_elapsed_seconds"] + result["suffix_elapsed_seconds"],
            "checkpoint_capture_seconds": baseline["baseline_elapsed_seconds"],
        }
        results[label] = result
    if "late" in results and not 0 < results["late"]["first_divergence_turn"] < 719:
        raise SystemExit("late case did not produce a late divergence")
    if "early" in results and results["early"]["first_divergence_turn"] != 0:
        raise SystemExit("early case did not produce turn-zero divergence")
    report = {"schema_version": 1, "binding": {"target_root": str(binding.root), "target_revision": binding.revision, "shared_sha256": binding.shared_sha256, "engine_sha256": binding.engine_sha256}, "opponent": "target.kaggriculture.agents.pass", "results": results}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    destination = args.output_dir / "summary.json"
    destination.write_text(json.dumps(report, indent=2) + "\n")
    for label, row in results.items():
        timing = row["timing_contract"]
        print(
            f"{label}: turn {row['first_divergence_turn']}, suffix {row['suffix_actions']}, "
            f"cached {timing['candidate_cached_total_seconds']:.3f}s vs clean "
            f"{timing['candidate_clean_seconds']:.3f}s, audit {row['audit_status']}"
        )
    print(f"Wrote {destination}")


if __name__ == "__main__":
    main()
