#!/usr/bin/env python3
"""Invoke the existing no-tools Foundry evidence analyst for one packet.

This is a runtime consumer of a notebook-created resource. It never creates
or updates Azure resources and sends only a redacted evidence brief.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


PROJECT_ENDPOINT = "https://foundry-trainer-resource.services.ai.azure.com/api/projects/foundry-trainer"
AGENT_NAME = "evidence-analyst"


def build_redacted_brief(packet: dict) -> dict:
    if packet.get("all_audits_passed") is not True:
        raise ValueError("Foundry feedback requires a packet whose clean audits all passed")
    if packet.get("source_policy_mutation_authorized") is True:
        raise ValueError("the evidence packet grants source-policy authority")

    matches = []
    for result in packet.get("audited_results", []):
        match = result.get("match", {})
        outcome = result.get("outcome", {})
        baseline = packet.get("baseline_outcomes", {}).get(
            f"{match.get('seed')}:{match.get('decision_player')}", {}
        )
        matches.append({
            "seed": match.get("seed"),
            "seat": match.get("decision_player"),
            "mode": result.get("mode"),
            "first_divergence_turn": result.get("first_divergence_turn"),
            "baseline_decision_reward": baseline.get("decision_reward"),
            "candidate_decision_reward": outcome.get("decision_reward"),
            "paired_decision_delta": (
                outcome.get("decision_reward", 0) - baseline.get("decision_reward", 0)
            ),
            "audit_status": result.get("audit_status"),
        })

    return {
        "analyst_contract_version": 1,
        "packet_kind": packet.get("packet_kind", "temporal-intervention-smoke-v1"),
        "packet_sha256": packet.get("packet_sha256"),
        "experiment_id": packet.get("experiment_id"),
        "parameter_name": packet.get("parameter_name"),
        "baseline_value": packet.get("baseline_value"),
        "interventions": [
            {"step": item.get("turn"), "value": item.get("override", {}).get(packet.get("parameter_name"))}
            for item in packet.get("interventions", [])
        ],
        "suite": packet.get("suite"),
        "matches": matches,
        "limitations": [
            "descriptive evidence for this exact deterministic suite",
            "human interpretation is required",
            "no source-policy mutation is authorized",
            "the analyst must not rank candidates or approve a new experiment",
        ],
        "review_status": "pending_human_review",
    }


def invoke(packet_path: Path) -> dict:
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    from analyst.instructions import EVIDENCE_ANALYST_INSTRUCTIONS

    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    brief = build_redacted_brief(packet)
    brief["packet_sha256"] = hashlib.sha256(packet_path.read_bytes()).hexdigest()
    input_text = EVIDENCE_ANALYST_INSTRUCTIONS + "\n\nEvidence brief JSON:\n" + json.dumps(
        brief, sort_keys=True, separators=(",", ":")
    )
    credential = DefaultAzureCredential()
    client = AIProjectClient(
        endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT", PROJECT_ENDPOINT),
        credential=credential,
    )
    try:
        response = client.get_openai_client().responses.create(
            input=input_text,
            max_output_tokens=5000,
            extra_body={"agent_reference": {"name": AGENT_NAME, "type": "agent_reference"}},
        )
        return {
            "status": "completed",
            "agent_name": AGENT_NAME,
            "response_id": getattr(response, "id", None),
            "packet_sha256": brief.get("packet_sha256"),
            "output_text": response.output_text,
            "review_status": "pending_human_review",
        }
    finally:
        client.close()
        credential.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(invoke(args.packet), sort_keys=True))
        return 0
    except Exception as error:  # surface the exact runtime blocker to the button
        print(json.dumps({"status": "blocked", "error": f"{type(error).__name__}: {error}"}, sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
