"""Immutable request and fail-closed response contracts for evidence analysis."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Collection


ANALYST_CONTRACT_VERSION = 1
REQUIRED_REVIEW_STATUS = "pending_human_review"

RESPONSE_FIELDS = frozenset({
    "analyst_contract_version",
    "packet_sha256",
    "assessment",
    "citations",
    "limitations",
    "review_status",
})
CITATION_FIELDS = frozenset({"packet_path", "claim"})


@dataclass(frozen=True)
class SubmittedEvidencePacket:
    """One immutable canonical JSON packet supplied to the analyst boundary."""

    canonical_json: str
    sha256: str

    @classmethod
    def from_jsonable(cls, value: dict[str, Any]) -> "SubmittedEvidencePacket":
        """Canonicalize a JSON object so later caller mutation cannot alter it."""
        if not isinstance(value, dict):
            raise TypeError("submitted evidence must be a JSON object")
        canonical_json = json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        return cls(
            canonical_json=canonical_json,
            sha256=hashlib.sha256(canonical_json.encode("utf-8")).hexdigest(),
        )

    def as_mapping(self) -> dict[str, Any]:
        """Return a fresh mapping; callers cannot mutate the submitted bytes."""
        return json.loads(self.canonical_json)


@dataclass(frozen=True)
class EvidenceAnalystRequest:
    """The complete evidence input permitted to reach a future analyst model."""

    analyst_contract_version: int
    submitted_packet: SubmittedEvidencePacket


@dataclass(frozen=True)
class EvidenceCitation:
    """One packet path and its permitted factual claim."""

    packet_path: str
    claim: str


@dataclass(frozen=True)
class EvidenceAnalystResponse:
    """A descriptive response shape with no planning or mutation fields."""

    analyst_contract_version: int
    packet_sha256: str
    assessment: str
    citations: tuple[EvidenceCitation, ...]
    limitations: tuple[str, ...]
    review_status: str


def validate_analyst_response(
    response_json: dict[str, Any],
    *,
    packet_sha256: str,
    allowed_citations: Collection[EvidenceCitation],
    required_limitations: Collection[str],
) -> EvidenceAnalystResponse:
    """Accept only a response bound to one brief and pending human review.

    This is deliberately a structural boundary. It prevents unsupported paths,
    dropped limits, extra planning fields, and a response for another packet;
    it cannot by itself prove that free-form prose is truthful.
    """
    if not isinstance(response_json, dict) or set(response_json) != RESPONSE_FIELDS:
        raise ValueError("response fields differ from the analyst v1 contract")
    if response_json["analyst_contract_version"] != ANALYST_CONTRACT_VERSION:
        raise ValueError("response uses an unsupported analyst contract version")
    if response_json["packet_sha256"] != packet_sha256:
        raise ValueError("response is not bound to the submitted packet")
    if response_json["review_status"] != REQUIRED_REVIEW_STATUS:
        raise ValueError("response does not preserve pending human review")
    if not isinstance(response_json["assessment"], str) or not response_json["assessment"].strip():
        raise ValueError("response assessment must be a non-empty string")

    allowed_pairs = {(item.packet_path, item.claim) for item in allowed_citations}
    raw_citations = response_json["citations"]
    if not isinstance(raw_citations, list) or not raw_citations:
        raise ValueError("response needs at least one packet-backed citation")
    citations: list[EvidenceCitation] = []
    for raw_citation in raw_citations:
        if not isinstance(raw_citation, dict) or set(raw_citation) != CITATION_FIELDS:
            raise ValueError("citation fields differ from the analyst v1 contract")
        citation = EvidenceCitation(**raw_citation)
        if (citation.packet_path, citation.claim) not in allowed_pairs:
            raise ValueError("response cites a claim outside the evidence brief")
        citations.append(citation)

    raw_limitations = response_json["limitations"]
    if not isinstance(raw_limitations, list) or not all(
        isinstance(item, str) and item for item in raw_limitations
    ):
        raise ValueError("response limitations must be non-empty strings")
    if not set(required_limitations).issubset(raw_limitations):
        raise ValueError("response dropped one or more evidence-brief limitations")

    return EvidenceAnalystResponse(
        analyst_contract_version=response_json["analyst_contract_version"],
        packet_sha256=response_json["packet_sha256"],
        assessment=response_json["assessment"],
        citations=tuple(citations),
        limitations=tuple(raw_limitations),
        review_status=response_json["review_status"],
    )
