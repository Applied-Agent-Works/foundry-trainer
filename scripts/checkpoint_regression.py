#!/usr/bin/env python3
"""Run the smallest local checkpoint/resume counterfactual proof.

This is the fast automated correctness test, not the broad timing survey or
the human-facing late/early demonstration.  It proves no-divergence reuse plus
early and late restored suffixes over a small deterministic conveyor suite.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kaggriculture_eval.binding import bind_target
from kaggriculture_eval.checkpoint import audit_cached, baseline_match, evaluate_cached, write_baseline


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prove", action="store_true", help="Run the required no/late/early proof cases.")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "var" / "cache")
    parser.add_argument("--result-dir", type=Path, default=ROOT / "var" / "results")
    parser.add_argument("--steps", type=int, default=144)
    args = parser.parse_args()
    if not args.prove:
        parser.error("the initial evaluator exposes only --prove; it does not search or mutate candidates")

    binding = bind_target()
    suite = [(42, 0), (42, 1), (43, 0), (43, 1)]
    baselines = []
    for seed, seat in suite:
        baseline = baseline_match(binding, seed=seed, seat=seat, steps=args.steps)
        destination = args.cache_dir / f"seed-{seed}-seat-{seat}.json.gz"
        write_baseline(baseline, destination)
        baselines.append(baseline)

    cases = {
        "no_divergence": {"pass_utility": 0.0},
        "late_divergence": {"pass_utility": 50.0},
        "early_divergence": {"pass_utility": 100.0},
    }
    results = {}
    for name, override in cases.items():
        rows = [audit_cached(binding, evaluate_cached(binding, baseline, override), override) for baseline in baselines]
        if any(row["audit_status"] != "passed" for row in rows):
            raise SystemExit(f"clean audit failed for {name}")
        results[name] = rows

    # These assertions make the intentional proof shape explicit.
    assert all(row["mode"] == "reused-baseline" for row in results["no_divergence"])
    assert all(row["mode"] == "restored-suffix" and 0 < row["first_divergence_turn"] < args.steps - 1 for row in results["late_divergence"])
    assert all(row["mode"] == "restored-suffix" and row["first_divergence_turn"] == 0 for row in results["early_divergence"])

    report = {"proof": "checkpoint-resume-incremental-counterfactual-regression", "binding": {"target_root": str(binding.root), "target_revision": binding.revision, "shared_sha256": binding.shared_sha256, "engine_sha256": binding.engine_sha256}, "suite": {"opponent": "target.carrot_conveyor_agent", "seeds": [42, 43], "seats": [0, 1], "steps": args.steps}, "results": results}
    args.result_dir.mkdir(parents=True, exist_ok=True)
    destination = args.result_dir / "checkpoint-resume-proof.json"
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Proof passed: {len(suite)} matches × 3 audited cases")
    print(f"Wrote {destination}")


if __name__ == "__main__":
    main()
