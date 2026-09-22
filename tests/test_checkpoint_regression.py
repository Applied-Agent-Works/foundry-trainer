from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kaggriculture_eval.binding import bind_target
from kaggriculture_eval.checkpoint import audit_cached, baseline_match, evaluate_cached


def test_checkpoint_resume_matches_clean_reruns() -> None:
    """Prove reuse plus restored early and late suffixes on one deterministic match."""
    binding = bind_target()
    baseline = baseline_match(binding, seed=42, seat=0, steps=144)

    unchanged = audit_cached(binding, evaluate_cached(binding, baseline, {"pass_utility": 0.0}), {"pass_utility": 0.0})
    assert unchanged["mode"] == "reused-baseline"
    assert unchanged["first_divergence_turn"] is None
    assert unchanged["suffix_actions"] == 0
    assert unchanged["audit_status"] == "passed"

    late = audit_cached(binding, evaluate_cached(binding, baseline, {"pass_utility": 50.0}), {"pass_utility": 50.0})
    assert late["mode"] == "restored-suffix"
    assert 0 < late["first_divergence_turn"] < 143
    assert 0 < late["suffix_actions"] < late["clean_audit"]["actions_run"]
    assert late["audit_status"] == "passed"

    early = audit_cached(binding, evaluate_cached(binding, baseline, {"pass_utility": 100.0}), {"pass_utility": 100.0})
    assert early["mode"] == "restored-suffix"
    assert early["first_divergence_turn"] == 0
    assert early["suffix_actions"] == early["clean_audit"]["actions_run"]
    assert early["audit_status"] == "passed"
