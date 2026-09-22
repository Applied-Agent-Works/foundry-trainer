#!/usr/bin/env python3
"""Report the carrot policy's observed investment-decision margins.

This reads immutable checkpoint observations from the fixed 60-match baseline
suite.  It does not execute the simulator, alter the target, or select a
candidate.  The target has one tunable economic gate: invest/plant when a
seed-owning farmer is at (or moving toward) an empty tile versus pass.  The
report separates all observations from turns where that gate is eligible.
"""

from __future__ import annotations

import argparse
import gzip
import json
import statistics
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kaggriculture_eval.binding import bind_target
from kaggriculture_eval.checkpoint import read_baseline


def _eligible(shared: Any, observation: dict[str, Any]) -> bool:
    """Mirror only the conditions under which the policy's economics matter."""
    farm = shared._my_farm(observation)
    position = tuple(farm["farmer"])
    tile = shared._tile_at(farm, position)
    return (
        shared._can_still_reach_first_carrot_yield(observation)
        and observation["private"]["seeds"].get(shared.CARROT, 0) > 0
        and (tile is None or shared._nearest_tile(farm, position, lambda value: value is None) is not None)
    )


def _row(shared: Any, observation: dict[str, Any], turn: int, match: dict[str, Any]) -> dict[str, Any]:
    explanation = shared.explain_carrot_decision(observation)
    margin = explanation["plant_utility"] - explanation["pass_utility"]
    return {
        "seed": match["seed"],
        "seat": match["decision_player"],
        "turn": turn,
        "day": observation["day"],
        "eligible_investment_gate": _eligible(shared, observation),
        "plant_utility": explanation["plant_utility"],
        "pass_utility": explanation["pass_utility"],
        "plant_minus_pass_margin": margin,
        "recommendation": explanation["recommendation"],
        "visible_opponent_ripe_carrots": explanation["visible_opponent_ripe_carrots"],
        "high_supply_probability": explanation["high_opponent_supply_probability"],
        "expected_sale_price": explanation["expected_sale_price"],
        "price_distribution": explanation["price_distribution"],
    }


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [row for row in rows if row["eligible_investment_gate"]]
    margins = [row["plant_minus_pass_margin"] for row in eligible]
    return {
        "observations": len(rows),
        "eligible_investment_gate_observations": len(eligible),
        "eligible_recommend_plant": sum(row["recommendation"] == "PLANT CARROT" for row in eligible),
        "eligible_recommend_pass": sum(row["recommendation"] == "PASS" for row in eligible),
        "margin": {
            "minimum": min(margins) if margins else None,
            "median": statistics.median(margins) if margins else None,
            "maximum": max(margins) if margins else None,
            "nearest_to_boundary": min(eligible, key=lambda row: abs(row["plant_minus_pass_margin"])) if eligible else None,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "var" / "cache" / "perturbation-sensitivity-60")
    parser.add_argument("--output", type=Path, default=ROOT / "var" / "results" / "decision-margin-60" / "summary.json")
    args = parser.parse_args()
    binding = bind_target()
    rows = []
    for path in sorted(args.cache_dir.glob("seed-*-seat-*.json.gz")):
        baseline = read_baseline(path)
        for turn in baseline["turns"]:
            rows.append(_row(binding.shared, turn["observation"], turn["turn"], baseline["match"]))
    if not rows:
        raise SystemExit(f"no baseline caches found in {args.cache_dir}")
    report = {
        "schema_version": 1,
        "purpose": "read-only observed decision-margin analysis; no target modification or candidate selection",
        "binding": {"target_root": str(binding.root), "target_revision": binding.revision, "shared_sha256": binding.shared_sha256, "engine_sha256": binding.engine_sha256},
        "baseline_cache_dir": str(args.cache_dir),
        "parameters": asdict(binding.shared.DEFAULT_PARAMETERS),
        "summary": _summary(rows),
        "eligible_gate_rows": [row for row in rows if row["eligible_investment_gate"]],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"], indent=2))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
