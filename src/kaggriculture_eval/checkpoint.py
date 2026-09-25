"""Baseline caching and exact checkpoint/resume counterfactual evaluation."""

from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

from .binding import TargetBinding


CACHE_SCHEMA_VERSION = 1
Opponent = Callable[[dict], dict]


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value))


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _outcome(environment: Any, seat: int) -> dict[str, Any]:
    other = 1 - seat
    return {
        "decision_reward": environment.state[seat].reward,
        "opponent_reward": environment.state[other].reward,
        "decision_status": environment.state[seat].status,
        "opponent_status": environment.state[other].status,
    }


def _configuration(steps: int, seed: int) -> dict[str, int]:
    return {"episodeSteps": steps, "seed": seed}


def _environment(steps: int, seed: int) -> Any:
    # Cache serialization helpers do not need the simulator package.  Keep this
    # import local so read_baseline/write_baseline remain usable for cache
    # inspection in a lightweight environment.
    from kaggle_environments import make

    environment = make("kaggriculture", configuration=_configuration(steps, seed), debug=True)
    environment.reset(2)
    # The game intentionally scrubs configuration.seed after initialization.
    # This value is the source of deterministic end-of-day random draws.
    if environment.info.get("seed") != seed:
        raise RuntimeError(f"target engine did not retain requested episode seed {seed}")
    return environment


def parameter_candidate(binding: TargetBinding, override: dict[str, float]) -> tuple[Any, dict[str, Any]]:
    """Create exactly one human-specified parameter override, never a source edit."""
    if len(override) != 1:
        raise ValueError("a candidate must override exactly one named policy parameter field")
    name, new_value = next(iter(override.items()))
    defaults = asdict(binding.default_parameters)
    if name not in defaults:
        raise ValueError(f"unknown {binding.parameter_type.__name__} field: {name}")
    old_value = defaults[name]
    values = {**defaults, name: new_value}
    parameters = binding.parameter_type(**values)
    return parameters, {"name": name, "old_value": old_value, "new_value": new_value}


def baseline_match(
    binding: TargetBinding, *, seed: int, seat: int, steps: int,
    opponent: Opponent | None = None, opponent_id: str | None = None,
) -> dict[str, Any]:
    """Run one baseline and snapshot the complete state before every action."""
    environment = _environment(steps, seed)
    turns: list[dict[str, Any]] = []
    started = perf_counter()
    while not environment.done:
        # State is copied through JSON now, breaking mutable aliases held by
        # Kaggle's history and preserving the exact pre-action restore point.
        checkpoint = _json_safe(environment.state)
        observation = _json_safe(environment.state[seat].observation)
        action = binding.decision_agent(observation)
        opponent_observation = _json_safe(environment.state[1 - seat].observation)
        opponent_action = (opponent or binding.opponent_agent)(opponent_observation)
        actions = [None, None]
        actions[seat], actions[1 - seat] = action, opponent_action
        turns.append(
            {
                "turn": len(turns),
                "checkpoint_state": checkpoint,
                "observation": observation,
                "baseline_action": _json_safe(action),
            }
        )
        environment.step(actions)
    return {
        "schema_version": CACHE_SCHEMA_VERSION,
        "kind": "baseline-match",
        "binding": {
            "target_root": str(binding.root),
            "target_revision": binding.revision,
            "shared_sha256": binding.shared_sha256,
            "engine_sha256": binding.engine_sha256,
            "source_hashes": dict(binding.source_hashes),
        },
        "match": {
            "seed": seed,
            "decision_player": seat,
            "steps": steps,
            "opponent": opponent_id or binding.opponent_id,
            "policy": binding.policy_id,
            "configuration": _configuration(steps, seed),
        },
        "turns": turns,
        "outcome": _outcome(environment, seat),
        "baseline_elapsed_seconds": perf_counter() - started,
    }


