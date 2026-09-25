"""Fast, simulator-free regression tests for the promoted evidence-analyst boundary."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
from typing import Any

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "carrot-tuning-system"))

from analyst import (  # noqa: E402
    ANALYST_CONTRACT_VERSION,
    EVIDENCE_ANALYST_INSTRUCTIONS,
    PROVISIONAL_EVIDENCE_ANALYST_MODEL,
    EvidenceAnalystRequest,
    SubmittedEvidencePacket,
    assess_packet_eligibility,
    build_evidence_brief,
    validate_analyst_response,
)


@pytest.fixture
def smoke_packet_json() -> dict[str, Any]:
    """Read the source-controlled redacted smoke fixture; no simulator runs."""
    path = REPOSITORY_ROOT / "tests/fixtures/carrot_candidate_evidence_smoke_v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def accepted_request(smoke_packet_json: dict[str, Any]) -> EvidenceAnalystRequest:
    return EvidenceAnalystRequest(
        analyst_contract_version=ANALYST_CONTRACT_VERSION,
        submitted_packet=SubmittedEvidencePacket.from_jsonable(smoke_packet_json),
    )


@pytest.fixture
def accepted_brief(accepted_request: EvidenceAnalystRequest):
    eligibility = assess_packet_eligibility(accepted_request)
    assert eligibility.accepted
    return build_evidence_brief(accepted_request, eligibility)


def compliant_response(brief: Any) -> dict[str, Any]:
    return {
        "analyst_contract_version": ANALYST_CONTRACT_VERSION,
        "packet_sha256": brief.packet_sha256,
        "assessment": "The packet is complete for descriptive analysis only.",
        "citations": [
            {"packet_path": citation.packet_path, "claim": citation.claim}
            for citation in brief.citations
        ],
        "limitations": list(brief.limitations),
        "review_status": "pending_human_review",
    }


def test_accepted_packet_builds_a_descriptive_only_brief(
    accepted_request: EvidenceAnalystRequest,
) -> None:
    eligibility = assess_packet_eligibility(accepted_request)

    assert eligibility.accepted
    assert eligibility.analysis_scope == "descriptive_only"
    assert not eligibility.recommendation_allowed
    assert build_evidence_brief(accepted_request, eligibility).packet_sha256 == (
        accepted_request.submitted_packet.sha256
    )


def test_failed_audit_is_refused_before_a_brief_can_be_built(
    smoke_packet_json: dict[str, Any],
) -> None:
    malformed = deepcopy(smoke_packet_json)
    malformed["per_match"][0]["audit_status"] = "failed"
    request = EvidenceAnalystRequest(
        ANALYST_CONTRACT_VERSION, SubmittedEvidencePacket.from_jsonable(malformed)
    )
    eligibility = assess_packet_eligibility(request)

    assert not eligibility.accepted
    assert any("audit" in reason for reason in eligibility.reasons)
    with pytest.raises(ValueError, match="ineligible"):
        build_evidence_brief(request, eligibility)


@pytest.mark.parametrize(
    ("label", "mutate"),
    [
        ("unhashable aggregate value", lambda packet: packet["aggregates"][0].__setitem__("candidate_value", [])),
        ("unhashable match seed", lambda packet: packet["per_match"][0].__setitem__("seed", [])),
    ],
)
def test_malformed_types_are_refused_cleanly_not_leaked_as_type_errors(
    smoke_packet_json: dict[str, Any], label: str, mutate: Any
) -> None:
    malformed = deepcopy(smoke_packet_json)
    mutate(malformed)
    request = EvidenceAnalystRequest(
        ANALYST_CONTRACT_VERSION, SubmittedEvidencePacket.from_jsonable(malformed)
    )

    eligibility = assess_packet_eligibility(request)

    assert not eligibility.accepted, label
    assert any("invalid" in reason or "type" in reason for reason in eligibility.reasons)


def test_oversized_packet_identity_is_refused_before_model_context_building(
    smoke_packet_json: dict[str, Any],
) -> None:
    malformed = deepcopy(smoke_packet_json)
    malformed["experiment_id"] = "x" * 100_000
    request = EvidenceAnalystRequest(
        ANALYST_CONTRACT_VERSION, SubmittedEvidencePacket.from_jsonable(malformed)
    )

    eligibility = assess_packet_eligibility(request)

    assert not eligibility.accepted
    assert any("provenance" in reason for reason in eligibility.reasons)


def test_response_must_be_bound_to_the_exact_submitted_packet(accepted_brief: Any) -> None:
    response = compliant_response(accepted_brief)
    response["packet_sha256"] = "not-the-submitted-packet"

    with pytest.raises(ValueError, match="not bound"):
        validate_analyst_response(
            response,
            packet_sha256=accepted_brief.packet_sha256,
            allowed_citations=accepted_brief.citations,
            required_limitations=accepted_brief.limitations,
        )


def test_response_rejects_boolean_contract_version_as_not_an_integer(
    accepted_brief: Any,
) -> None:
    response = compliant_response(accepted_brief)
    response["analyst_contract_version"] = True

    with pytest.raises(ValueError, match="unsupported analyst contract version"):
        validate_analyst_response(
            response,
            packet_sha256=accepted_brief.packet_sha256,
            allowed_citations=accepted_brief.citations,
            required_limitations=accepted_brief.limitations,
        )


def test_response_refuses_a_smuggled_planning_field(accepted_brief: Any) -> None:
    response = compliant_response(accepted_brief)
    response["proposed_candidate_value"] = 10

    with pytest.raises(ValueError, match="fields differ"):
        validate_analyst_response(
            response,
            packet_sha256=accepted_brief.packet_sha256,
            allowed_citations=accepted_brief.citations,
            required_limitations=accepted_brief.limitations,
        )


def test_response_refuses_unknown_or_uncited_claim(accepted_brief: Any) -> None:
    response = compliant_response(accepted_brief)
    response["citations"][0]["claim"] = "candidate 10 is globally best"

    with pytest.raises(ValueError, match="outside the evidence brief"):
        validate_analyst_response(
            response,
            packet_sha256=accepted_brief.packet_sha256,
            allowed_citations=accepted_brief.citations,
            required_limitations=accepted_brief.limitations,
        )


def test_response_refuses_dropped_limit_or_nonpending_review(accepted_brief: Any) -> None:
    response = compliant_response(accepted_brief)
    response["limitations"] = response["limitations"][:-1]

    with pytest.raises(ValueError, match="dropped"):
        validate_analyst_response(
            response,
            packet_sha256=accepted_brief.packet_sha256,
            allowed_citations=accepted_brief.citations,
            required_limitations=accepted_brief.limitations,
        )

    response = compliant_response(accepted_brief)
    response["review_status"] = "approved"
    with pytest.raises(ValueError, match="pending human review"):
        validate_analyst_response(
            response,
            packet_sha256=accepted_brief.packet_sha256,
            allowed_citations=accepted_brief.citations,
            required_limitations=accepted_brief.limitations,
        )


def test_compliant_response_passes_and_preserves_all_required_limits(accepted_brief: Any) -> None:
    validated = validate_analyst_response(
        compliant_response(accepted_brief),
        packet_sha256=accepted_brief.packet_sha256,
        allowed_citations=accepted_brief.citations,
        required_limitations=accepted_brief.limitations,
    )

    assert validated.review_status == "pending_human_review"
    assert set(accepted_brief.limitations).issubset(validated.limitations)
    assert len(validated.citations) == len(accepted_brief.citations)


def test_instruction_and_model_choice_are_source_controlled_and_non_deployed() -> None:
    assert "only task is to explain facts" in EVIDENCE_ANALYST_INSTRUCTIONS
    assert "Do not calculate game results" in EVIDENCE_ANALYST_INSTRUCTIONS
    assert PROVISIONAL_EVIDENCE_ANALYST_MODEL.model_name == "gpt-5.6-luna"
    assert PROVISIONAL_EVIDENCE_ANALYST_MODEL.deployment_name is None
    assert PROVISIONAL_EVIDENCE_ANALYST_MODEL.deployment_status == "not_deployed"
