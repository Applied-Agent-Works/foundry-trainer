#!/usr/bin/env python3
"""Execute the approved Carrot smoke contract for the local review backend.

This is an intentionally narrow bridge. It accepts only the source-controlled
approved contract, a pinned sibling target, and ignored per-run directories.
It prints one JSON receipt and never edits policy source or calls Foundry.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluator.runner import LocalInnerLoopAdapter, LocalRunRequest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    args = parser.parse_args()

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
