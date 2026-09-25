#!/usr/bin/env python3
"""Repeat the original 140-match local baseline timing and trace sweep.

This is deliberately a *baseline* producer, not a candidate evaluator.  It
recreates the suite used to understand normal match cost: 20 ``pass`` matches
and 60 each for ``random`` and ``starter``.  Every match is a 720-turn season,
and the policy is seated in both player positions.  It stores only the policy
observation/action trace needed for rapid action-replay timing; it does not
claim that a trace alone is a restorable simulator checkpoint.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import importlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from time import perf_counter
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kaggle_environments import make

from kaggriculture_eval.carrot_adapter import CARROT_ADAPTER
from kaggriculture_eval.binding import bind_target


Agent = Callable[[dict], dict]
# These are intentionally the same fixed suites as the prior Kaggriculture
# timing study.  Do not silently alter them while comparing timing reports.
STEPS = 720
SUITES = {"pass": range(42, 52), "random": range(42, 72), "starter": range(42, 72)}


def json_copy(value: Any) -> Any:
    return json.loads(json.dumps(value))


@dataclass
class TimedAgent:
    name: str
    function: Agent
    calls: int = 0
    elapsed_seconds: float = 0.0
    trace: list[dict[str, Any]] = field(default_factory=list)

    def __call__(self, observation: dict, *_: object) -> dict:
        started = perf_counter()
        action = self.function(observation)
        self.calls += 1
        self.elapsed_seconds += perf_counter() - started
        if self.name == "decision":
            self.trace.append({"observation": json_copy(observation), "action": json_copy(action)})
        return action


def target_builtin_agents(binding_root: Path) -> dict[str, Agent]:
    """Resolve only built-ins registered by the explicitly bound target game."""
    module = importlib.import_module("kaggriculture")
    if Path(module.__file__).resolve().parent != binding_root:
        raise RuntimeError(f"builtin opponents resolved outside the bound target: {module.__file__}")
    return module.agents


def run_match(binding: Any, builtin_agents: dict[str, Agent], opponent_name: str, seed: int, seat: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    decision = TimedAgent("decision", binding.shared.carrot_decision_agent)
    opponent = TimedAgent(opponent_name, builtin_agents[opponent_name])
    players = [decision, opponent] if seat == 0 else [opponent, decision]
    environment = make("kaggriculture", configuration={"episodeSteps": STEPS, "seed": seed}, debug=True)
    started = perf_counter()
    environment.run(players)
    total = perf_counter() - started
    final = environment.state
    other = 1 - seat
    return ({
        "seed": seed, "decision_player": seat, "opponent": opponent_name, "steps": STEPS,
        "total_seconds": total, "decision_seconds": decision.elapsed_seconds,
        "opponent_seconds": opponent.elapsed_seconds,
        "engine_seconds": max(0.0, total - decision.elapsed_seconds - opponent.elapsed_seconds),
        "decision_calls": decision.calls, "opponent_calls": opponent.calls,
        "decision_reward": final[seat].reward, "opponent_reward": final[other].reward,
        "decision_status": final[seat].status, "opponent_status": final[other].status,
    }, decision.trace)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "var" / "results" / "baseline-timing-140")
    parser.add_argument("--trace-dir", type=Path, default=ROOT / "var" / "trace-cache" / "baseline-timing-140")
    args = parser.parse_args()
    binding = bind_target(adapter=CARROT_ADAPTER)
    builtins = target_builtin_agents(binding.root)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {"schema_version": 1, "binding": {"target_root": str(binding.root), "target_revision": binding.revision, "shared_sha256": binding.shared_sha256, "engine_sha256": binding.engine_sha256}, "steps": STEPS, "suites": {}}

    for opponent, seeds in SUITES.items():
        rows = []
        for seed in seeds:
            for seat in (0, 1):
                # A fresh environment prevents state from leaking between
                # matches; traces are indexed by seed, opponent, and seat.
                row, trace = run_match(binding, builtins, opponent, seed, seat)
                rows.append(row)
                path = args.trace_dir / opponent / f"seed-{seed}-decision-player-{seat}.json.gz"
                path.parent.mkdir(parents=True, exist_ok=True)
                with gzip.open(path, "wt", encoding="utf-8") as stream:
                    json.dump({"schema_version": 1, "binding": report["binding"], "match": row, "turns": trace}, stream, separators=(",", ":"))
        suite_dir = args.output_dir / opponent
        suite_dir.mkdir(parents=True, exist_ok=True)
        with (suite_dir / "matches.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
            writer.writeheader(); writer.writerows(rows)
        summary = {"opponent": opponent, "seeds": list(seeds), "matches": len(rows), "mean_total_ms": mean(r["total_seconds"] for r in rows) * 1000, "mean_engine_ms": mean(r["engine_seconds"] for r in rows) * 1000, "mean_decision_ms": mean(r["decision_seconds"] for r in rows) * 1000, "mean_opponent_ms": mean(r["opponent_seconds"] for r in rows) * 1000}
        (suite_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        report["suites"][opponent] = summary
        print(f"{opponent}: {len(rows)} matches, mean {summary['mean_total_ms']:.1f} ms", flush=True)
    (args.output_dir / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Wrote {args.output_dir}")


if __name__ == "__main__":
    main()
