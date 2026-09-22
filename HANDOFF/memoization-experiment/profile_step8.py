#!/usr/bin/env python3
"""Profile the local work performed by the notebook's step-eight match suites.

This is a measurement harness, not a game policy.  It runs fully local,
reproducible Kaggriculture matches and separates elapsed wall-clock time into:

* the current carrot decision agent;
* the selected opponent agent; and
* the simulator plus runner/framework overhead (the remaining time).

It also collects a cProfile report for the decision agent and writes a small
timing chart.  Example, from the repository root:

    .venv/bin/python memoization-experiment/profile_step8.py --opponent conveyor --seeds 42

For a tiny timing sample, use one seed.  Add ``--record-traces`` to save the
decision observations/actions, then use ``--replay-traces`` to test whether
the current agent makes exactly the same decisions without rerunning the game.
This script intentionally runs matches sequentially: timing data from
concurrently executing processes would measure CPU contention as well as the
work of the game and agents.
"""

from __future__ import annotations

import argparse
import cProfile
import csv
import gzip
import hashlib
import io
import json
import pstats
import sys
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from time import perf_counter
from typing import Callable

import matplotlib.pyplot as plt
from kaggle_environments import make

# This script intentionally lives outside the source package.  Put the
# repository first so ``agents`` resolves to this project's policies rather
# than an unrelated Kaggle-environments module.
EXPERIMENT_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = EXPERIMENT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.carrot.conveyor import agent as conveyor_agent
from agents.carrot.decision import agent as decision_agent
from agents.archive.test_agent_v0 import agent as test_agent_v0_agent


Agent = Callable[[dict], dict]


@dataclass
class TimedAgent:
    """Wrap one agent and accumulate only time spent inside its callable."""

    name: str
    function: Agent
    profile: bool = False
    record_trace: bool = False
    calls: int = 0
    elapsed_seconds: float = 0.0
    profiler: cProfile.Profile | None = field(default=None, init=False)
    trace_turns: list[dict] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        if self.profile:
            self.profiler = cProfile.Profile()

    def __call__(self, observation: dict, *_: object) -> dict:
        """Accept the runner's optional configuration argument and ignore it.

        The Kaggle adapter normally detects one-argument agents automatically.
        Once we wrap an agent in a callable object, it passes configuration as
        a second positional argument, although these local policies do not use
        it.
        """
        started = perf_counter()
        if self.profiler is not None:
            self.profiler.enable()
        try:
            action = self.function(observation)
            if self.record_trace:
                # Serialize immediately: the game may mutate its state after
                # this turn, while a trace must preserve this exact input.
                self.trace_turns.append(
                    {
                        "observation": json.loads(json.dumps(observation)),
                        "action": json.loads(json.dumps(action)),
                    }
                )
            return action
        finally:
            if self.profiler is not None:
                self.profiler.disable()
            self.calls += 1
            self.elapsed_seconds += perf_counter() - started


def parse_seeds(text: str) -> list[int]:
    """Accept comma-separated integers and inclusive ranges such as 42-46."""
    seeds: list[int] = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = (int(value) for value in part.split("-", maxsplit=1))
            if end < start:
                raise argparse.ArgumentTypeError(f"seed range must ascend: {part}")
            seeds.extend(range(start, end + 1))
        else:
            seeds.append(int(part))
    if not seeds:
        raise argparse.ArgumentTypeError("provide at least one seed")
    return seeds


def selected_opponent(name: str) -> str | Agent:
    """Return a Kaggle built-in name or a local callable for one opponent."""
    opponents: dict[str, str | Agent] = {
        "pass": "pass",
        "random": "random",
        "starter": "starter",
        "conveyor": conveyor_agent,
        "test-agent-v0": test_agent_v0_agent,
    }
    return opponents[name]


def builtin_timed_agent(name: str) -> TimedAgent:
    """Resolve a built-in agent so its execution time can be measured too."""
    # Kaggriculture's built-ins are registered in the local game module.
    from kaggriculture import agents

    return TimedAgent(name, agents[name])


def timed_opponent(name: str) -> TimedAgent:
    """Build the requested opponent wrapper, including built-in agents."""
    opponent = selected_opponent(name)
    if isinstance(opponent, str):
        return builtin_timed_agent(opponent)
    return TimedAgent(name, opponent)


