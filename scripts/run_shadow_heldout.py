#!/usr/bin/env python3
"""Capture held-out Carrot observations and evaluate all graphs in shadow mode."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kaggriculture_eval.carrot_adapter import CARROT_ADAPTER  # noqa: E402
from kaggriculture_eval.checkpoint import baseline_match  # noqa: E402
from kaggriculture_eval.graph_registry import bind_registered_graphs  # noqa: E402
from kaggriculture_eval.shadow import evaluate_shadow_proposals, select_shadow_proposal  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, action="append", required=True)
    parser.add_argument("--steps", type=int, default=720)
    args = parser.parse_args()

    from kaggriculture_eval.binding import bind_target

    carrot = bind_target(args.target_root, adapter=CARROT_ADAPTER)
    bindings = bind_registered_graphs(args.target_root)
    records = []
    for seed in args.seed:
        for seat in (0, 1):
            baseline = baseline_match(carrot, seed=seed, seat=seat, steps=args.steps)
            for turn in baseline["turns"]:
                proposals = evaluate_shadow_proposals(turn["observation"], bindings)
                records.append({
                    "seed": seed,
                    "seat": seat,
                    "turn": turn["turn"],
                    "selection": select_shadow_proposal(proposals),
                    "proposals": [proposal.as_dict() for proposal in proposals],
                })
    destination = args.report_dir / "heldout-shadow-trace-v1.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": 1,
        "kind": "heldout-shadow-trace-v1",
        "target_revision": carrot.revision,
        "seeds": args.seed,
        "seats": [0, 1],
        "steps": args.steps,
        "opponent": carrot.opponent_id,
        "graph_ids": list(bindings),
        "observation_count": len(records),
        "simulator_used_for_observation_capture": True,
        "actions_applied_by_selector": False,
        "foundry_packet_written": False,
        "records": records,
    }
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    investment_conflicts = sum(
        len({p["action_class"] for p in record["proposals"] if p["investment_window_open"]}) > 1
        for record in records
    )
    selections = sum(record["selection"]["selected_graph_id"] is not None for record in records)
    print(json.dumps({
        "report_path": str(destination),
        "target_revision": carrot.revision,
        "observation_count": len(records),
        "investment_conflict_count": investment_conflicts,
        "non_pass_selection_count": selections,
        "actions_applied_by_selector": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
