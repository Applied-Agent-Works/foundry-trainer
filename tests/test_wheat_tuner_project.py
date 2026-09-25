from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "wheat-tuning-system"))

from kaggriculture_eval.wheat_adapter import WHEAT_ADAPTER  # noqa: E402
from kaggriculture_eval.binding import bind_target  # noqa: E402
from kaggriculture_eval.checkpoint import audit_cached, baseline_match, evaluate_cached  # noqa: E402
from wheat_tuner.runner import _cache_plan, _validate_cache, read_and_validate_spec, validate_controls  # noqa: E402


SPEC = ROOT / "wheat-tuning-system/experiments/approved/wheat_crop/future_price_multiplier_smoke_v1.json"


def test_wheat_contract_and_explicit_binding_are_valid() -> None:
    specification = read_and_validate_spec(SPEC)
    binding = bind_target(ROOT.parent / "kaggriculture", adapter=WHEAT_ADAPTER)

    validate_controls(specification, binding)

    assert specification["parameter"]["name"] == "future_price_multiplier"
    assert binding.adapter is WHEAT_ADAPTER
    assert binding.policy_id.endswith("wheat_decision_agent")
    assert binding.opponent_id.endswith("wheat_conveyor_agent")
    assert binding.parameter_type.__name__ == "PointPriceParameters"
    assert binding.default_parameters.future_price_multiplier == 1.0
    assert Path(binding.parameter_module.__file__).resolve() == (
        ROOT.parent / "kaggriculture" / "agents" / "one_time_crop.py"
    ).resolve()
    assert set(binding.source_hashes) == {
        "agents/wheat/shared.py",
        "agents/one_time_crop.py",
        "kaggriculture.py",
    }
    assert binding.source_hashes["agents/one_time_crop.py"] == specification["target"]["expected_parameter_sha256"]


def test_documented_first_pass_command_uses_unique_receipt_paths() -> None:
    readme = (ROOT / "wheat-tuning-system" / "README.md").read_text(encoding="utf-8")
    assert "RUN_ID=20260924-next" in readme
    assert "var/wheat-tuning-system/runs/$RUN_ID/cache" in readme
    assert "var/wheat-tuning-system/runs/$RUN_ID/report" in readme
    assert "canonical-20260924/report/wheat-future-price-multiplier-smoke-v1.json" in readme


def test_wheat_contract_rejects_baseline_candidate() -> None:
    specification = read_and_validate_spec(SPEC)
    binding = bind_target(ROOT.parent / "kaggriculture", adapter=WHEAT_ADAPTER)
    specification["parameter"]["candidate_values"] = [1.0]

    with pytest.raises(ValueError, match="exclude baseline"):
        validate_controls(specification, binding)


def test_auxiliary_source_hash_changes_cache_identity_and_invalidates_cache() -> None:
    specification = read_and_validate_spec(SPEC)
    binding = bind_target(ROOT.parent / "kaggriculture", adapter=WHEAT_ADAPTER)
    original_group, _ = _cache_plan(specification, binding, ROOT / "var" / "test-wheat-cache")

    changed_hashes = dict(binding.source_hashes)
    changed_hashes["agents/one_time_crop.py"] = "0" * 64
    changed_binding = replace(binding, source_hashes=changed_hashes)
    changed_group, _ = _cache_plan(specification, changed_binding, ROOT / "var" / "test-wheat-cache")
    assert changed_group != original_group

    cache = {
        "schema_version": 1,
        "kind": "baseline-match",
        "binding": {
            "target_root": str(binding.root),
            "target_revision": binding.revision,
            "shared_sha256": binding.shared_sha256,
            "engine_sha256": binding.engine_sha256,
            "source_hashes": dict(binding.source_hashes),
        },
        "match": {
            "seed": 42,
            "decision_player": 0,
            "steps": 720,
            "opponent": binding.opponent_id,
            "policy": binding.policy_id,
        },
        "turns": [{"turn": 0}],
    }
    _validate_cache(cache, binding, 42, 0, 720)
    invalid = deepcopy(cache)
    invalid["binding"]["source_hashes"]["agents/one_time_crop.py"] = "0" * 64
    with pytest.raises(ValueError, match="present baseline cache is not reusable"):
        _validate_cache(invalid, binding, 42, 0, 720)


@pytest.mark.simulator
def test_wheat_restored_suffix_clean_audit_uses_bound_wheat_policy() -> None:
    """Regression for the Watermelon-discovered carrot clean-audit bug."""
    binding = bind_target(ROOT.parent / "kaggriculture", adapter=WHEAT_ADAPTER)
    baseline = baseline_match(binding, seed=42, seat=0, steps=144)

    audited = audit_cached(
        binding,
        evaluate_cached(binding, baseline, {"future_price_multiplier": 0.05}),
        {"future_price_multiplier": 0.05},
    )

    assert audited["mode"] == "restored-suffix"
    assert audited["first_divergence_turn"] == 0
    assert audited["audit_status"] == "passed"
