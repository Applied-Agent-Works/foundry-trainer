"""Regression checks for the explicit Watermelon adapter boundary."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "watermelon-tuning-system"))

from watermelon_tuner import runner as watermelon_runner  # noqa: E402
from watermelon_tuner.runner import WatermelonContractError, read_and_validate_spec  # noqa: E402
from kaggriculture_eval.binding import bind_target  # noqa: E402
from kaggriculture_eval.checkpoint import audit_cached, baseline_match, evaluate_cached  # noqa: E402
from kaggriculture_eval.melon_adapter import MELON_ADAPTER  # noqa: E402


SPEC = ROOT / "watermelon-tuning-system/experiments/approved/melon_investment/future_price_multiplier_smoke_v1.json"


def test_first_pass_spec_is_schema_valid() -> None:
    spec = read_and_validate_spec(SPEC)
    assert spec["parameter"]["name"] == "future_price_multiplier"
    assert spec["suite"]["opponent_id"].endswith("melon_conveyor_agent")
    assert set(spec["target"]["source_hashes"]) == {
        "agents/melon/shared.py",
        "agents/one_time_crop.py",
        "kaggriculture.py",
    }


def test_receipt_contract_requires_a_top_level_clean_audit_status() -> None:
    """A generated receipt must expose its all-match audit result directly."""
    source = (ROOT / "watermelon-tuning-system/watermelon_tuner/runner.py").read_text(
        encoding="utf-8"
    )
    assert '"audit_status": "passed"' in source


def test_documented_first_pass_command_uses_unique_receipt_paths() -> None:
    readme = (ROOT / "watermelon-tuning-system" / "README.md").read_text(encoding="utf-8")
    assert "RUN_ID=20260924-next" in readme
    assert "var/watermelon-tuning-system/runs/$RUN_ID/cache" in readme
    assert "var/watermelon-tuning-system/runs/$RUN_ID/report" in readme
    assert "runs/20260926-repin-003649/report/melon-future-price-multiplier-smoke-v1.json" in readme


def test_watermelon_path_uses_only_the_explicit_melon_adapter() -> None:
    assert watermelon_runner.MELON_ADAPTER is MELON_ADAPTER
    assert "CARROT_ADAPTER" not in watermelon_runner.__dict__


@pytest.fixture
def melon_binding():
    return bind_target(ROOT.parent / "kaggriculture", adapter=MELON_ADAPTER)


def test_melon_binding_uses_explicit_helper_and_complete_hash_set(melon_binding) -> None:
    assert melon_binding.policy_id.endswith("melon_decision_agent")
    assert melon_binding.opponent_id.endswith("melon_conveyor_agent")
    assert melon_binding.parameter_type.__name__ == "PointPriceParameters"
    assert melon_binding.default_parameters.future_price_multiplier == 1.0
    assert hasattr(melon_binding.shared, melon_binding.adapter.policy_attribute)
    assert melon_binding.parameter_module.__file__.endswith("agents/one_time_crop.py")
    assert set(melon_binding.source_hashes) == {
        "agents/melon/shared.py",
        "agents/one_time_crop.py",
        "kaggriculture.py",
    }


def test_auxiliary_source_hash_changes_cache_identity(tmp_path: Path, melon_binding) -> None:
    specification = read_and_validate_spec(SPEC)
    first_group, _ = watermelon_runner._cache_plan(specification, melon_binding, tmp_path)
    changed = replace(
        melon_binding,
        source_hashes={
            **melon_binding.source_hashes,
            "agents/one_time_crop.py": "0" * 64,
        },
    )
    second_group, _ = watermelon_runner._cache_plan(specification, changed, tmp_path)
    assert first_group != second_group


def test_cache_with_mismatched_auxiliary_hash_is_rejected(melon_binding) -> None:
    specification = read_and_validate_spec(SPEC)
    suite = specification["suite"]
    cache = {
        "schema_version": 1,
        "kind": "baseline-match",
        "binding": {
            "target_root": str(melon_binding.root),
            "target_revision": melon_binding.revision,
            "shared_sha256": melon_binding.shared_sha256,
            "engine_sha256": melon_binding.engine_sha256,
            "source_hashes": {
                **melon_binding.source_hashes,
                "agents/one_time_crop.py": "0" * 64,
            },
        },
        "match": {
            "seed": suite["seeds"][0],
            "decision_player": suite["seats"][0],
            "steps": suite["steps"],
            "opponent": melon_binding.opponent_id,
            "policy": melon_binding.policy_id,
        },
        "turns": [{"turn": 0}],
    }
    with pytest.raises(WatermelonContractError, match="not reusable"):
        watermelon_runner._validate_cache(
            cache,
            melon_binding,
            suite["seeds"][0],
            suite["seats"][0],
            suite["steps"],
        )


@pytest.mark.simulator
def test_early_divergence_restored_suffix_matches_clean_audit(melon_binding) -> None:
    baseline = baseline_match(melon_binding, seed=42, seat=0, steps=144)
    fast = evaluate_cached(
        melon_binding, baseline, {"future_price_multiplier": 0.05}
    )
    assert fast["mode"] == "restored-suffix"
    assert fast["first_divergence_turn"] == 0
    audited = audit_cached(
        melon_binding, fast, {"future_price_multiplier": 0.05}
    )
    assert audited["audit_status"] == "passed"
    assert audited["clean_audit"]["outcome"] == audited["outcome"]
