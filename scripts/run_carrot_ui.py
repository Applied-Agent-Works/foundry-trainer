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
from kaggriculture_eval.checkpoint import (
    audit_scheduled_cached,
    evaluate_scheduled_cached,
    read_baseline,
)


def _context(args: argparse.Namespace):
    adapter = LocalInnerLoopAdapter()
    specification = adapter.read_and_validate_spec(args.spec)
    declared = tuple(specification["parameter"]["candidate_values"])
    if args.candidate_values:
        try:
            selected_values = tuple(float(value) for value in json.loads(args.candidate_values))
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError("candidate values must be a JSON array of numbers") from error
    else:
        selected_values = (args.candidate_value,)
    if not selected_values or any(value not in declared for value in selected_values):
        raise ValueError(f"candidate values must be a non-empty subset of the declared envelope: {declared}")
    if args.candidate_value not in selected_values:
        raise ValueError("the selected candidate value must be included in the candidate range")
    specification = deepcopy(specification)
    specification["parameter"]["candidate_values"] = list(selected_values)
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


def _read_interventions(args: argparse.Namespace, specification: dict) -> list[dict]:
    if not args.schedule:
        return []
    try:
        raw = json.loads(args.schedule)
    except json.JSONDecodeError as error:
        raise ValueError("the intervention schedule is not valid JSON") from error
    if not isinstance(raw, list) or not raw:
        raise ValueError("the intervention schedule must be a non-empty JSON list")
    parameter_name = specification["parameter"]["name"]
    declared_values = {float(value) for value in specification["parameter"]["candidate_values"]}
    schedule = [
        {"turn": int(item["step"]), "override": {parameter_name: float(item["value"])} }
        for item in raw
    ]
    if any(item["override"][parameter_name] not in declared_values for item in schedule):
        raise ValueError(f"intervention values must be declared candidates: {sorted(declared_values)}")
    if any(item["turn"] < 0 or item["turn"] >= specification["suite"]["steps"] for item in schedule):
        raise ValueError("intervention steps must fall inside the approved suite")
    return schedule


def _write_temporal_packet(
    report_dir: Path,
    specification: dict,
    binding,
    schedule: list[dict],
    candidate_values: tuple[float, ...],
    baseline_outcomes: dict[str, dict],
    audited_results: list[dict],
) -> tuple[Path, str]:
    """Write an immutable, explicitly temporal inner-loop receipt."""
    import hashlib

    payload = {
        "packet_schema_version": 1,
        "packet_kind": "temporal-intervention-smoke-v1",
        "experiment_id": specification["experiment_id"],
        "target_revision": binding.revision,
        "target_shared_sha256": binding.shared_sha256,
        "target_engine_sha256": binding.engine_sha256,
        "parameter_name": specification["parameter"]["name"],
        "baseline_value": specification["parameter"]["baseline_value"],
        "suite": specification["suite"],
        "interventions": schedule,
        "candidate_values": candidate_values,
        "baseline_outcomes": baseline_outcomes,
        "audited_results": audited_results,
        "all_audits_passed": all(result.get("audit_status") == "passed" for result in audited_results),
        "interpretation_status": "descriptive-temporal-smoke-only; human interpretation required",
        "source_policy_mutation_authorized": False,
    }
    if not payload["all_audits_passed"]:
        raise ValueError("only passing scheduled audits may be written")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    destination = report_dir / "evidence-packets" / "temporal-intervention-smoke-v1.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite existing evidence packet: {destination}")
    destination.write_bytes(encoded)
    return destination, hashlib.sha256(encoded).hexdigest()


def run_stage(args: argparse.Namespace) -> dict:
    adapter, specification, binding, plan = _context(args)
    schedule = _read_interventions(args, specification)
    candidate_values = tuple(float(value) for value in specification["parameter"]["candidate_values"])
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
        if schedule:
            parameter_name = specification["parameter"]["name"]
            fast_results = []
            for candidate_value in candidate_values:
                candidate_schedule = [
                    {"turn": item["turn"], "override": {parameter_name: candidate_value}}
                    for item in schedule
                ]
                for seed, seat in entries_by_key:
                    fast_results.append(evaluate_scheduled_cached(
                        binding,
                        read_baseline(entries_by_key[(seed, seat)].path),
                        candidate_schedule,
                        opponent=binding.shared.carrot_conveyor_agent,
                    ))
        else:
            fast_results = [
                evaluate_declared_candidate_from_cache(
                    specification,
                    binding,
                    entries_by_key[(seed, seat)],
                    {specification["parameter"]["name"]: args.candidate_value},
                )
                for seed, seat in entries_by_key
            ]
        _write_json(state_path, {"baseline_outcomes": baseline_outcomes, "fast_results": fast_results, "schedule": schedule, "candidate_values": candidate_values})
        return {"stage": "inner-loop", "status": "completed", "match_count": len(fast_results), "candidate_count": len(candidate_values)}

    state_payload = _read_json(state_path)
    fast_results = state_payload["fast_results"]
    if args.stage == "divergence":
        divergences = sum(result.get("first_divergence_turn") is not None for result in fast_results)
        return {"stage": "divergence", "status": "completed", "divergent_match_count": divergences}

    if args.stage == "audit":
        audited_results = (
            [
                audit_scheduled_cached(binding, result, result["interventions"], opponent=binding.shared.carrot_conveyor_agent)
                for result in fast_results
            ]
            if schedule
            else [
                audit_declared_candidate_result(specification, binding, result, {specification["parameter"]["name"]: args.candidate_value})
                for result in fast_results
            ]
        )
        state_payload["audited_results"] = audited_results
        _write_json(state_path, state_payload)
        return {"stage": "audit", "status": "completed", "audits_passed": True}

    if args.stage == "packet":
        audited_results = state_payload["audited_results"]
        if state_payload.get("schedule"):
            written_path, written_sha256 = _write_temporal_packet(
                args.report_dir,
                specification,
                binding,
                state_payload["schedule"],
                tuple(state_payload.get("candidate_values", [args.candidate_value])),
                state_payload["baseline_outcomes"],
                audited_results,
            )
            baseline_by_match = state_payload["baseline_outcomes"]
            aggregates = []
            for candidate_value in state_payload.get("candidate_values", [args.candidate_value]):
                results = [result for result in audited_results if result["candidate"]["new_value"] == candidate_value]
                mean_delta = sum(
                    result["outcome"]["decision_reward"]
                    - baseline_by_match[f"{result['match']['seed']}:{result['match']['decision_player']}"]["decision_reward"]
                    for result in results
                ) / len(results)
                aggregates.append({
                    "candidate_value": candidate_value,
                    "match_count": len(results),
                    "mean_paired_decision_delta": mean_delta,
                    "divergent_match_count": sum(result["first_divergence_turn"] is not None for result in results),
                    "all_audits_passed": all(result["audit_status"] == "passed" for result in results),
                })
            return {
                "stage": "packet",
                "status": "completed",
                "packet_path": str(written_path),
                "packet_sha256": written_sha256,
                "match_count": len(audited_results),
                "candidate_count": len(aggregates),
                "audits_passed": True,
                "aggregates": aggregates,
                "intervention_schedule": state_payload["schedule"],
            }
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
    parser.add_argument("--candidate-values", help="JSON array of approved candidate values to run")
    parser.add_argument("--schedule", help='JSON intervention schedule, e.g. [{"step": 0, "value": 40}]')
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
