#!/usr/bin/env python3
"""Compare the carrot policy's seed-opportunity value across a fixed suite.

This is a controlled *two-value comparison*, not an automatic parameter search.
It compares the documented default value (20.0) with a human-selected candidate
(80.0), holds the game configuration/opponent/seeds/seats constant, and audits
every fast checkpoint result against a clean direct candidate rerun.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kaggriculture_eval.binding import bind_target
from kaggriculture_eval.checkpoint import audit_cached, baseline_match, clean_rerun, evaluate_cached, write_baseline


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(range(42, 52)))
    parser.add_argument("--steps", type=int, default=720)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "var" / "results" / "seed-opportunity-20-vs-80")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "var" / "cache" / "seed-opportunity-20-vs-80")
    args = parser.parse_args()

    binding = bind_target()
    game = importlib.import_module("kaggriculture")
    if Path(game.__file__).resolve().parent != binding.root:
        raise RuntimeError("pass opponent did not resolve from the explicit target binding")
    opponent = game.agents["pass"]
    baseline_override = {"seed_opportunity_value": 20.0}
    candidate_override = {"seed_opportunity_value": 80.0}

    rows = []
    for seed in args.seeds:
        for seat in (0, 1):
            # Baseline captures a state before every action.  Its output must
            # agree with the equivalent direct run before it can support reuse.
            baseline = baseline_match(
                binding, seed=seed, seat=seat, steps=args.steps,
                opponent=opponent, opponent_id="target.kaggriculture.agents.pass",
            )
            direct_baseline = clean_rerun(
                binding, seed=seed, seat=seat, steps=args.steps,
                override=baseline_override, opponent=opponent,
            )
            if baseline["outcome"] != direct_baseline["outcome"]:
                raise SystemExit(f"baseline mismatch for seed {seed}, seat {seat}")
            write_baseline(baseline, args.cache_dir / f"seed-{seed}-seat-{seat}.json.gz")

            candidate = audit_cached(
                binding, evaluate_cached(binding, baseline, candidate_override, opponent),
                candidate_override, opponent,
            )
            if candidate["audit_status"] != "passed":
                raise SystemExit(f"candidate audit failed for seed {seed}, seat {seat}")

            baseline_reward = baseline["outcome"]["decision_reward"]
            candidate_reward = candidate["outcome"]["decision_reward"]
            rows.append({
                "seed": seed,
                "seat": seat,
                "baseline_outcome": baseline["outcome"],
                "candidate_outcome": candidate["outcome"],
                "reward_delta": candidate_reward - baseline_reward,
                "first_divergence_turn": candidate["first_divergence_turn"],
                "suffix_actions": candidate["suffix_actions"],
                "mode": candidate["mode"],
                "audit_status": candidate["audit_status"],
                "equivalent_baseline_direct_seconds": direct_baseline["elapsed_seconds"],
                "candidate_cached_seconds": candidate["replay_elapsed_seconds"] + candidate["suffix_elapsed_seconds"],
                "candidate_clean_seconds": candidate["clean_audit"]["elapsed_seconds"],
            })
            print(
                f"seed {seed}, seat {seat}: delta {candidate_reward - baseline_reward:+.0f}, "
                f"divergence {candidate['first_divergence_turn']}, audit passed",
                flush=True,
            )

    deltas = [row["reward_delta"] for row in rows]
    divergences = [row["first_divergence_turn"] for row in rows if row["first_divergence_turn"] is not None]
    report = {
        "schema_version": 1,
        "purpose": "compare one named carrot policy preference across fixed matched seeds and seats",
        "binding": {
            "target_root": str(binding.root), "target_revision": binding.revision,
            "shared_sha256": binding.shared_sha256, "engine_sha256": binding.engine_sha256,
        },
        "controls": {
            "opponent": "target.kaggriculture.agents.pass", "opponent_deterministic": True,
            "seeds": args.seeds, "seats": [0, 1], "steps": args.steps,
        },
        "parameter": {
            "name": "seed_opportunity_value", "baseline_value": 20.0,
            "candidate_value": 80.0,
            "note": "Policy preference only; the fixed game carrot seed cost remains 20.",
        },
        "summary": {
            "matches": len(rows),
            "mean_baseline_reward": mean(row["baseline_outcome"]["decision_reward"] for row in rows),
            "mean_candidate_reward": mean(row["candidate_outcome"]["decision_reward"] for row in rows),
            "mean_reward_delta": mean(deltas),
            "candidate_better": sum(delta > 0 for delta in deltas),
            "candidate_worse": sum(delta < 0 for delta in deltas),
            "candidate_tied": sum(delta == 0 for delta in deltas),
            "no_divergence": sum(row["first_divergence_turn"] is None for row in rows),
            "mean_first_divergence_turn": mean(divergences) if divergences else None,
            "mean_suffix_actions": mean(row["suffix_actions"] for row in rows),
            "all_clean_audits_passed": all(row["audit_status"] == "passed" for row in rows),
            "conclusion": "No keep/reject conclusion: acceptance threshold was not predeclared.",
        },
        "matches": rows,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    destination = args.output_dir / "summary.json"
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"], indent=2))
    print(f"Wrote {destination}")


if __name__ == "__main__":
    main()
