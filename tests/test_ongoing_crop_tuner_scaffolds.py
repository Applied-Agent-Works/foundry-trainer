"""Contract and evaluator checks for the Tomato/Strawberry tuner scaffolds."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator
import pytest


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT.parent / "kaggriculture"
sys.path.insert(0, str(ROOT / "src"))

from kaggriculture_eval.binding import bind_target  # noqa: E402
from kaggriculture_eval.checkpoint import (  # noqa: E402
    audit_cached,
    baseline_match,
    evaluate_cached,
    parameter_candidate,
)
from kaggriculture_eval.strawberry_adapter import STRAWBERRY_ADAPTER  # noqa: E402
from kaggriculture_eval.tomato_adapter import TOMATO_ADAPTER  # noqa: E402


CASES = (
    {
        "name": "tomato",
        "adapter": TOMATO_ADAPTER,
        "project": ROOT / "tomato-tuning-system",
        "spec": ROOT / "tomato-tuning-system/experiments/draft/tomato_crop/future_price_multiplier_smoke_v1.json",
        "approved_spec": ROOT / "tomato-tuning-system/experiments/approved/tomato_crop/future_price_multiplier_smoke_v1.json",
        "shared_path": "agents/tomato/shared.py",
        "crop": "TOMATO",
        "quote": 60,
    },
    {
        "name": "strawberry",
        "adapter": STRAWBERRY_ADAPTER,
        "project": ROOT / "strawberry-tuning-system",
        "spec": ROOT / "strawberry-tuning-system/experiments/draft/strawberry_crop/future_price_multiplier_smoke_v1.json",
        "approved_spec": ROOT / "strawberry-tuning-system/experiments/approved/strawberry_crop/future_price_multiplier_smoke_v1.json",
        "shared_path": "agents/strawberry/shared.py",
        "crop": "STRAWBERRY",
        "quote": 120,
    },
)


def _read_contract(case: dict) -> tuple[dict, dict]:
    specification = json.loads(case["spec"].read_text(encoding="utf-8"))
    schema_path = case["project"] / "experiments/schema/experiment-spec-v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(specification)
    return specification, schema


def _investment_observation(crop: str, quote: int) -> dict:
    return {
        "day": 0,
        "player": 0,
        "farms": [{"money": 3000, "farmer": [0, 0], "tiles": [[None]]}],
        "private": {"seeds": {}, "shed": {}},
        "market": {"prices": {crop: quote}},
    }


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_draft_contract_is_valid_and_fail_closed(case: dict) -> None:
    specification, _ = _read_contract(case)

    assert specification["lifecycle_status"] == "draft"
    assert specification["execution_authorization"]["operations"] == []
    assert specification["parameter"]["name"] == "future_price_multiplier"
    assert specification["parameter"]["baseline_value"] == 1.0
    assert 1.0 not in specification["parameter"]["candidate_values"]
    assert specification["suite"] == {
        "opponent_id": case["adapter"].opponent_id,
        "opponent_deterministic": True,
        "seeds": [42, 43],
        "seats": [0, 1],
        "steps": 720,
    }
    assert specification["evaluation"] == {
        "checkpoint_policy": "before_every_decision",
        "reuse_no_divergence_baseline": True,
        "clean_audit_required": True,
        "result_storage": "local_ignored_var_directory",
    }
    assert specification["governance"] == {
        "human_decision_required": True,
        "source_policy_mutation_authorized": False,
        "candidate_expansion_authorized": False,
    }


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_contract_rejects_execution_authority_and_governance_relaxation(case: dict) -> None:
    specification, schema = _read_contract(case)
    validator = Draft202012Validator(schema)

    executable = deepcopy(specification)
    executable["execution_authorization"]["operations"] = ["candidate_evidence_run"]
    assert list(validator.iter_errors(executable))

    mutable = deepcopy(specification)
    mutable["governance"]["source_policy_mutation_authorized"] = True
    assert list(validator.iter_errors(mutable))


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_approved_contracts_authorize_the_same_bounded_operations(case: dict) -> None:
    specification = json.loads(case["approved_spec"].read_text(encoding="utf-8"))
    schema_path = case["project"] / "experiments/schema/experiment-spec-v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(specification)

    assert specification["lifecycle_status"] == "approved"
    assert specification["execution_authorization"]["operations"] == [
        "baseline_cache_preparation",
        "candidate_evidence_run",
    ]
    assert specification["target"]["source_hashes"] == {
        case["shared_path"]: specification["target"]["source_hashes"][case["shared_path"]],
        "agents/ongoing_crop.py": specification["target"]["expected_parameter_sha256"],
        "kaggriculture.py": specification["target"]["expected_engine_sha256"],
    }


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_explicit_binding_matches_complete_recorded_provenance(case: dict) -> None:
    specification, _ = _read_contract(case)
    binding = bind_target(TARGET, adapter=case["adapter"])

    assert binding.adapter is case["adapter"]
    assert binding.parameter_type.__name__ == "OngoingCropParameters"
    assert binding.default_parameters.future_price_multiplier == 1.0
    assert binding.parameter_module.__file__.endswith("agents/ongoing_crop.py")
    assert set(binding.source_hashes) == {
        case["shared_path"],
        "agents/ongoing_crop.py",
        "kaggriculture.py",
    }
    assert specification["target"] == {
        "binding_mode": "explicit_sibling_target",
        "expected_revision": binding.revision,
        "expected_shared_sha256": binding.shared_sha256,
        "expected_parameter_sha256": binding.source_hashes["agents/ongoing_crop.py"],
        "expected_engine_sha256": binding.engine_sha256,
        "source_hashes": binding.source_hashes,
    }


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_policy_and_deterministic_opponent_are_crop_specific(case: dict) -> None:
    binding = bind_target(TARGET, adapter=case["adapter"])
    observation = _investment_observation(case["crop"], case["quote"])

    first_opponent_action = binding.opponent_agent(deepcopy(observation))
    second_opponent_action = binding.opponent_agent(deepcopy(observation))
    assert first_opponent_action == second_opponent_action
    assert first_opponent_action["market"] == [["BUY_SEED", case["crop"], 1]]
    assert binding.policy_id.endswith(f"{case['name']}_decision_agent")
    assert binding.opponent_id.endswith(f"{case['name']}_conveyor_agent")


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_in_memory_parameter_override_crosses_the_plant_pass_threshold(case: dict) -> None:
    binding = bind_target(TARGET, adapter=case["adapter"])
    observation = _investment_observation(case["crop"], case["quote"])
    parameters, change = parameter_candidate(
        binding, {"future_price_multiplier": 0.05}
    )

    baseline = binding.decision_agent(deepcopy(observation))
    candidate = binding.decision_agent(deepcopy(observation), parameters)
    assert baseline["market"] == [["BUY_SEED", case["crop"], 1]]
    assert candidate == {"farmer": ["PASS"], "hands": [], "market": []}
    assert change == {
        "name": "future_price_multiplier",
        "old_value": 1.0,
        "new_value": 0.05,
    }


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_candidate_parameter_boundary_rejects_unknown_or_multiple_fields(case: dict) -> None:
    binding = bind_target(TARGET, adapter=case["adapter"])
    with pytest.raises(ValueError, match="exactly one"):
        parameter_candidate(
            binding,
            {"future_price_multiplier": 0.05, "pass_utility": 1.0},
        )
    with pytest.raises(ValueError, match="unknown OngoingCropParameters field"):
        parameter_candidate(binding, {"not_a_policy_parameter": 0.0})


@pytest.mark.simulator
@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
@pytest.mark.parametrize("seat", (0, 1), ids=("seat-0", "seat-1"))
def test_restored_suffix_matches_clean_audit_for_both_seats(case: dict, seat: int) -> None:
    binding = bind_target(TARGET, adapter=case["adapter"])
    baseline = baseline_match(binding, seed=42, seat=seat, steps=144)
    override = {"future_price_multiplier": 0.05}
    fast = evaluate_cached(binding, baseline, override)

    assert fast["mode"] == "restored-suffix"
    assert fast["first_divergence_turn"] == 0
    assert fast["candidate_source_revision"] == binding.revision
    assert fast["match"]["opponent"] == binding.opponent_id

    audited = audit_cached(binding, fast, override)
    assert audited["audit_status"] == "passed"
    assert audited["clean_audit"]["outcome"] == audited["outcome"]
