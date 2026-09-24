"""Deterministic packet eligibility and redacted evidence-brief policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import (
    ANALYST_CONTRACT_VERSION,
    EvidenceAnalystRequest,
    EvidenceCitation,
)


SUPPORTED_PACKET_SCHEMA_VERSION = 1
PACKET_FIELDS = frozenset({
    "aggregates", "all_audits_passed", "baseline_value", "experiment_id",
    "interpretation_status", "packet_schema_version", "parameter_name", "per_match",
    "source_policy_mutation_authorized", "suite_seats", "suite_seeds", "suite_steps",
    "target_engine_sha256", "target_revision", "target_shared_sha256",
})
AGGREGATE_FIELDS = frozenset({
    "all_audits_passed", "candidate_value", "divergent_match_count", "match_count",
    "mean_candidate_decision_reward", "mean_paired_decision_delta", "total_suffix_actions",
})
MATCH_FIELDS = frozenset({
    "audit_status", "baseline_decision_reward", "candidate_decision_reward",
    "candidate_value", "clean_actions_run", "clean_elapsed_seconds", "fast_mode",
    "first_divergence_turn", "opponent_reward", "paired_decision_delta",
    "replay_elapsed_seconds", "seat", "seed", "suffix_actions", "suffix_elapsed_seconds",
})


@dataclass(frozen=True)
class PacketEligibility:
    """A fail-closed decision about whether descriptive analysis may begin."""

    accepted: bool
    analysis_scope: str
    recommendation_allowed: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class CandidateEvidenceSummary:
    """One descriptive aggregate with no success/failure label."""

    candidate_value: float
    match_count: int
    mean_paired_decision_delta: float
    divergent_match_count: int
    total_suffix_actions: int


@dataclass(frozen=True)
class EvidenceBrief:
    """Redacted factual context permitted to reach a future analyst role."""

    packet_sha256: str
    experiment_id: str
    parameter_name: str
    baseline_value: float
    suite_seed_count: int
    suite_seats: tuple[int, ...]
    suite_steps: int
    candidates: tuple[CandidateEvidenceSummary, ...]
    limitations: tuple[str, ...]
    citations: tuple[EvidenceCitation, ...]


def assess_packet_eligibility(request: EvidenceAnalystRequest) -> PacketEligibility:
    """Accept only complete, clean-audited v1 packets for descriptive analysis."""
    reasons: list[str] = []
    if request.analyst_contract_version != ANALYST_CONTRACT_VERSION:
        reasons.append("unsupported analyst contract version")

    packet = request.submitted_packet.as_mapping()
    if set(packet) != PACKET_FIELDS:
        reasons.append("packet fields differ from the supported v1 contract")
    if packet.get("packet_schema_version") != SUPPORTED_PACKET_SCHEMA_VERSION:
        reasons.append("unsupported packet schema version")
    if not all(isinstance(packet.get(field), str) and packet[field] for field in (
        "experiment_id", "parameter_name", "target_revision", "target_shared_sha256",
        "target_engine_sha256", "interpretation_status",
    )):
        reasons.append("packet lacks required provenance or interpretation fields")

    aggregates = packet.get("aggregates")
    matches = packet.get("per_match")
    seeds = packet.get("suite_seeds")
    seats = packet.get("suite_seats")
    if not isinstance(aggregates, list) or not aggregates or not isinstance(matches, list) or not matches:
        reasons.append("packet has no aggregate or per-match evidence")
    if not isinstance(seeds, list) or not seeds or not isinstance(seats, list) or not seats:
        reasons.append("packet has no declared seed or seat coverage")
    if isinstance(aggregates, list):
        if any(not isinstance(item, dict) or set(item) != AGGREGATE_FIELDS for item in aggregates):
            reasons.append("aggregate fields differ from the supported v1 contract")
        elif not all(item["all_audits_passed"] is True for item in aggregates):
            reasons.append("an aggregate reports a non-passing audit")
    if isinstance(matches, list):
        if any(not isinstance(item, dict) or set(item) != MATCH_FIELDS for item in matches):
            reasons.append("per-match fields differ from the supported v1 contract")
        elif not all(item["audit_status"] == "passed" for item in matches):
            reasons.append("a per-match clean audit did not pass")
    if packet.get("all_audits_passed") is not True:
        reasons.append("packet-level clean-audit status is not passed")
    if packet.get("source_policy_mutation_authorized") is not False:
        reasons.append("submitted packet improperly carries source-policy authority")

    if all(isinstance(value, list) for value in (aggregates, matches, seeds, seats)):
        candidate_values = {item.get("candidate_value") for item in aggregates if isinstance(item, dict)}
        expected = {(value, seed, seat) for value in candidate_values for seed in seeds for seat in seats}
        observed = {
            (item.get("candidate_value"), item.get("seed"), item.get("seat"))
            for item in matches
            if isinstance(item, dict)
        }
        if not candidate_values or observed != expected or len(matches) != len(observed):
            reasons.append("per-match evidence does not exactly cover the declared aggregate/seed/seat envelope")

    if reasons:
        return PacketEligibility(False, "refused", False, tuple(reasons))
    return PacketEligibility(
        accepted=True,
        analysis_scope="descriptive_only",
        recommendation_allowed=False,
        reasons=(
            "packet is complete and clean-audited for descriptive analysis",
            "the analyst contract never grants recommendation or source-policy authority",
            "the packet retains its own interpretation limit: " + packet["interpretation_status"],
        ),
    )


def build_evidence_brief(
    request: EvidenceAnalystRequest, eligibility: PacketEligibility
) -> EvidenceBrief:
    """Summarize an eligible packet without ranking or recommending candidates."""
    if not eligibility.accepted:
        raise ValueError("cannot build an analyst brief from an ineligible packet")
    packet = request.submitted_packet.as_mapping()
    candidates = tuple(
        CandidateEvidenceSummary(
            candidate_value=float(aggregate["candidate_value"]),
            match_count=int(aggregate["match_count"]),
            mean_paired_decision_delta=float(aggregate["mean_paired_decision_delta"]),
            divergent_match_count=int(aggregate["divergent_match_count"]),
            total_suffix_actions=int(aggregate["total_suffix_actions"]),
        )
        for aggregate in packet["aggregates"]
    )
    citations = tuple(
        EvidenceCitation(
            packet_path=f"aggregates[{index}]",
            claim=(
                f"candidate {summary.candidate_value:g}: mean paired delta "
                f"{summary.mean_paired_decision_delta:g} across {summary.match_count} matches"
            ),
        )
        for index, summary in enumerate(candidates)
    )
    return EvidenceBrief(
        packet_sha256=request.submitted_packet.sha256,
        experiment_id=packet["experiment_id"],
        parameter_name=packet["parameter_name"],
        baseline_value=float(packet["baseline_value"]),
        suite_seed_count=len(packet["suite_seeds"]),
        suite_seats=tuple(packet["suite_seats"]),
        suite_steps=int(packet["suite_steps"]),
        candidates=candidates,
        limitations=(
            packet["interpretation_status"],
            f"observed seed count: {len(packet['suite_seeds'])}",
            "no source-policy mutation is authorized",
            "this brief does not rank candidates or propose a new experiment",
        ),
        citations=citations,
    )