def decision_source_fingerprint() -> str:
    """Hash the policy files that define the current decision behavior."""
    digest = hashlib.sha256()
    for relative_path in ("agents/carrot/decision.py", "agents/carrot/shared.py"):
        digest.update(relative_path.encode())
        digest.update((PROJECT_ROOT / relative_path).read_bytes())
    return digest.hexdigest()


def trace_path(trace_dir: Path, opponent: str, seed: int, decision_player: int) -> Path:
    """Use a stable path so one seed/seat pairing maps to one trace file."""
    return trace_dir / opponent / f"seed-{seed}-decision-player-{decision_player}.json.gz"


def run_one_match(
    seed: int,
    opponent_name: str,
    decision_player: int,
    steps: int,
    profile_decision: bool = False,
    record_trace: bool = False,
) -> dict:
    """Run one match and return reproducible timing and outcome measurements."""
    # cProfile changes the cost of a Python call.  Keep it off for the timing
    # pass, then collect a separate representative function profile below.
    decision = TimedAgent(
        "decision",
        decision_agent,
        profile=profile_decision,
        record_trace=record_trace,
    )
    opponent = timed_opponent(opponent_name)
    players = [decision, opponent] if decision_player == 0 else [opponent, decision]

    environment = make(
        "kaggriculture",
        configuration={"episodeSteps": steps, "seed": seed},
        debug=True,
    )
    started = perf_counter()
    environment.run(players)
    total_seconds = perf_counter() - started

    # The residual includes Kaggriculture's turn processing, observation work,
    # action validation, market updates, and small Python/framework overhead.
    engine_seconds = max(0.0, total_seconds - decision.elapsed_seconds - opponent.elapsed_seconds)
    final_states = environment.steps[-1]
    opponent_player = 1 - decision_player
    return {
        "seed": seed,
        "decision_player": decision_player,
        "opponent": opponent_name,
        "steps": steps,
        "total_seconds": total_seconds,
        "decision_seconds": decision.elapsed_seconds,
        "opponent_seconds": opponent.elapsed_seconds,
        "engine_seconds": engine_seconds,
        "decision_calls": decision.calls,
        "opponent_calls": opponent.calls,
        "decision_reward": final_states[decision_player].reward,
        "opponent_reward": final_states[opponent_player].reward,
        "decision_status": final_states[decision_player].status,
        "opponent_status": final_states[opponent_player].status,
        "profile": decision.profiler,
        "trace": decision.trace_turns,
    }


def write_match_rows(results: list[dict], destination: Path) -> None:
    """Write match-level measurements without the in-memory profiler object."""
    columns = [key for key in results[0] if key not in {"profile", "trace"}]
    with destination.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for result in results:
            writer.writerow({key: result[key] for key in columns})


