"""Fast, simulator-free regression tests for the reviewed local adapter boundaries."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "carrot-tuning-system"))

from evaluator.runner import (  # noqa: E402
    BaselineCacheEntry,
    BaselineCacheReadResult,
    BaselineCacheState,
    LocalSmokeEvidencePacket,
    audit_declared_candidate_result,
    build_local_smoke_evidence_packet,
    evaluate_declared_candidate_from_cache,
    plan_baseline_cache_preparation,
    read_spec,
    select_declared_candidate_override,
    validate_baseline_cache_payload,
    write_local_smoke_evidence_packet,
)


@pytest.fixture
def approved_spec() -> dict:
    path = REPOSITORY_ROOT / (
        "carrot-tuning-system/experiments/approved/carrot_investment/"
        "seed_opportunity_baseline_smoke_v1.json"
    )
    return json.loads(path.read_text())


@pytest.fixture
def matching_binding(approved_spec: dict) -> SimpleNamespace:
    target = approved_spec["target"]
    return SimpleNamespace(
        root=Path("/explicit/kaggriculture"),
        revision=target["expected_revision"],
        shared_sha256=target["expected_shared_sha256"],
        engine_sha256=target["expected_engine_sha256"],
    )


@pytest.fixture
def baseline_outcomes() -> dict[tuple[int, int], dict]:
    return {
        (42, 0): {"decision_reward": 8849.0},
        (42, 1): {"decision_reward": 8809.0},
    }


@pytest.fixture
def audited_results(approved_spec: dict, matching_binding: SimpleNamespace) -> tuple[dict, ...]:
    """Synthetic records match the notebook's already-measured smoke shapes.

    They exercise packet validation without presenting this fixture as a game run.
    """
    rows_by_value = {
        10.0: ((0, 8849.0, 8729.0, None, 0), (1, 8809.0, 8789.0, None, 0)),
        40.0: ((0, 8849.0, 8729.0, None, 0), (1, 8809.0, 8789.0, None, 0)),
        60.0: ((0, 8849.0, 8729.0, None, 0), (1, 8809.0, 8789.0, None, 0)),
        80.0: ((0, 9776.0, 10846.0, 107, 612), (1, 9756.0, 10886.0, 107, 612)),
    }
    records = []
    for value in approved_spec["parameter"]["candidate_values"]:
        for seat, reward, opponent_reward, divergence, suffix in rows_by_value[value]:
            outcome = {
                "decision_reward": reward,
                "opponent_reward": opponent_reward,
            }
            records.append(
                {
                    "candidate": {
                        "name": "seed_opportunity_value",
                        "old_value": 20.0,
                        "new_value": value,
                    },
                    "match": {"seed": 42, "decision_player": seat, "steps": 720},
                    "candidate_source_revision": matching_binding.revision,
                    "mode": "reused-baseline" if divergence is None else "restored-suffix",
                    "first_divergence_turn": divergence,
                    "suffix_actions": suffix,
                    "outcome": outcome,
                    "replay_elapsed_seconds": 0.0,
                    "suffix_elapsed_seconds": 0.0,
                    "audit_status": "passed",
                    "clean_audit": {
                        "outcome": outcome.copy(),
                        "actions_run": 719,
                        "elapsed_seconds": 0.0,
                    },
                }
            )
    return tuple(records)


def build_packet(
    approved_spec: dict,
    matching_binding: SimpleNamespace,
    audited_results: tuple[dict, ...],
    baseline_outcomes: dict[tuple[int, int], dict],
) -> LocalSmokeEvidencePacket:
    return build_local_smoke_evidence_packet(
        approved_spec, matching_binding, audited_results, baseline_outcomes
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [(10, {"seed_opportunity_value": 10.0}), (80.0, {"seed_opportunity_value": 80.0})],
)
def test_declared_candidate_override_accepts_only_declared_numbers(
    approved_spec: dict, value: float, expected: dict[str, float]
) -> None:
    assert select_declared_candidate_override(approved_spec, value) == expected


@pytest.mark.parametrize("value", [25.0, True, "10", None])
def test_declared_candidate_override_rejects_undeclared_or_non_numeric_values(
    approved_spec: dict, value: object
) -> None:
    with pytest.raises(ValueError):
        select_declared_candidate_override(approved_spec, value)  # type: ignore[arg-type]


def test_candidate_evaluation_rejects_undeclared_override_before_cache_access(
    approved_spec: dict, matching_binding: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    entry = BaselineCacheEntry(42, 0, Path("should-not-be-read.json.gz"))

    def unexpected_cache_read(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("cache reader must not run for an undeclared override")

    monkeypatch.setattr("evaluator.runner.read_and_validate_baseline_cache", unexpected_cache_read)
    with pytest.raises(ValueError, match="not declared"):
        evaluate_declared_candidate_from_cache(
            approved_spec,
            matching_binding,
            entry,
            {"seed_opportunity_value": 25.0},
        )


def test_candidate_evaluation_rejects_a_match_outside_the_approved_suite_before_cache_access(
    approved_spec: dict, matching_binding: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    entry = BaselineCacheEntry(42, 2, Path("outside-suite.json.gz"))

    def unexpected_cache_read(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("cache reader must not run for an out-of-suite match")

    monkeypatch.setattr("evaluator.runner.read_and_validate_baseline_cache", unexpected_cache_read)
    with pytest.raises(ValueError, match="outside the approved suite"):
        evaluate_declared_candidate_from_cache(
            approved_spec,
            matching_binding,
            entry,
            {"seed_opportunity_value": 10.0},
        )


def test_candidate_evaluation_rejects_non_reusable_cache_before_checkpoint_import(
    approved_spec: dict, matching_binding: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    entry = BaselineCacheEntry(42, 0, Path("invalid-cache.json.gz"))
    invalid_read = BaselineCacheReadResult(entry, False, None, None)
    monkeypatch.setattr(
        "evaluator.runner.read_and_validate_baseline_cache", lambda *_args: invalid_read
    )

    with pytest.raises(ValueError, match="reusable validated baseline cache"):
        evaluate_declared_candidate_from_cache(
            approved_spec,
            matching_binding,
            entry,
            {"seed_opportunity_value": 10.0},
        )


def test_candidate_audit_rejects_duplicate_or_mismatched_results_before_clean_rerun(
    approved_spec: dict, matching_binding: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unexpected_clean_audit(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("clean audit must not run when its input guard fails")

    monkeypatch.setattr("kaggriculture_eval.checkpoint.audit_cached", unexpected_clean_audit)
    already_audited = {"audit_status": "passed"}
    with pytest.raises(ValueError, match="unaudited fast result"):
        audit_declared_candidate_result(
            approved_spec,
            matching_binding,
            already_audited,
            {"seed_opportunity_value": 10.0},
        )

    mismatched_candidate = {
        "audit_status": "not-run",
        "candidate": {
            "name": "seed_opportunity_value",
            "old_value": 20.0,
            "new_value": 40.0,
        },
    }
    with pytest.raises(ValueError, match="does not correspond"):
        audit_declared_candidate_result(
            approved_spec,
            matching_binding,
            mismatched_candidate,
            {"seed_opportunity_value": 10.0},
        )


def test_evidence_packet_requires_exact_complete_audited_coverage(
    approved_spec: dict,
    matching_binding: SimpleNamespace,
    audited_results: tuple[dict, ...],
    baseline_outcomes: dict[tuple[int, int], dict],
) -> None:
    packet = build_packet(
        approved_spec, matching_binding, audited_results, baseline_outcomes
    )

    assert len(packet.per_match) == 8
    assert packet.all_audits_passed
    assert [aggregate.mean_paired_decision_delta for aggregate in packet.aggregates] == [
        0.0,
        0.0,
        0.0,
        937.0,
    ]

    with pytest.raises(ValueError, match="exactly cover"):
        build_packet(
            approved_spec, matching_binding, audited_results[:-1], baseline_outcomes
        )
    with pytest.raises(ValueError, match="exactly cover"):
        build_packet(
            approved_spec,
            matching_binding,
            audited_results + (audited_results[0],),
            baseline_outcomes,
        )


def test_evidence_packet_rejects_bad_audit_and_wrong_target_revision(
    approved_spec: dict,
    matching_binding: SimpleNamespace,
    audited_results: tuple[dict, ...],
    baseline_outcomes: dict[tuple[int, int], dict],
) -> None:
    failed_audit = dict(audited_results[0], audit_status="failed")
    with pytest.raises(ValueError, match="passing clean audit"):
        build_packet(
            approved_spec,
            matching_binding,
            (failed_audit, *audited_results[1:]),
            baseline_outcomes,
        )

    wrong_revision = dict(audited_results[0], candidate_source_revision="not-the-target")
    with pytest.raises(ValueError, match="target revision differs"):
        build_packet(
            approved_spec,
            matching_binding,
            (wrong_revision, *audited_results[1:]),
            baseline_outcomes,
        )


def test_evidence_packet_writer_round_trips_and_refuses_overwrite(
    tmp_path: Path,
    approved_spec: dict,
    matching_binding: SimpleNamespace,
    audited_results: tuple[dict, ...],
    baseline_outcomes: dict[tuple[int, int], dict],
) -> None:
    packet = build_packet(
        approved_spec, matching_binding, audited_results, baseline_outcomes
    )

    write_result = write_local_smoke_evidence_packet(packet, tmp_path)
    assert write_result.path.is_file()
    assert write_result.byte_count == write_result.path.stat().st_size
    assert json.loads(write_result.path.read_text()) == json.loads(
        json.dumps(packet.as_jsonable())
    )
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        write_local_smoke_evidence_packet(packet, tmp_path)


@pytest.mark.parametrize(
    "change",
    [
        {"all_audits_passed": False},
        {"source_policy_mutation_authorized": True},
    ],
)
def test_evidence_packet_writer_rejects_unsafe_packets_before_writing(
    tmp_path: Path,
    approved_spec: dict,
    matching_binding: SimpleNamespace,
    audited_results: tuple[dict, ...],
    baseline_outcomes: dict[tuple[int, int], dict],
    change: dict[str, bool],
) -> None:
    packet = replace(
        build_packet(approved_spec, matching_binding, audited_results, baseline_outcomes),
        **change,
    )
    with pytest.raises(ValueError):
        write_local_smoke_evidence_packet(packet, tmp_path)
    assert not (tmp_path / "evidence-packets").exists()


def test_evidence_packet_writer_rejects_a_failed_aggregate_before_writing(
    tmp_path: Path,
    approved_spec: dict,
    matching_binding: SimpleNamespace,
    audited_results: tuple[dict, ...],
    baseline_outcomes: dict[tuple[int, int], dict],
) -> None:
    packet = build_packet(approved_spec, matching_binding, audited_results, baseline_outcomes)
    failed_aggregate = replace(packet.aggregates[0], all_audits_passed=False)
    unsafe_packet = replace(packet, aggregates=(failed_aggregate, *packet.aggregates[1:]))

    with pytest.raises(ValueError, match="aggregate with a failed audit"):
        write_local_smoke_evidence_packet(unsafe_packet, tmp_path)
    assert not (tmp_path / "evidence-packets").exists()


def test_cache_payload_validation_accepts_expected_shape_and_rejects_wrong_match(
    approved_spec: dict, matching_binding: SimpleNamespace
) -> None:
    entry = BaselineCacheEntry(42, 0, Path("cache.json.gz"))
    cache = {
        "schema_version": 1,
        "kind": "baseline-match",
        "binding": {
            "target_root": str(matching_binding.root),
            "target_revision": matching_binding.revision,
            "shared_sha256": matching_binding.shared_sha256,
            "engine_sha256": matching_binding.engine_sha256,
        },
        "match": {
            "seed": 42,
            "decision_player": 0,
            "steps": 720,
            "opponent": approved_spec["suite"]["opponent_id"],
            "policy": "target.agents.carrot.shared.carrot_decision_agent",
            "configuration": {"episodeSteps": 720, "seed": 42},
        },
        "turns": [
            {
                "turn": 0,
                "checkpoint_state": [],
                "observation": {},
                "baseline_action": {},
            }
        ],
        "outcome": {
            "decision_reward": 1,
            "opponent_reward": 0,
            "decision_status": "DONE",
            "opponent_status": "DONE",
        },
    }
    valid = validate_baseline_cache_payload(cache, entry, approved_spec, matching_binding)
    assert valid.is_valid

    wrong_seed = dict(cache, match=dict(cache["match"], seed=43))
    invalid = validate_baseline_cache_payload(
        wrong_seed, entry, approved_spec, matching_binding
    )
    assert not invalid.is_valid
    assert any(check.label == "Planned match identity" and not check.passed for check in invalid.checks)


def test_cache_preparation_requires_validation_before_reuse(tmp_path: Path) -> None:
    reusable = BaselineCacheEntry(42, 0, tmp_path / "reusable.json.gz")
    invalid = BaselineCacheEntry(42, 1, tmp_path / "invalid.json.gz")
    missing = BaselineCacheEntry(43, 0, tmp_path / "missing.json.gz")
    reusable.path.touch()
    invalid.path.touch()
    plan = SimpleNamespace(entries=(reusable, invalid, missing))
    state = BaselineCacheState(plan, (reusable, invalid), (missing,))
    payload_check = SimpleNamespace(is_valid=True)
    reusable_read = BaselineCacheReadResult(reusable, True, None, payload_check)
    invalid_read = BaselineCacheReadResult(invalid, True, "bad gzip", None)

    preparation = plan_baseline_cache_preparation(state, (reusable_read, invalid_read))
    assert [action.decision for action in preparation.actions] == [
        "reuse",
        "materialize",
        "materialize",
    ]


def test_read_spec_distinguishes_valid_json_from_malformed_json(tmp_path: Path) -> None:
    valid_path = tmp_path / "valid.json"
    invalid_path = tmp_path / "invalid.json"
    valid_path.write_text('{"ok": true}')
    invalid_path.write_text('{not json}')

    assert read_spec(valid_path) == {"ok": True}
    with pytest.raises(ValueError, match="not valid JSON"):
        read_spec(invalid_path)
