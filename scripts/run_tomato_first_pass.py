#!/usr/bin/env python3
"""Run the approved, bounded local Tomato Tuner first pass."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tomato-tuning-system"))

from tomato_tuner.runner import read_and_validate_spec, run_first_pass  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the approved local Tomato Tuner first pass.")
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = run_first_pass(
        read_and_validate_spec(args.spec),
        target_root=args.target_root,
        cache_root=args.cache_root,
        report_dir=args.report_dir,
    )
    print(f"Tomato first pass complete: {summary['report_path']}")
    print(f"Baseline mean reward: {summary['baseline']['mean_decision_reward']:.2f}")
    for aggregate in summary["aggregates"]:
        print(
            f"candidate={aggregate['candidate_value']:.2f} "
            f"reward={aggregate['mean_candidate_decision_reward']:.2f} "
            f"delta={aggregate['mean_paired_decision_delta']:.2f} "
            f"divergences={aggregate['divergent_match_count']}/{aggregate['match_count']} "
            f"suffix_actions={aggregate['total_suffix_actions']} "
            f"audits={aggregate['all_audits_passed']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
