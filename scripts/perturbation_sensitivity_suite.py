#!/usr/bin/env python3
"""Run the documented local +/-10% CarrotParameters sensitivity screen.

This is intentionally a fixed, human-readable matrix rather than a search:
eleven nonzero policy fields, each at one negative and one positive change.
It never writes to Kaggriculture.  Every cached counterfactual is compared to
a complete clean rerun of the identical seed, seat, steps, and conveyor
opponent.  A failed clean audit aborts that candidate and marks the suite
incomplete.

The default 60-match suite is seeds 42--71 in both seats.  Four candidates
are evaluated concurrently by default because they use independent, immutable
baseline cache files.  Set --workers 1 for completely serial timing.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import statistics
import sys
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kaggriculture_eval.binding import bind_target
from kaggriculture_eval.checkpoint import (
    audit_cached,
    baseline_match,
    evaluate_cached,
    read_baseline,
    write_baseline,
)


# Kept in source (rather than inferred at runtime) so the exact human-reviewed
# experiment matrix remains stable even if a future policy adds a field.
MATRIX: tuple[tuple[str, float, float], ...] = (
    ("supply_high_given_zero_ripe", 0.045, 0.055),
    ("supply_high_given_one_to_three_ripe", 0.27, 0.33),
    ("supply_high_given_four_plus_ripe", 0.63, 0.77),
    ("low_price_multiplier", 0.54, 0.66),
    ("high_price_multiplier", 1.08, 1.32),
    ("low_price_base", 0.135, 0.165),
    ("low_price_supply_weight", 0.585, 0.715),
    ("high_price_base", 0.045, 0.055),
    ("high_price_demand_weight", 0.018, 0.022),
    ("high_price_supply_penalty", 0.27, 0.33),
    ("seed_opportunity_value", 18.0, 22.0),
)

# A human-selected follow-up after the observed margin report.  Unlike the
# default screen, seed opportunity has four deliberately coarse values because
# the earlier 20 -> 80 demonstration established a threshold response.  The
# pass values are the documented absolute pair around its zero baseline.
COARSE_PREFERENCE_CASES: tuple[dict[str, float], ...] = (
    {"seed_opportunity_value": 10.0},
    {"seed_opportunity_value": 40.0},
    {"seed_opportunity_value": 60.0},
    {"seed_opportunity_value": 80.0},
    {"pass_utility": -25.0},
    {"pass_utility": 25.0},
)


def _cache_path(cache_dir: Path, seed: int, seat: int) -> Path:
    return cache_dir / f"seed-{seed}-seat-{seat}.json.gz"


def _candidate_cases() -> list[dict[str, float]]:
    return [{name: value} for name, negative, positive in MATRIX for value in (negative, positive)]


def _validate_matrix(binding: Any) -> None:
    defaults = asdict(binding.shared.DEFAULT_PARAMETERS)
    for name, negative, positive in MATRIX:
        if name not in defaults:
            raise ValueError(f"matrix field is absent from target policy: {name}")
        if not negative < defaults[name] < positive:
            raise ValueError(f"matrix values do not bracket the default for {name}")
    defaults = asdict(binding.shared.DEFAULT_PARAMETERS)
    for override in COARSE_PREFERENCE_CASES:
        name = next(iter(override))
        if name not in defaults:
            raise ValueError(f"coarse-screen field is absent from target policy: {name}")


def _load_or_make_baselines(binding: Any, cache_dir: Path, seeds: range, steps: int) -> list[dict[str, Any]]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    baselines = []
    for seed in seeds:
        for seat in (0, 1):
            path = _cache_path(cache_dir, seed, seat)
            if path.exists():
                baseline = read_baseline(path)
                info = baseline["binding"]
                match = baseline["match"]
                valid = (
                    info["target_revision"] == binding.revision
                    and info["shared_sha256"] == binding.shared_sha256
                    and info["engine_sha256"] == binding.engine_sha256
                    and match["steps"] == steps
                    and match["seed"] == seed
                    and match["decision_player"] == seat
                )
                if valid:
                    baselines.append(baseline)
                    continue
            baseline = baseline_match(binding, seed=seed, seat=seat, steps=steps)
            write_baseline(baseline, path)
            baselines.append(baseline)
            print(f"baseline seed {seed}, seat {seat} captured", flush=True)
    return baselines


def _summarize(override: dict[str, float], rows: list[dict[str, Any]], baseline_rewards: dict[tuple[int, int], float]) -> dict[str, Any]:
    deltas = []
    by_seat: dict[int, list[float]] = {0: [], 1: []}
    divergences = []
    suffixes = []
    for row in rows:
        match = row["match"]
        key = (match["seed"], match["decision_player"])
        delta = row["outcome"]["decision_reward"] - baseline_rewards[key]
        deltas.append(delta)
        by_seat[match["decision_player"]].append(delta)
        if row["first_divergence_turn"] is not None:
            divergences.append(row["first_divergence_turn"])
        suffixes.append(row["suffix_actions"])
    change = rows[0]["candidate"]
    return {
        "parameter": change,
        "matches": len(rows),
        "mean_baseline_reward": statistics.mean(baseline_rewards[(r["match"]["seed"], r["match"]["decision_player"])] for r in rows),
        "mean_candidate_reward": statistics.mean(r["outcome"]["decision_reward"] for r in rows),
        "mean_paired_reward_delta": statistics.mean(deltas),
        "median_paired_reward_delta": statistics.median(deltas),
        "candidate_better": sum(delta > 0 for delta in deltas),
        "candidate_worse": sum(delta < 0 for delta in deltas),
        "candidate_tied": sum(delta == 0 for delta in deltas),
        "seat_mean_paired_reward_delta": {str(seat): statistics.mean(values) for seat, values in by_seat.items()},
        "no_divergence_matches": len(rows) - len(divergences),
        "first_divergence_turn": {
            "min": min(divergences) if divergences else None,
            "median": statistics.median(divergences) if divergences else None,
            "max": max(divergences) if divergences else None,
        },
        "mean_suffix_actions": statistics.mean(suffixes),
        "clean_audits_passed": sum(r["audit_status"] == "passed" for r in rows),
        "all_clean_audits_passed": all(r["audit_status"] == "passed" for r in rows),
        "elapsed_cached_seconds": sum(r["replay_elapsed_seconds"] + r["suffix_elapsed_seconds"] for r in rows),
        "elapsed_clean_audit_seconds": sum(r["clean_audit"]["elapsed_seconds"] for r in rows),
    }


def _run_candidate(cache_dir: str, override: dict[str, float], baseline_rewards: dict[tuple[int, int], float]) -> dict[str, Any]:
    """Worker entry point: isolated target binding and 60 complete audits."""
    binding = bind_target()
    rows = []
    for path in sorted(Path(cache_dir).glob("seed-*-seat-*.json.gz")):
        baseline = read_baseline(path)
        row = audit_cached(binding, evaluate_cached(binding, baseline, override), override)
        rows.append(row)
    summary = _summarize(override, rows, baseline_rewards)
    return {"summary": summary, "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "var" / "cache" / "perturbation-sensitivity-60")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--screen", choices=("fine", "coarse-preferences"), default="fine", help="Fixed human-reviewed candidate matrix to run.")
    parser.add_argument("--first-seed", type=int, default=42)
    parser.add_argument("--last-seed", type=int, default=71)
    parser.add_argument("--steps", type=int, default=720)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be at least one")
    seeds = range(args.first_seed, args.last_seed + 1)
    binding = bind_target()
    _validate_matrix(binding)
    started = perf_counter()
    baselines = _load_or_make_baselines(binding, args.cache_dir, seeds, args.steps)
    expected_matches = len(seeds) * 2
    if len(baselines) != expected_matches:
        raise RuntimeError("baseline suite is incomplete")
    baseline_rewards = {(b["match"]["seed"], b["match"]["decision_player"]): b["outcome"]["decision_reward"] for b in baselines}
    cases = _candidate_cases() if args.screen == "fine" else list(COARSE_PREFERENCE_CASES)
    if args.output_dir is None:
        args.output_dir = ROOT / "var" / "results" / ("perturbation-sensitivity-60" if args.screen == "fine" else "coarse-preferences-60")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    completed = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(_run_candidate, str(args.cache_dir), override, baseline_rewards): override for override in cases}
        for position, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            override = futures[future]
            result = future.result()
            name, value = next(iter(override.items()))
            destination = args.output_dir / f"{name}-{value:g}.json"
            destination.write_text(json.dumps(result, indent=2) + "\n")
            completed.append(result["summary"])
            audit = result["summary"]["all_clean_audits_passed"]
            print(f"[{position}/{len(cases)}] {name}={value:g}: delta {result['summary']['mean_paired_reward_delta']:+.2f}, audits {'passed' if audit else 'FAILED'}", flush=True)
            if not audit:
                for pending in futures:
                    pending.cancel()
                raise SystemExit(f"clean audit failed for {name}={value:g}")
    completed.sort(key=lambda row: (row["parameter"]["name"], row["parameter"]["new_value"]))
    report = {
        "schema_version": 1,
        "purpose": f"fixed human-reviewed {args.screen} CarrotParameters screen; not automatic policy mutation or search",
        "binding": {"target_root": str(binding.root), "target_revision": binding.revision, "shared_sha256": binding.shared_sha256, "engine_sha256": binding.engine_sha256},
        "opponent": "target.agents.carrot.shared.carrot_conveyor_agent",
        "suite": {"seeds": list(seeds), "seats": [0, 1], "steps": args.steps, "matches_per_candidate": expected_matches},
        "baseline": {"mean_reward": statistics.mean(baseline_rewards.values()), "cache_dir": str(args.cache_dir)},
        "candidates": completed,
        "all_clean_audits_passed": all(row["all_clean_audits_passed"] for row in completed),
        "wall_elapsed_seconds": perf_counter() - started,
    }
    destination = args.output_dir / "summary.json"
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Completed {len(completed)} candidates; wrote {destination}", flush=True)


if __name__ == "__main__":
    main()
