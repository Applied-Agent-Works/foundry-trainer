#!/usr/bin/env python3
"""Run the constructed synthetic selector suite without a simulator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kaggriculture_eval.graph_registry import bind_registered_graphs  # noqa: E402
from kaggriculture_eval.shadow import evaluate_shadow_proposals, select_shadow_proposal  # noqa: E402
from kaggriculture_eval.shadow_suite import build_observation  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    args = parser.parse_args()
    scenarios: list[dict[str, Any]] = json.loads(args.fixture.read_text(encoding="utf-8"))
    bindings = bind_registered_graphs(args.target_root)
    records = []
    for scenario in scenarios:
        proposals = evaluate_shadow_proposals(build_observation(scenario), bindings)
        records.append({
            "scenario_id": scenario["id"],
            "selection": select_shadow_proposal(proposals),
            "proposals": [proposal.as_dict() for proposal in proposals],
        })
    report = {
        "schema_version": 1,
        "kind": "synthetic-shadow-selector-suite-v1",
        "fixture": str(args.fixture),
        "target_revision": next(iter(bindings.values())).revision,
        "simulator_used": False,
        "actions_applied": False,
        "scenario_count": len(records),
        "records": records,
    }
    destination = args.report_dir / "shadow-selector-suite-v1.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({
        "report_path": str(destination),
        "scenario_count": len(records),
        "simulator_used": False,
        "actions_applied": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