def write_trace(result: dict, destination: Path) -> None:
    """Persist one deterministic decision trace and its original outcome."""
    payload = {
        "schema_version": 1,
        "baseline_fingerprint": decision_source_fingerprint(),
        "match": {
            key: result[key]
            for key in (
                "seed",
                "decision_player",
                "opponent",
                "steps",
                "total_seconds",
                "decision_reward",
                "opponent_reward",
                "decision_status",
                "opponent_status",
            )
        },
        "turns": result["trace"],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(destination, "wt") as stream:
        json.dump(payload, stream, separators=(",", ":"))


def canonical_action(action: dict) -> str:
    """Compare semantically identical JSON-like Kaggle action dictionaries."""
    return json.dumps(action, sort_keys=True, separators=(",", ":"))


def replay_trace(path: Path) -> dict:
    """Run the current policy on recorded observations until it diverges."""
    with gzip.open(path, "rt") as stream:
        payload = json.load(stream)

    started = perf_counter()
    first_divergence = None
    for turn_number, turn in enumerate(payload["turns"]):
        actual_action = decision_agent(turn["observation"])
        if canonical_action(actual_action) != canonical_action(turn["action"]):
            first_divergence = {
                "turn": turn_number,
                "recorded_action": turn["action"],
                "current_action": actual_action,
            }
            break
    replay_seconds = perf_counter() - started
    original = payload["match"]
    return {
        "trace": str(path),
        "seed": original["seed"],
        "decision_player": original["decision_player"],
        "opponent": original["opponent"],
        "steps": original["steps"],
        "turns_checked": turn_number + 1 if payload["turns"] else 0,
        "trace_reused": first_divergence is None,
        "first_divergence": first_divergence,
        "baseline_total_seconds": original["total_seconds"],
        "replay_seconds": replay_seconds,
        "baseline_fingerprint": payload["baseline_fingerprint"],
        "candidate_fingerprint": decision_source_fingerprint(),
        "baseline_outcome": {
            key: original[key]
            for key in ("decision_reward", "opponent_reward", "decision_status", "opponent_status")
        },
    }


def write_decision_profile(results: list[dict], destination: Path) -> list[dict]:
    """Merge decision cProfile data and retain the expensive local functions."""
    combined = pstats.Stats()
    for result in results:
        profile = result["profile"]
        assert profile is not None
        combined.add(profile)

    # Keep the complete conventional text report for drilling into call paths.
    report = io.StringIO()
    combined.stream = report
    combined.sort_stats("cumulative").print_stats(40)
    destination.write_text(report.getvalue())

    agent_root = PROJECT_ROOT / "agents"
    rows: list[dict] = []
    for (filename, line, function), (primitive_calls, total_calls, own_seconds, cumulative_seconds, _) in combined.stats.items():
        try:
            Path(filename).resolve().relative_to(agent_root)
        except ValueError:
            continue
        rows.append(
            {
                "function": f"{Path(filename).name}:{line}:{function}",
                "calls": total_calls,
                "own_seconds": own_seconds,
                "cumulative_seconds": cumulative_seconds,
            }
        )
    return sorted(rows, key=lambda row: row["cumulative_seconds"], reverse=True)


def write_timing_chart(results: list[dict], destination: Path) -> None:
    """Draw one stacked bar per match: engine, decision, and opponent time."""
    labels = [f"{row['seed']}/P{row['decision_player']}" for row in results]
    engine = [row["engine_seconds"] * 1000 for row in results]
    decision = [row["decision_seconds"] * 1000 for row in results]
    opponent = [row["opponent_seconds"] * 1000 for row in results]

    figure, axis = plt.subplots(figsize=(max(7, len(results) * 1.1), 4.5))
    axis.bar(labels, engine, label="Simulator and framework")
    axis.bar(labels, decision, bottom=engine, label="Decision agent")
    axis.bar(
        labels,
        opponent,
        bottom=[left + middle for left, middle in zip(engine, decision)],
        label="Opponent agent",
    )
    axis.set_title("Wall-clock time per local Kaggriculture match")
    axis.set_xlabel("Seed / decision-player position")
    axis.set_ylabel("Elapsed time (milliseconds)")
    axis.legend()
    figure.tight_layout()
    figure.savefig(destination, dpi=150)
    plt.close(figure)


def write_replay_chart(results: list[dict], destination: Path) -> None:
    """Compare original live-match time with the trace-validation time."""
    labels = [f"{row['seed']}/P{row['decision_player']}" for row in results]
    baseline = [row["baseline_total_seconds"] * 1000 for row in results]
    replay = [row["replay_seconds"] * 1000 for row in results]
    positions = list(range(len(results)))
    width = 0.38

    figure, axis = plt.subplots(figsize=(max(7, len(results) * 1.1), 4.5))
    axis.bar([position - width / 2 for position in positions], baseline, width, label="Original live match")
    axis.bar([position + width / 2 for position in positions], replay, width, label="Memoized trace replay")
    axis.set_title("Live simulation versus decision-trace replay")
    axis.set_xlabel("Seed / decision-player position")
    # The two modes differ by roughly two orders of magnitude. A logarithmic
    # axis keeps the replay bars legible without hiding the live-match costs.
    axis.set_ylabel("Elapsed time (milliseconds, log scale)")
    axis.set_yscale("log")
    axis.set_xticks(positions, labels)
    axis.legend()
    figure.tight_layout()
    figure.savefig(destination, dpi=150)
    plt.close(figure)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--opponent",
        choices=("pass", "random", "starter", "conveyor", "test-agent-v0"),
        default="conveyor",
        help="Opponent used in the timing sample (default: conveyor).",
    )
    parser.add_argument(
        "--seeds",
        type=parse_seeds,
        default=[42],
        help="Comma-separated seeds or inclusive ranges, for example 42 or 42-46.",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=720,
        help="Turns per match; use 720 for a full season (default: 720).",
    )
    parser.add_argument(
        "--one-seat",
        action="store_true",
        help="Run only the decision-agent-as-player-0 order instead of both seats.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=EXPERIMENT_ROOT / "results",
        help="Directory for CSV, JSON, cProfile text, and timing chart.",
    )
    parser.add_argument(
        "--trace-dir",
        type=Path,
        default=EXPERIMENT_ROOT / "trace-cache",
        help="Directory containing compressed decision traces (default: trace-cache).",
    )
    parser.add_argument(
        "--record-traces",
        action="store_true",
        help="Save one decision observation/action trace for every live match.",
    )
    parser.add_argument(
        "--replay-traces",
        action="store_true",
        help="Do not run games; replay existing traces against the current decision agent.",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    if arguments.steps <= 0:
        raise SystemExit("--steps must be positive")
    if arguments.replay_traces and arguments.record_traces:
        raise SystemExit("choose either --record-traces or --replay-traces, not both")

    # The default captures both seats; --one-seat is useful for a quick probe.
    positions = (0,) if arguments.one_seat else (0, 1)
    arguments.output_dir.mkdir(parents=True, exist_ok=True)

    if arguments.replay_traces:
        trace_paths = [
            trace_path(arguments.trace_dir, arguments.opponent, seed, position)
            for seed in arguments.seeds
            for position in positions
        ]
        missing = [path for path in trace_paths if not path.is_file()]
        if missing:
            joined = "\n".join(str(path) for path in missing)
            raise SystemExit(f"missing trace file(s):\n{joined}\nRun once with --record-traces first.")

        replay_results = [replay_trace(path) for path in trace_paths]
        (arguments.output_dir / "replay-summary.json").write_text(
            json.dumps(replay_results, indent=2) + "\n"
        )
        write_replay_chart(replay_results, arguments.output_dir / "replay-timing.png")
        reused = sum(row["trace_reused"] for row in replay_results)
        live_ms = mean(row["baseline_total_seconds"] for row in replay_results) * 1000
        replay_ms = mean(row["replay_seconds"] for row in replay_results) * 1000
        print(f"Replayed {len(replay_results)} trace(s): {reused}/{len(replay_results)} exactly reused")
        print(f"Mean original live match: {live_ms:.1f} ms")
        print(f"Mean trace replay: {replay_ms:.1f} ms")
        if replay_ms > 0:
            print(f"Timing speedup: {live_ms / replay_ms:.1f}x")
        print(f"Wrote replay artifacts to {arguments.output_dir}")
        return

    results = [
        run_one_match(
            seed,
            arguments.opponent,
            position,
            arguments.steps,
            record_trace=arguments.record_traces,
        )
        for seed in arguments.seeds
        for position in positions
    ]

    write_match_rows(results, arguments.output_dir / "matches.csv")
    if arguments.record_traces:
        for result in results:
            write_trace(
                result,
                trace_path(
                    arguments.trace_dir,
                    arguments.opponent,
                    result["seed"],
                    result["decision_player"],
                ),
            )
    # Profile one representative match separately.  It describes *where* the
    # decision time goes, without adding profiler overhead to timing.csv/PNG.
    profile_sample = run_one_match(
        arguments.seeds[0],
        arguments.opponent,
        positions[0],
        arguments.steps,
        profile_decision=True,
    )
    profile_rows = write_decision_profile([profile_sample], arguments.output_dir / "decision-profile.txt")
    write_timing_chart(results, arguments.output_dir / "timing.png")

    summary = {
        "opponent": arguments.opponent,
        "seeds": arguments.seeds,
        "steps": arguments.steps,
        "matches": len(results),
        "function_profile_match": {
            "seed": profile_sample["seed"],
            "decision_player": profile_sample["decision_player"],
            "note": "Separate representative match; excluded from timing averages.",
        },
        "mean_total_ms": mean(row["total_seconds"] for row in results) * 1000,
        "mean_engine_ms": mean(row["engine_seconds"] for row in results) * 1000,
        "mean_decision_ms": mean(row["decision_seconds"] for row in results) * 1000,
        "mean_opponent_ms": mean(row["opponent_seconds"] for row in results) * 1000,
        "top_decision_functions": profile_rows[:10],
        "trace_recording": arguments.record_traces,
    }
    (arguments.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    print(f"Profiled {len(results)} match(es): decision vs {arguments.opponent}")
    print(f"Mean total:    {summary['mean_total_ms']:.1f} ms")
    print(f"Mean simulator/framework residual: {summary['mean_engine_ms']:.1f} ms")
    print(f"Mean decision agent: {summary['mean_decision_ms']:.1f} ms")
    print(f"Mean opponent agent: {summary['mean_opponent_ms']:.1f} ms")
    print(f"Wrote timing artifacts to {arguments.output_dir}")


if __name__ == "__main__":
    main()
