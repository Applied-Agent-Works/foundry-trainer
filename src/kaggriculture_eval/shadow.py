"""Non-mutating shadow evaluation for the registered decision graphs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping

from .binding import TargetBinding
from .checkpoint import parameter_candidate
from .graph_registry import DecisionGraphDescriptor, get_graph_descriptor


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _action_class(action: Mapping[str, Any]) -> str:
    """Give the proposal a coarse comparable label without choosing an action."""
    commands: list[str] = []
    for value in action.values():
        if not isinstance(value, list):
            continue
        for command in value:
            if isinstance(command, list) and command:
                commands.append(str(command[0]))
            elif isinstance(command, str):
                commands.append(command)
    if "PLANT" in commands or "BUY_SEED" in commands:
        return "plant"
    if any(command in commands for command in ("WATER", "HARVEST", "EAST", "WEST", "NORTH", "SOUTH")):
        return "care-or-move"
    if commands and all(command == "PASS" for command in commands):
        return "pass"
    return "other"


def _phase(
    observation: Mapping[str, Any],
    descriptor: DecisionGraphDescriptor,
    action_class: str,
) -> tuple[str, bool]:
    """Separate maintenance from a fully eligible investment decision."""
    try:
        farm = observation["farms"][observation["player"]]
        tiles = farm["tiles"]
    except (KeyError, IndexError, TypeError):
        return "unknown", False
    active = any(
        isinstance(tile, dict)
        and tile.get("kind") == "PLANT"
        and tile.get("crop") == descriptor.crop
        for row in tiles
        for tile in row
    )
    if active:
        return "maintenance", False
    empty_tile = any(tile is None for row in tiles for tile in row)
    if action_class in {"plant", "pass"} and not empty_tile:
        return "blocked-no-empty-tile", False
    private = observation.get("private", {})
    seeds = private.get("seeds", {}).get(descriptor.crop, 0)
    money = farm.get("money", 0)
    if action_class in {"plant", "pass"} and not (seeds > 0 or money >= descriptor.seed_cost):
        return "blocked-no-seed-or-money", False
    day = observation.get("day")
    if action_class in {"plant", "pass"} and isinstance(day, int) and day + descriptor.planning_horizon >= 30:
        return "blocked-season-horizon", False
    if action_class in {"plant", "pass"} and empty_tile:
        return "investment-decision", True
    if not empty_tile:
        return "blocked-no-empty-tile", False
    return "preparation", False


def _utility(
    binding: TargetBinding,
    descriptor: DecisionGraphDescriptor,
    observation: Mapping[str, Any],
    parameters: Any,
) -> tuple[float | None, dict[str, float], str]:
    """Read the graph's existing utility calculation without changing policy."""
    if descriptor.graph_id == "carrot_investment":
        explained = binding.shared.explain_carrot_decision(observation, parameters)
        utility = float(explained["plant_utility"])
        pass_utility = float(explained["pass_utility"])
        return (
            utility,
            {"plant_utility": utility, "pass_utility": pass_utility, "utility_margin": utility - pass_utility},
            f"Carrot plant utility {utility:g} versus PASS utility {pass_utility:g}.",
        )
    helper = getattr(binding.parameter_module, "expected_crop_value", None)
    if helper is None:
        helper = getattr(binding.parameter_module, "expected_ongoing_crop_value", None)
    if helper is None:
        return None, {}, "This graph does not expose a normalized utility calculation yet."
    crop = getattr(binding.shared, descriptor.adapter.crop_constant_attribute or "")
    utility = float(helper(observation, crop, parameters))
    pass_utility = float(getattr(parameters, "pass_utility", 0.0))
    return (
        utility,
        {"plant_utility": utility, "pass_utility": pass_utility, "utility_margin": utility - pass_utility},
        f"{descriptor.display_name} plant utility {utility:g} versus PASS utility {pass_utility:g}.",
    )


