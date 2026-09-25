"""Bounded Strawberry Tuner orchestration over the shared local evaluator."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from kaggriculture_eval.binding import TargetBinding, bind_target
from kaggriculture_eval.checkpoint import (
    audit_cached,
    baseline_match,
    evaluate_cached,
    read_baseline,
    write_baseline,
)
from kaggriculture_eval.strawberry_adapter import STRAWBERRY_ADAPTER


class StrawberryContractError(ValueError):
    """The bounded Strawberry Tuner contract cannot safely run."""


def read_and_validate_spec(spec_path: Path) -> dict[str, Any]:
    try:
        value = json.loads(spec_path.read_text(encoding="utf-8"))
        # Both crop runners validate draft and approved contracts against the
        # same lifecycle-aware schema. The contract's lifecycle status and
        # execution authorization determine whether execution is permitted.
        schema_path = Path(__file__).resolve().parents[1] / "experiments/schema/experiment-spec-v1.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (OSError, json.JSONDecodeError) as error:
        raise StrawberryContractError(f"cannot read Strawberry Tuner spec: {spec_path}") from error
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda item: item.json_path)
    if errors:
        detail = "; ".join(f"{error.json_path}: {error.message}" for error in errors)
        raise StrawberryContractError(f"specification failed validation: {detail}")
    return value


def bind_and_validate_target(specification: dict[str, Any], target_root: Path) -> TargetBinding:
    try:
        binding = bind_target(target_root, adapter=STRAWBERRY_ADAPTER)
    except (RuntimeError, ValueError) as error:
        raise StrawberryContractError(f"STRAWBERRY target binding failed: {error}") from error
    expected = specification["target"]
    checks = {
        "revision": (expected["expected_revision"], binding.revision),
        "shared_sha256": (expected["expected_shared_sha256"], binding.shared_sha256),
        "parameter_sha256": (
            expected["expected_parameter_sha256"],
            binding.source_hashes[STRAWBERRY_ADAPTER.parameter_relative_path or ""],
        ),
        "engine_sha256": (expected["expected_engine_sha256"], binding.engine_sha256),
        "source_hashes": (expected["source_hashes"], binding.source_hashes),
    }
    mismatches = [
        f"{name}: expected {want}, observed {got}"
        for name, (want, got) in checks.items()
        if want != got
    ]
    if mismatches:
        raise StrawberryContractError("target fingerprint mismatch: " + "; ".join(mismatches))
    return binding


def validate_controls(specification: dict[str, Any], binding: TargetBinding) -> None:
    parameter = specification["parameter"]
    suite = specification["suite"]
    evaluation = specification["evaluation"]
    governance = specification["governance"]
    defaults = asdict(binding.default_parameters)
    failures: list[str] = []
    if parameter["name"] != "future_price_multiplier" or parameter["name"] not in defaults:
        failures.append("parameter is outside the first-pass Strawberry policy scope")
    if parameter["baseline_value"] != defaults.get(parameter["name"]):
        failures.append("declared baseline does not match target default")
    if not parameter["candidate_values"] or parameter["baseline_value"] in parameter["candidate_values"]:
        failures.append("candidate envelope must be non-empty and exclude baseline")
    if suite["opponent_id"] != binding.opponent_id or not hasattr(binding.shared, "strawberry_conveyor_agent"):
        failures.append("opponent is not the bound deterministic STRAWBERRY conveyor")
    if set(suite["seats"]) != {0, 1} or len(suite["seeds"]) != len(set(suite["seeds"])):
        failures.append("suite must contain both seats and unique seeds")
    if evaluation["checkpoint_policy"] != "before_every_decision" or not evaluation["clean_audit_required"]:
        failures.append("checkpoint and clean-audit controls are not enabled")
    if (
        not governance["human_decision_required"]
        or governance["source_policy_mutation_authorized"]
        or governance["candidate_expansion_authorized"]
    ):
        failures.append("governance locks are not fail-closed")
    if failures:
        raise StrawberryContractError("invalid first-pass controls: " + "; ".join(failures))


def _cache_plan(
    specification: dict[str, Any], binding: TargetBinding, cache_root: Path
) -> tuple[str, tuple[tuple[int, int, Path], ...]]:
    suite = specification["suite"]
    identity = {
        "format": "strawberry-baseline-match-v1",
        "experiment_id": specification["experiment_id"],
        "revision": binding.revision,
        "shared_sha256": binding.shared_sha256,
        "engine_sha256": binding.engine_sha256,
        "source_hashes": dict(sorted(binding.source_hashes.items())),
        "opponent": suite["opponent_id"],
        "seeds": suite["seeds"],
        "seats": suite["seats"],
        "steps": suite["steps"],
    }
    group = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    directory = cache_root / "baseline-caches" / group
    entries = tuple(
        (seed, seat, directory / f"seed-{seed}-seat-{seat}.json.gz")
        for seed in suite["seeds"]
        for seat in suite["seats"]
    )
    return group, entries


def _validate_cache(cache: dict[str, Any], binding: TargetBinding, seed: int, seat: int, steps: int) -> None:
    match = cache.get("match", {})
    provenance = cache.get("binding", {})
    if (
        cache.get("schema_version") != 1
        or cache.get("kind") != "baseline-match"
        or match.get("seed") != seed
        or match.get("decision_player") != seat
        or match.get("steps") != steps
        or match.get("opponent") != binding.opponent_id
        or match.get("policy") != binding.policy_id
        or provenance.get("target_root") != str(binding.root)
        or provenance.get("target_revision") != binding.revision
        or provenance.get("shared_sha256") != binding.shared_sha256
        or provenance.get("engine_sha256") != binding.engine_sha256
        or provenance.get("source_hashes") != dict(binding.source_hashes)
        or not cache.get("turns")
    ):
        raise StrawberryContractError(f"present baseline cache is not reusable: seed {seed}, seat {seat}")


def run_first_pass(
    specification: dict[str, Any], *, target_root: Path, cache_root: Path, report_dir: Path
) -> dict[str, Any]:
    if specification.get("lifecycle_status") != "approved":
        raise StrawberryContractError("first-pass execution requires lifecycle_status=approved")
    if "candidate_evidence_run" not in specification["execution_authorization"]["operations"]:
        raise StrawberryContractError("contract does not authorize candidate_evidence_run")
    binding = bind_and_validate_target(specification, target_root)
    validate_controls(specification, binding)
    _, entries = _cache_plan(specification, binding, cache_root)
    suite = specification["suite"]
    caches: dict[tuple[int, int], dict[str, Any]] = {}
    for seed, seat, path in entries:
        if path.is_file():
            cache = read_baseline(path)
            _validate_cache(cache, binding, seed, seat, suite["steps"])
        else:
            cache = baseline_match(binding, seed=seed, seat=seat, steps=suite["steps"])
            path.parent.mkdir(parents=True, exist_ok=True)
            write_baseline(cache, path)
        caches[(seed, seat)] = cache

    parameter = specification["parameter"]
    rows: list[dict[str, Any]] = []
    for candidate_value in parameter["candidate_values"]:
        override = {parameter["name"]: float(candidate_value)}
        for seed, seat, _ in entries:
            fast = evaluate_cached(binding, caches[(seed, seat)], override)
            audited = audit_cached(binding, fast, override)
            if audited.get("audit_status") != "passed":
                raise StrawberryContractError(
                    f"clean audit failed for candidate {candidate_value}, seed {seed}, seat {seat}"
                )
            rows.append(
                {
                    "candidate": {
                        "name": parameter["name"],
                        "old_value": float(parameter["baseline_value"]),
                        "new_value": float(candidate_value),
                    },
                    "match": {"seed": seed, "decision_player": seat, "steps": suite["steps"]},
                    "mode": audited["mode"],
                    "first_divergence_turn": audited["first_divergence_turn"],
                    "suffix_actions": audited["suffix_actions"],
                    "outcome": audited["outcome"],
                    "replay_elapsed_seconds": audited["replay_elapsed_seconds"],
                    "suffix_elapsed_seconds": audited["suffix_elapsed_seconds"],
                    "clean_audit": audited["clean_audit"],
                    "audit_status": audited["audit_status"],
                    "candidate_source_revision": audited["candidate_source_revision"],
                }
            )

    baseline_rewards = [cache["outcome"]["decision_reward"] for cache in caches.values()]
    aggregates = []
    for candidate_value in parameter["candidate_values"]:
        candidate_rows = [row for row in rows if row["candidate"]["new_value"] == float(candidate_value)]
        mean_reward = sum(row["outcome"]["decision_reward"] for row in candidate_rows) / len(candidate_rows)
        mean_delta = sum(
            row["outcome"]["decision_reward"]
            - caches[(row["match"]["seed"], row["match"]["decision_player"])]
            ["outcome"]["decision_reward"]
            for row in candidate_rows
        ) / len(candidate_rows)
        aggregates.append(
            {
                "candidate_value": float(candidate_value),
                "match_count": len(candidate_rows),
                "mean_candidate_decision_reward": mean_reward,
                "mean_paired_decision_delta": mean_delta,
                "divergent_match_count": sum(row["first_divergence_turn"] is not None for row in candidate_rows),
                "total_suffix_actions": sum(row["suffix_actions"] for row in candidate_rows),
                "all_audits_passed": all(row["audit_status"] == "passed" for row in candidate_rows),
            }
        )

    summary = {
        "schema_version": 1,
        "kind": "strawberry-first-pass-summary",
        "experiment_id": specification["experiment_id"],
        "binding": {
            "target_root": str(binding.root),
            "target_revision": binding.revision,
            "shared_sha256": binding.shared_sha256,
            "engine_sha256": binding.engine_sha256,
            "source_hashes": dict(sorted(binding.source_hashes.items())),
            "policy": binding.policy_id,
            "opponent": binding.opponent_id,
        },
        "parameter": {
            "name": parameter["name"],
            "baseline_value": parameter["baseline_value"],
            "candidate_values": parameter["candidate_values"],
        },
        "suite": suite,
        "baseline": {
            "match_count": len(baseline_rewards),
            "mean_decision_reward": sum(baseline_rewards) / len(baseline_rewards),
            "outcomes": [cache["outcome"] for cache in caches.values()],
        },
        "aggregates": aggregates,
        "per_match": rows,
        "audit_status": "passed",
        "controls": {
            "checkpoint_policy": specification["evaluation"]["checkpoint_policy"],
            "clean_audit_required": True,
            "source_policy_mutation_authorized": False,
        },
    }
    destination = report_dir / f"{specification['experiment_id']}.json"
    encoded = (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if destination.exists():
        if destination.read_bytes() != encoded:
            raise FileExistsError(f"refusing to overwrite conflicting report: {destination}")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(encoded)
    summary["report_path"] = str(destination)
    return summary
