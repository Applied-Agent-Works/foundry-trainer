"""Local, deterministic boundaries for the future Foundry evidence analyst.

This package deliberately has no model client, Foundry client, filesystem path
input, or hosted-agent entry point. It preserves the reviewed contract and
policy gates until a separately approved deployment slice wires them together.
"""

from .contracts import (
    ANALYST_CONTRACT_VERSION,
    EvidenceAnalystRequest,
    EvidenceAnalystResponse,
    EvidenceCitation,
    SubmittedEvidencePacket,
    validate_analyst_response,
)
from .instructions import (
    EVIDENCE_ANALYST_INSTRUCTIONS,
    EVIDENCE_ANALYST_INSTRUCTION_VERSION,
    PROVISIONAL_EVIDENCE_ANALYST_MODEL,
    ProvisionalModelChoice,
)
from .policy import (
    EvidenceBrief,
    PacketEligibility,
    assess_packet_eligibility,
    build_evidence_brief,
)

__all__ = [
    "ANALYST_CONTRACT_VERSION",
    "EVIDENCE_ANALYST_INSTRUCTIONS",
    "EVIDENCE_ANALYST_INSTRUCTION_VERSION",
    "EvidenceAnalystRequest",
    "EvidenceAnalystResponse",
    "EvidenceBrief",
    "EvidenceCitation",
    "PROVISIONAL_EVIDENCE_ANALYST_MODEL",
    "PacketEligibility",
    "ProvisionalModelChoice",
    "SubmittedEvidencePacket",
    "assess_packet_eligibility",
    "build_evidence_brief",
    "validate_analyst_response",
]
