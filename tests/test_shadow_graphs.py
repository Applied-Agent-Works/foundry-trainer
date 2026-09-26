from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kaggriculture_eval.graph_registry import (  # noqa: E402
    GRAPH_REGISTRY,
    bind_registered_graphs,
    graph_descriptors,
)
from kaggriculture_eval.shadow import evaluate_shadow_proposals, select_shadow_proposal  # noqa: E402
from kaggriculture_eval.shadow_suite import build_observation  # noqa: E402
from kaggriculture_eval.shadow import trace_shadow_observations  # noqa: E402


def test_registry_contains_the_five_current_graphs() -> None:
    assert tuple(descriptor.graph_id for descriptor in graph_descriptors()) == (
        "carrot_investment",
        "wheat_crop",
        "melon_investment",
        "tomato_crop",
        "strawberry_crop",
    )
    assert {descriptor.lifecycle for descriptor in graph_descriptors()} == {"one-time-crop", "ongoing-crop"}
    assert all("candidate" in descriptor.supported_stages for descriptor in graph_descriptors())


def test_synthetic_fixture_exercises_true_multi_crop_conflicts() -> None:
    fixture = json.loads((ROOT / "tests/fixtures/shadow_multi_eligible_v1.json").read_text())
    bindings = bind_registered_graphs(ROOT.parent / "kaggriculture")
    observations = [
        (item["seed"], item["seat"], item["turn"], item["observation"])
        for item in fixture
    ]
    trace = trace_shadow_observations(observations, bindings)
    assert len(trace) == 3
    assert sum(row["investment_disagreement"] for row in trace) == 2


def test_selector_chooses_highest_positive_utility_for_fixture() -> None:
    fixture = json.loads((ROOT / "tests/fixtures/shadow_multi_eligible_v1.json").read_text())
    bindings = bind_registered_graphs(ROOT.parent / "kaggriculture")
    selected = []
    for item in fixture:
        proposals = evaluate_shadow_proposals(item["observation"], bindings)
        selected.append(select_shadow_proposal(proposals)["selected_graph_id"])
    assert selected == ["melon_investment", "strawberry_crop", "melon_investment"]


def test_broader_selector_suite_has_twelve_scenarios() -> None:
    fixture = json.loads((ROOT / "tests/fixtures/shadow_selector_suite_v1.json").read_text())
    bindings = bind_registered_graphs(ROOT.parent / "kaggriculture")
    records = []
    for scenario in fixture:
        proposals = evaluate_shadow_proposals(build_observation(scenario), bindings)
        records.append(select_shadow_proposal(proposals))
    assert len(records) == 12
    assert records[8]["selected_graph_id"] is None  # late season
    assert records[9]["selected_graph_id"] is None  # no empty tile
    assert records[10]["selected_graph_id"] is None  # no money or seed


@pytest.mark.simulator
def test_shadow_evaluates_all_graphs_without_stepping_the_simulator() -> None:
    from kaggle_environments import make

    environment = make("kaggriculture", configuration={"episodeSteps": 8, "seed": 42}, debug=True)
    environment.reset(2)
    observation = environment.state[0].observation
    bindings = bind_registered_graphs(ROOT.parent / "kaggriculture")

    proposals = evaluate_shadow_proposals(
        observation,
        bindings,
        overrides={"wheat_crop": {"future_price_multiplier": 0.05}},
    )

    assert tuple(proposal.graph_id for proposal in proposals) == tuple(GRAPH_REGISTRY)
    assert all(proposal.action for proposal in proposals)
    assert all(proposal.observation_sha256 for proposal in proposals)
    assert all(proposal.decision_phase == "investment-decision" for proposal in proposals)
    assert all(proposal.investment_window_open for proposal in proposals)
    assert proposals[1].parameter_override == {"future_price_multiplier": 0.05}
    trace = trace_shadow_observations([(42, 0, 0, observation)], bindings)
    assert len(trace) == 1
    assert len(trace[0]["proposals"]) == 5
    assert isinstance(trace[0]["disagreement"], bool)
    assert trace[0]["investment_disagreement"] is False
    assert environment.done is False
    assert environment.state[0].observation == observation
