"""Deterministic packet eligibility and redacted evidence-brief policy."""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
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
MAX_PACKET_TEXT_LENGTH = 4096
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _finite_number(value: Any) -> bool:
    """Return true only for finite JSON-number-like values, never booleans."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _nonnegative_integer(value: Any) -> bool:
    """Reject bool/list/string values before they reach set or arithmetic logic."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _bounded_text(value: Any) -> bool:
    return isinstance(value, str) and 0 < len(value) <= MAX_PACKET_TEXT_LENGTH


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
    if not all(_bounded_text(packet.get(field)) for field in (
        "experiment_id", "parameter_name", "interpretation_status",
    )):
        reasons.append("packet lacks required provenance or interpretation fields")
    if not (
        isinstance(packet.get("target_revision"), str)
        and HEX40.fullmatch(packet["target_revision"])
        and isinstance(packet.get("target_shared_sha256"), str)
        and HEX64.fullmatch(packet["target_shared_sha256"])
        and isinstance(packet.get("target_engine_sha256"), str)
        and HEX64.fullmatch(packet["target_engine_sha256"])
    ):
        reasons.append("packet target provenance has an invalid revision or hash")
    if not _finite_number(packet.get("baseline_value")):
        reasons.append("packet baseline value is not a finite number")

    aggregates = packet.get("aggregates")
    matches = packet.get("per_match")
    seeds = packet.get("suite_seeds")
    seats = packet.get("suite_seats")
    if not isinstance(aggregates, list) or not aggregates or not isinstance(matches, list) or not matches:
        reasons.append("packet has no aggregate or per-match evidence")
    if not isinstance(seeds, list) or not seeds or not isinstance(seats, list) or not seats:
        reasons.append("packet has no declared seed or seat coverage")
    elif (
        any(not _nonnegative_integer(seed) for seed in seeds)
        or len(set(seeds)) != len(seeds)
        or any(seat not in (0, 1) or isinstance(seat, bool) for seat in seats)
        or len(set(seats)) != len(seats)
        or not _nonnegative_integer(packet.get("suite_steps"))
        or packet["suite_steps"] == 0
    ):
        reasons.append("packet suite coverage has invalid seed, seat, or step types")
    if isinstance(aggregates, list):
        if any(not isinstance(item, dict) or set(item) != AGGREGATE_FIELDS for item in aggregates):
            reasons.append("aggregate fields differ from the supported v1 contract")
        else:
            if not all(item["all_audits_passed"] is True for item in aggregates):
                reasons.append("an aggregate reports a non-passing audit")
            if any(
                not item["all_audits_passed"] is True
                or not _finite_number(item["candidate_value"])
                or not _nonnegative_integer(item["match_count"])
                or item["match_count"] == 0
                or not _finite_number(item["mean_paired_decision_delta"])
                or not _nonnegative_integer(item["divergent_match_count"])
                or not _nonnegative_integer(item["total_suffix_actions"])
                for item in aggregates
            ):
                reasons.append("aggregate values have invalid numeric or count types")
    if isinstance(matches, list):
        if any(not isinstance(item, dict) or set(item) != MATCH_FIELDS for item in matches):
            reasons.append("per-match fields differ from the supported v1 contract")
        else:
            if not all(item["audit_status"] == "passed" for item in matches):
                reasons.append("a per-match clean audit did not pass")
            if any(
                not _finite_number(item["candidate_value"])
                or not _nonnegative_integer(item["seed"])
                or item["seat"] not in (0, 1)
                or isinstance(item["seat"], bool)
                or not _finite_number(item["baseline_decision_reward"])
                or not _finite_number(item["candidate_decision_reward"])
                or not _finite_number(item["opponent_reward"])
                or not _finite_number(item["paired_decision_delta"])
                or not _nonnegative_integer(item["clean_actions_run"])
                or not _finite_number(item["clean_elapsed_seconds"])
                or not _nonnegative_integer(item["suffix_actions"])
                or not _finite_number(item["replay_elapsed_seconds"])
                or not _finite_number(item["suffix_elapsed_seconds"])
                or not isinstance(item["fast_mode"], str)
                or not item["fast_mode"]
                or (
                    item["first_divergence_turn"] is not None
                    and not _nonnegative_integer(item["first_divergence_turn"])
                )
                for item in matches
            ):
                reasons.append("per-match evidence has invalid numeric, count, or identity types")
    if packet.get("all_audits_passed") is not True:
        reasons.append("packet-level clean-audit status is not passed")
    if packet.get("source_policy_mutation_authorized") is not False:
        reasons.append("submitted packet improperly carries source-policy authority")

    if all(isinstance(value, list) for value in (aggregates, matches, seeds, seats)):
        candidate_values_raw = [
            item.get("candidate_value") for item in aggregates if isinstance(item, dict)
        ]
        match_values = [
            (item.get("candidate_value"), item.get("seed"), item.get("seat"))
            for item in matches
            if isinstance(item, dict)
        ]
        if (
            all(_finite_number(value) for value in candidate_values_raw)
            and all(_nonnegative_integer(seed) for seed in seeds)
            and all(seat in (0, 1) and not isinstance(seat, bool) for seat in seats)
            and all(
                _finite_number(value)
                and _nonnegative_integer(seed)
                and seat in (0, 1)
                and not isinstance(seat, bool)
                for value, seed, seat in match_values
            )
        ):
            candidate_values = set(candidate_values_raw)
            expected = {(value, seed, seat) for value in candidate_values for seed in seeds for seat in seats}
            observed = set(match_values)
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
