#!/usr/bin/env python3
"""Execute the approved Carrot smoke contract for the local review backend.

This is an intentionally narrow bridge. It accepts only the source-controlled
approved contract, a pinned sibling target, and ignored per-run directories.
It prints one JSON receipt and never edits policy source or calls Foundry.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path

from evaluator.runner import (
    LocalInnerLoopAdapter,
    LocalRunRequest,
    audit_declared_candidate_result,
    build_local_smoke_evidence_packet,
    evaluate_declared_candidate_from_cache,
    write_local_smoke_evidence_packet,
)


def _context(args: argparse.Namespace):
    adapter = LocalInnerLoopAdapter()
    specification = adapter.read_and_validate_spec(args.spec)
    declared = tuple(specification["parameter"]["candidate_values"])
    if args.candidate_value not in declared:
        raise ValueError(f"candidate {args.candidate_value} is not declared: {declared}")
    specification = deepcopy(specification)
    specification["parameter"]["candidate_values"] = [args.candidate_value]
    adapter.authorize_execution_operation(specification, "candidate_evidence_run")
    binding = adapter.bind_and_validate_target(specification, args.target_root)
    adapter.authorize_lifecycle(specification)
    adapter.validate_local_controls(specification, binding)
    plan = adapter.plan_baseline_caches(specification, binding, args.cache_root)
    return adapter, specification, binding, plan


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def run_stage(args: argparse.Namespace) -> dict:
    adapter, specification, binding, plan = _context(args)
    stage_dir = args.report_dir / "stages"
    state_path = stage_dir / "inner-loop.json"
    if args.stage == "baseline":
        state = adapter.inspect_baseline_cache_state(plan)
        read_results = tuple(
            adapter.read_and_validate_baseline_cache(entry, specification, binding)
            for entry in state.present_entries
        )
        preparation = adapter.plan_baseline_cache_preparation(state, read_results)
        for action in preparation.materialize_actions:
            adapter.materialize_selected_baseline(action, specification, binding)
        return {"stage": "baseline", "status": "completed", "cache_count": len(plan.entries)}

    state = adapter.inspect_baseline_cache_state(plan)
    read_results = tuple(
        adapter.read_and_validate_baseline_cache(entry, specification, binding)
        for entry in state.present_entries
    )
    if any(not result.is_reusable_candidate for result in read_results) or len(read_results) != len(plan.entries):
        raise ValueError("baseline stage must complete successfully before candidate stages")
    baseline_outcomes = {
        f"{entry.seed}:{entry.seat}": adapter.read_validated_baseline_outcome(entry, specification, binding)
        for entry in plan.entries
    }
    entries_by_key = {(entry.seed, entry.seat): entry for entry in plan.entries}

    if args.stage == "inner-loop":
        fast_results = [
            evaluate_declared_candidate_from_cache(
                specification,
                binding,
                entries_by_key[(seed, seat)],
                {specification["parameter"]["name"]: args.candidate_value},
            )
            for seed, seat in entries_by_key
        ]
        _write_json(state_path, {"baseline_outcomes": baseline_outcomes, "fast_results": fast_results})
        return {"stage": "inner-loop", "status": "completed", "match_count": len(fast_results)}

    state_payload = _read_json(state_path)
    fast_results = state_payload["fast_results"]
    if args.stage == "divergence":
        divergences = sum(result.get("first_divergence_turn") is not None for result in fast_results)
        return {"stage": "divergence", "status": "completed", "divergent_match_count": divergences}

    if args.stage == "audit":
        audited_results = [
            audit_declared_candidate_result(specification, binding, result, {specification["parameter"]["name"]: args.candidate_value})
            for result in fast_results
        ]
        state_payload["audited_results"] = audited_results
        _write_json(state_path, state_payload)
        return {"stage": "audit", "status": "completed", "audits_passed": True}

    if args.stage == "packet":
        audited_results = state_payload["audited_results"]
        baseline = {
            tuple(int(part) for part in key.split(":")): value
            for key, value in state_payload["baseline_outcomes"].items()
        }
        packet = build_local_smoke_evidence_packet(specification, binding, tuple(audited_results), baseline)
        written = write_local_smoke_evidence_packet(packet, args.report_dir)
        return {
            "stage": "packet",
            "status": "completed",
            "packet_path": str(written.path),
            "packet_sha256": written.sha256,
            "match_count": len(packet.per_match),
            "candidate_count": len(packet.aggregates),
            "audits_passed": packet.all_audits_passed,
            "aggregates": [
                {
                    "candidate_value": aggregate.candidate_value,
                    "match_count": aggregate.match_count,
                    "mean_paired_decision_delta": aggregate.mean_paired_decision_delta,
                    "divergent_match_count": aggregate.divergent_match_count,
                    "all_audits_passed": aggregate.all_audits_passed,
                }
                for aggregate in packet.aggregates
            ],
        }
    raise ValueError(f"unsupported stage: {args.stage}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--candidate-value", type=float, required=True)
    parser.add_argument("--stage", choices=["full", "baseline", "inner-loop", "divergence", "audit", "packet"], default="full")
    args = parser.parse_args()

    if args.stage != "full":
        print(json.dumps(run_stage(args), sort_keys=True))
        return 0

    adapter = LocalInnerLoopAdapter()
    specification = adapter.read_and_validate_spec(args.spec)
    adapter.authorize_execution_operation(specification, "candidate_evidence_run")
    binding = adapter.bind_and_validate_target(specification, args.target_root)
    adapter.authorize_lifecycle(specification)
    adapter.validate_local_controls(specification, binding)

    # Baselines are created only in this run's ignored directory. Existing
    # invalid evidence is never replaced; the adapter stops instead.
    request = LocalRunRequest(
        spec_path=args.spec,
        target_root=args.target_root,
        cache_root=args.cache_root,
        report_directory=args.report_dir,
        candidate_values=(args.candidate_value,),
    )
    plan = adapter.plan_baseline_caches(specification, binding, args.cache_root)
    state = adapter.inspect_baseline_cache_state(plan)
    read_results = tuple(
        adapter.read_and_validate_baseline_cache(entry, specification, binding)
        for entry in state.present_entries
    )
    preparation = adapter.plan_baseline_cache_preparation(state, read_results)
    for action in preparation.materialize_actions:
        adapter.materialize_selected_baseline(action, specification, binding)

    batch = adapter.run(request)
    completed = adapter.complete_local_candidate_batch(batch, args.report_dir)
    print(json.dumps({
        "status": "completed",
        "execution_mode": "full_simulator",
        "target_revision": binding.revision,
        "target_root": str(binding.root),
        "cache_root": str(args.cache_root),
        "report_directory": str(args.report_dir),
        "packet_path": str(completed.packet_write.path),
        "packet_sha256": completed.packet_write.sha256,
        "match_count": len(completed.evidence_packet.per_match),
        "candidate_count": len(completed.evidence_packet.aggregates),
        "aggregates": [
            {
                "candidate_value": aggregate.candidate_value,
                "match_count": aggregate.match_count,
                "mean_paired_decision_delta": aggregate.mean_paired_decision_delta,
                "divergent_match_count": aggregate.divergent_match_count,
                "all_audits_passed": aggregate.all_audits_passed,
            }
            for aggregate in completed.evidence_packet.aggregates
        ],
        "audits_passed": completed.evidence_packet.all_audits_passed,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