def write_baseline(cache: dict[str, Any], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(destination, "wt", encoding="utf-8") as stream:
        json.dump(cache, stream, separators=(",", ":"))


def read_baseline(source: Path) -> dict[str, Any]:
    with gzip.open(source, "rt", encoding="utf-8") as stream:
        cache = json.load(stream)
    if not isinstance(cache, dict) or cache.get("schema_version") != CACHE_SCHEMA_VERSION:
        raise ValueError("unsupported baseline cache schema")
    return cache


def _restore_environment(cache: dict[str, Any], checkpoint_state: list[dict[str, Any]]) -> Any:
    from kaggle_environments.utils import structify

    match = cache["match"]
    environment = _environment(match["steps"], match["seed"])
    environment.state = structify(checkpoint_state)
    # Kaggle's core assigns the next observation's ``step`` from
    # ``len(environment.steps)``.  Retain only placeholders for the already
    # completed prefix so the restored suffix continues at the checkpoint's
    # absolute turn rather than silently restarting its step counter at one.
    completed_turns = int(environment.state[0].observation.step)
    environment.steps = [None] * (completed_turns + 1)
    environment.logs = []
    environment.info["seed"] = match["seed"]
    return environment


def _run_suffix(
    binding: TargetBinding, cache: dict[str, Any], parameters: Any, start_turn: int,
    opponent: Opponent | None = None,
) -> dict[str, Any]:
    match = cache["match"]
    environment = _restore_environment(cache, cache["turns"][start_turn]["checkpoint_state"])
    started = perf_counter()
    suffix_actions = 0
    while not environment.done:
        observation = _json_safe(environment.state[match["decision_player"]].observation)
        action = binding.decision_agent(observation, parameters)
        opponent_observation = _json_safe(environment.state[1 - match["decision_player"]].observation)
        opponent_action = (opponent or binding.opponent_agent)(opponent_observation)
        actions = [None, None]
        actions[match["decision_player"]], actions[1 - match["decision_player"]] = action, opponent_action
        environment.step(actions)
        suffix_actions += 1
    return {
        "outcome": _outcome(environment, match["decision_player"]),
        "suffix_actions": suffix_actions,
        "suffix_elapsed_seconds": perf_counter() - started,
    }


def evaluate_cached(
    binding: TargetBinding, cache: dict[str, Any], override: dict[str, float], opponent: Opponent | None = None,
) -> dict[str, Any]:
    """Replay to first mismatch, then reuse or restore and simulate forward."""
    parameters, change = parameter_candidate(binding, override)
    started = perf_counter()
    divergence_turn = None
    for turn in cache["turns"]:
        candidate = binding.decision_agent(turn["observation"], parameters)
        if _canonical(candidate) != _canonical(turn["baseline_action"]):
            divergence_turn = turn["turn"]
            break
    replay_elapsed = perf_counter() - started
    if divergence_turn is None:
        outcome = _json_safe(cache["outcome"])
        suffix_actions = 0
        mode = "reused-baseline"
        suffix_elapsed = 0.0
    else:
        suffix = _run_suffix(binding, cache, parameters, divergence_turn, opponent)
        outcome = suffix["outcome"]
        suffix_actions = suffix["suffix_actions"]
        suffix_elapsed = suffix["suffix_elapsed_seconds"]
        mode = "restored-suffix"
    return {
        "match": cache["match"],
        "baseline_source_revision": cache["binding"]["target_revision"],
        "candidate_source_revision": binding.revision,
        "candidate": change,
        "candidate_fingerprint": hashlib.sha256(_canonical(change).encode()).hexdigest(),
        "mode": mode,
        "first_divergence_turn": divergence_turn,
        "suffix_actions": suffix_actions,
        "outcome": outcome,
        "replay_elapsed_seconds": replay_elapsed,
        "suffix_elapsed_seconds": suffix_elapsed,
        "audit_status": "not-run",
    }


def _normalise_interventions(
    binding: TargetBinding,
    cache: dict[str, Any],
    interventions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Validate an ordered, one-parameter intervention schedule."""
    if not interventions:
        raise ValueError("an intervention schedule must contain at least one change point")

    turns = [int(item["turn"]) for item in interventions]
    if turns != sorted(turns) or len(turns) != len(set(turns)):
        raise ValueError("intervention turns must be sorted and unique")
    if turns[0] < 0 or turns[-1] >= len(cache["turns"]):
        raise ValueError("intervention turns must identify baseline checkpoints")

    normalized: list[dict[str, Any]] = []
    parameter_name: str | None = None
    for item in interventions:
        override = item.get("override")
        if not isinstance(override, dict) or len(override) != 1:
            raise ValueError("each intervention must override exactly one parameter")
        parameters, change = parameter_candidate(binding, {str(k): float(v) for k, v in override.items()})
        del parameters
        if parameter_name is None:
            parameter_name = change["name"]
        elif change["name"] != parameter_name:
            raise ValueError("all intervention points must change the same parameter")
        normalized.append({"turn": int(item["turn"]), "override": {change["name"]: change["new_value"]}})
    return normalized


def _scheduled_parameters(
    binding: TargetBinding,
    interventions: list[dict[str, Any]],
    absolute_turn: int,
) -> tuple[Any, int | None]:
    """Return the active parameters and schedule index for one turn."""
    active_index: int | None = None
    for index, intervention in enumerate(interventions):
        if intervention["turn"] > absolute_turn:
            break
        active_index = index
    if active_index is None:
        return binding.default_parameters, None
    parameters, _ = parameter_candidate(binding, interventions[active_index]["override"])
    return parameters, active_index


def evaluate_scheduled_cached(
    binding: TargetBinding,
    cache: dict[str, Any],
    interventions: list[dict[str, Any]],
    opponent: Opponent | None = None,
) -> dict[str, Any]:
    """Restore the earliest change point and run a time-varying candidate suffix."""
    schedule = _normalise_interventions(binding, cache, interventions)
    start_turn = schedule[0]["turn"]
    environment = _restore_environment(cache, cache["turns"][start_turn]["checkpoint_state"])
    started = perf_counter()
    first_divergence_turn = None
    changed_actions = 0
    suffix_actions = 0
    applied_points: list[int] = []
    absolute_turn = start_turn
    while not environment.done:
        parameters, schedule_index = _scheduled_parameters(binding, schedule, absolute_turn)
        if schedule_index is not None and schedule[schedule_index]["turn"] == absolute_turn:
            applied_points.append(absolute_turn)
        observation = _json_safe(environment.state[cache["match"]["decision_player"]].observation)
        action = binding.decision_agent(observation, parameters)
        baseline_action = cache["turns"][absolute_turn]["baseline_action"]
        if _canonical(action) != _canonical(baseline_action):
            changed_actions += 1
            if first_divergence_turn is None:
                first_divergence_turn = absolute_turn
        opponent_observation = _json_safe(environment.state[1 - cache["match"]["decision_player"]].observation)
        opponent_action = (opponent or binding.opponent_agent)(opponent_observation)
        actions = [None, None]
        actions[cache["match"]["decision_player"]], actions[1 - cache["match"]["decision_player"]] = action, opponent_action
        environment.step(actions)
        suffix_actions += 1
        absolute_turn += 1
    return {
        "match": cache["match"],
        "baseline_source_revision": cache["binding"]["target_revision"],
        "candidate_source_revision": binding.revision,
        "candidate": {
            "name": next(iter(schedule[0]["override"])),
            "old_value": asdict(binding.default_parameters)[next(iter(schedule[0]["override"]))],
            "new_value": schedule[-1]["override"][next(iter(schedule[-1]["override"]))],
        },
        "interventions": schedule,
        "candidate_fingerprint": hashlib.sha256(_canonical(schedule).encode()).hexdigest(),
        "mode": "scheduled-suffix",
        "first_divergence_turn": first_divergence_turn,
        "changed_actions": changed_actions,
        "applied_intervention_turns": applied_points,
        "suffix_actions": suffix_actions,
        "outcome": _outcome(environment, cache["match"]["decision_player"]),
        "replay_elapsed_seconds": 0.0,
        "suffix_elapsed_seconds": perf_counter() - started,
        "audit_status": "not-run",
    }


def clean_scheduled_rerun(
    binding: TargetBinding,
    *,
    seed: int,
    seat: int,
    steps: int,
    interventions: list[dict[str, Any]],
    opponent: Opponent | None = None,
) -> dict[str, Any]:
    """Run a scheduled intervention from a clean simulator start."""
    schedule = _normalise_interventions(binding, {"turns": [{"turn": 0}] * steps}, interventions)
    environment = _environment(steps, seed)
    started = perf_counter()
    actions_run = 0
    absolute_turn = 0
    while not environment.done:
        parameters, _ = _scheduled_parameters(binding, schedule, absolute_turn)
        action = binding.decision_agent(_json_safe(environment.state[seat].observation), parameters)
        opponent_action = (opponent or binding.opponent_agent)(_json_safe(environment.state[1 - seat].observation))
        actions = [None, None]
        actions[seat], actions[1 - seat] = action, opponent_action
        environment.step(actions)
        actions_run += 1
        absolute_turn += 1
    return {
        "outcome": _outcome(environment, seat),
        "actions_run": actions_run,
        "elapsed_seconds": perf_counter() - started,
    }


def audit_scheduled_cached(
    binding: TargetBinding,
    fast: dict[str, Any],
    interventions: list[dict[str, Any]],
    opponent: Opponent | None = None,
) -> dict[str, Any]:
    """Confirm a scheduled suffix with a matching clean scheduled rerun."""
    match = fast["match"]
    audit = clean_scheduled_rerun(
        binding,
        seed=match["seed"],
        seat=match["decision_player"],
        steps=match["steps"],
        interventions=interventions,
        opponent=opponent,
    )
    fast["clean_audit"] = audit
    fast["audit_status"] = "passed" if audit["outcome"] == fast["outcome"] else "failed"
    return fast


def clean_rerun(
    binding: TargetBinding, *, seed: int, seat: int, steps: int, override: dict[str, float], opponent: Opponent | None = None,
) -> dict[str, Any]:
    """A full candidate run used only as an audit oracle for cached results."""
    parameters, _ = parameter_candidate(binding, override)
    environment = _environment(steps, seed)
    started = perf_counter()
    actions_run = 0
    while not environment.done:
        action = binding.decision_agent(_json_safe(environment.state[seat].observation), parameters)
        opponent_action = (opponent or binding.opponent_agent)(_json_safe(environment.state[1 - seat].observation))
        actions = [None, None]
        actions[seat], actions[1 - seat] = action, opponent_action
        environment.step(actions)
        actions_run += 1
    return {"outcome": _outcome(environment, seat), "actions_run": actions_run, "elapsed_seconds": perf_counter() - started}


def audit_cached(
    binding: TargetBinding, fast: dict[str, Any], override: dict[str, float], opponent: Opponent | None = None,
) -> dict[str, Any]:
    match = fast["match"]
    audit = clean_rerun(binding, seed=match["seed"], seat=match["decision_player"], steps=match["steps"], override=override, opponent=opponent)
    fast["clean_audit"] = audit
    fast["audit_status"] = "passed" if audit["outcome"] == fast["outcome"] else "failed"
    return fast
