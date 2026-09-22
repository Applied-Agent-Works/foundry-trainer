#!/usr/bin/env python3
"""Run two values of one named carrot policy parameter head to head.

Each match uses the same Kaggriculture engine, seed, and configuration for both
policy variants.  Every seed is run twice with the player positions swapped so
the result is not attributed to a fixed player index.  This is a direct policy
comparison, not a checkpoint/reuse counterfactual: changing both players'
policies changes the shared market trajectory immediately.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from statistics import mean
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kaggle_environments import make

from kaggriculture_eval.binding import bind_target


def policy(binding, parameter: str, value: float):
    """Create an in-memory policy variant; never edit Kaggriculture source."""
    values = asdict(binding.shared.DEFAULT_PARAMETERS)
    if parameter not in values:
        raise ValueError(f"unknown CarrotParameters field: {parameter}")
    values[parameter] = value
    parameters = binding.shared.CarrotParameters(**values)
    return lambda observation: binding.shared.carrot_decision_agent(observation, parameters)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44, 45, 46])
    parser.add_argument("--steps", type=int, default=720)
    parser.add_argument("--parameter", default="seed_opportunity_value", help="One CarrotParameters field to compare.")
    parser.add_argument("--left-value", type=float, default=20.0, help="First parameter value (default: 20).")
    parser.add_argument("--right-value", type=float, default=80.0, help="Second parameter value (default: 80).")
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    binding = bind_target()
    left_value, right_value = args.left_value, args.right_value
    if left_value == right_value:
        parser.error("--left-value and --right-value must differ")
    output_dir = args.output_dir or ROOT / "var" / "results" / f"head-to-head-{left_value:g}-vs-{right_value:g}"
    left_policy, right_policy = policy(binding, args.parameter, left_value), policy(binding, args.parameter, right_value)
    rows = []
    for seed in args.seeds:
        for left_player in (0, 1):
            right_player = 1 - left_player
            environment = make("kaggriculture", configuration={"episodeSteps": args.steps, "seed": seed}, debug=True)
            environment.reset(2)
            started = perf_counter()
            while not environment.done:
                actions = [None, None]
                actions[left_player] = left_policy(environment.state[left_player].observation)
                actions[right_player] = right_policy(environment.state[right_player].observation)
                environment.step(actions)
            elapsed = perf_counter() - started
            reward_left = environment.state[left_player].reward
            reward_right = environment.state[right_player].reward
            rows.append({
                "seed": seed, "left_player": left_player, "right_player": right_player,
                "reward_left": reward_left, "reward_right": reward_right,
                "delta_right_minus_left": reward_right - reward_left,
                "winner": f"{right_value:g}" if reward_right > reward_left else f"{left_value:g}" if reward_left > reward_right else "tie",
                "elapsed_seconds": elapsed,
                "status_left": environment.state[left_player].status,
                "status_right": environment.state[right_player].status,
            })
            print(f"seed {seed}, {left_value:g}=P{left_player}: {left_value:g}={reward_left:.0f}, {right_value:g}={reward_right:.0f}", flush=True)

    deltas = [row["delta_right_minus_left"] for row in rows]
    report = {
        "schema_version": 1,
        "purpose": "direct head-to-head comparison of two human-selected carrot policy parameter values",
        "binding": {"target_root": str(binding.root), "target_revision": binding.revision, "shared_sha256": binding.shared_sha256, "engine_sha256": binding.engine_sha256},
        "controls": {"seeds": args.seeds, "seats_per_seed": [0, 1], "steps": args.steps},
        "parameter": {"name": args.parameter, "left_value": left_value, "right_value": right_value, "note": "One in-memory CarrotParameters override per policy; fixed game facts are unchanged."},
        "summary": {
            "matches": len(rows), "mean_reward_left": mean(row["reward_left"] for row in rows),
            "mean_reward_right": mean(row["reward_right"] for row in rows),
            "mean_delta_right_minus_left": mean(deltas), "right_wins": sum(delta > 0 for delta in deltas),
            "left_wins": sum(delta < 0 for delta in deltas), "ties": sum(delta == 0 for delta in deltas),
            "all_completed": all(row["status_left"] == row["status_right"] == "DONE" for row in rows),
            "conclusion": "Descriptive only; no acceptance threshold was predeclared.",
        },
        "matches_detail": rows,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / "summary.json"
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"], indent=2))
    print(f"Wrote {destination}")


if __name__ == "__main__":
    main()