@dataclass(frozen=True)
class ShadowProposal:
    """One graph's proposal for an observation; it is never applied."""

    graph_id: str
    graph_name: str
    crop: str
    lifecycle: str
    graph_adapter_id: str
    action_class: str
    decision_phase: str
    investment_window_open: bool
    utility: float | None
    utility_components: dict[str, float]
    utility_explanation: str
    action: dict[str, Any]
    parameter_values: dict[str, Any]
    parameter_override: dict[str, float]
    observation_sha256: str
    target_revision: str
    policy_id: str
    opponent_id: str
    source_hashes: dict[str, str]
    limitations: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-safe local record for comparison and diagnostics."""
        return asdict(self)


def evaluate_shadow_proposals(
    observation: dict[str, Any],
    bindings: Mapping[str, TargetBinding],
    overrides: Mapping[str, Mapping[str, float]] | None = None,
) -> tuple[ShadowProposal, ...]:
    """Evaluate all supplied graphs without stepping the simulator.

    ``overrides`` is optional and remains an in-memory candidate input.  The
    function does not select a winner, mutate the observation, or apply any
    returned action to a simulator.
    """
    overrides = overrides or {}
    observation_hash = hashlib.sha256(_canonical(observation).encode()).hexdigest()
    proposals: list[ShadowProposal] = []
    for graph_id, binding in bindings.items():
        descriptor = get_graph_descriptor(graph_id)
        override = {str(name): float(value) for name, value in overrides.get(graph_id, {}).items()}
        if override:
            parameters, _ = parameter_candidate(binding, override)
        else:
            parameters = binding.default_parameters
        action = binding.decision_agent(observation, parameters)
        action_copy = json.loads(json.dumps(action))
        action_class = _action_class(action_copy)
        decision_phase, investment_window_open = _phase(
            observation, descriptor, action_class
        )
        utility, utility_components, utility_explanation = _utility(
            binding, descriptor, observation, parameters
        )
        proposals.append(
            ShadowProposal(
                graph_id=descriptor.graph_id,
                graph_name=descriptor.display_name,
                crop=descriptor.crop,
                lifecycle=descriptor.lifecycle,
                graph_adapter_id=descriptor.adapter.adapter_id,
                action_class=action_class,
                decision_phase=decision_phase,
                investment_window_open=investment_window_open,
                utility=utility,
                utility_components=utility_components,
                utility_explanation=utility_explanation,
                action=action_copy,
                parameter_values=asdict(parameters),
                parameter_override=override,
                observation_sha256=observation_hash,
                target_revision=binding.revision,
                policy_id=binding.policy_id,
                opponent_id=binding.opponent_id,
                source_hashes=dict(sorted(binding.source_hashes.items())),
                limitations=descriptor.limitations,
            )
        )
    return tuple(proposals)


def select_shadow_proposal(proposals: tuple[ShadowProposal, ...]) -> dict[str, Any]:
    """Select the highest positive-utility proposal without applying it."""
    candidates = [
        proposal
        for proposal in proposals
        if proposal.investment_window_open
        and proposal.action_class == "plant"
        and proposal.utility_components.get("utility_margin", 0.0) > 0
    ]
    candidates.sort(key=lambda proposal: (-proposal.utility_components["utility_margin"], proposal.graph_id))
    if not candidates:
        return {
            "selected_graph_id": None,
            "decision": "PASS",
            "reason": "No eligible graph proposed a positive-utility planting action.",
            "candidate_graph_ids": [],
        }
    selected = candidates[0]
    return {
        "selected_graph_id": selected.graph_id,
        "decision": "PLANT",
        "reason": selected.utility_explanation,
        "candidate_graph_ids": [proposal.graph_id for proposal in candidates],
        "selected_utility_margin": selected.utility_components["utility_margin"],
    }


def trace_shadow_observations(
    observations: list[tuple[int, int, int, dict[str, Any]]],
    bindings: Mapping[str, TargetBinding],
    overrides: Mapping[str, Mapping[str, float]] | None = None,
) -> tuple[dict[str, Any], ...]:
    """Trace registered graph proposals over shared observations.

    Each observation is ``(seed, seat, turn, observation_dict)``.  The source
    observation stream is read-only; this function only calls policy functions
    and never advances or mutates a simulator.
    """
    rows: list[dict[str, Any]] = []
    for seed, seat, turn, observation in observations:
        proposals = evaluate_shadow_proposals(observation, bindings, overrides)
        action_classes = {proposal.graph_id: proposal.action_class for proposal in proposals}
        decision_phases = {proposal.graph_id: proposal.decision_phase for proposal in proposals}
        investment_windows = {
            proposal.graph_id: proposal.investment_window_open for proposal in proposals
        }
        rows.append({
            "seed": seed,
            "seat": seat,
            "turn": turn,
            "observation_sha256": proposals[0].observation_sha256 if proposals else None,
            "action_classes": action_classes,
            "decision_phases": decision_phases,
            "investment_windows": investment_windows,
            "disagreement": len(set(action_classes.values())) > 1,
            "investment_disagreement": len({
                proposal.action_class
                for proposal in proposals
                if proposal.investment_window_open
            }) > 1,
            "proposals": [proposal.as_dict() for proposal in proposals],
        })
    return tuple(rows)
