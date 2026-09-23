"""Deliberately incomplete orchestration boundary for local experiments.

The existing ``kaggriculture_eval`` package remains the proven simulation
engine. This module will eventually validate a declared experiment and call
those primitives; it must never become a second simulator or policy editor.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LocalRunRequest:
    """Locations supplied to the future local runner, not evaluator results."""

    # The source-controlled JSON contract the future runner must read.
    spec_path: Path
    # An explicit sibling checkout prevents ambiguous imports of ``agents``.
    target_root: Path
    # Generated evidence belongs in an ignored local directory, never in the spec.
    report_directory: Path


class LocalInnerLoopAdapter:
    """Coordinate a bounded local experiment after its implementation is reviewed.

    This skeleton intentionally does not load a spec, bind a target, run a
    baseline, call the checkpoint evaluator, write a report, or alter source.
    """

    def run(self, request: LocalRunRequest) -> None:
        """Run one approved experiment once the steps below are implemented.

        Implementation sequence:

        1. Read the JSON specification at ``request.spec_path``.
        2. Validate it against schema v1 and reject unauthorized lifecycle states.
        3. Bind explicitly to ``request.target_root`` and compare revision/hashes.
        4. Validate the declared parameter, suite, and one-field candidate envelope.
        5. Load or create an immutable baseline cache for every seed/seat match.
        6. Call the proven checkpoint evaluator for exactly the declared values.
        7. Require a clean full-run audit for every fast result; fail closed on a mismatch.
        8. Write one local ignored evidence packet under ``request.report_directory``.
        9. Compare a historical reproduction with its recorded expectations.

        Each step needs its own tests and review. Do not skip directly to a
        simulator call, unbounded candidate generation, or a policy source edit.
        """
        del request  # The framework deliberately has no side effects yet.
        raise NotImplementedError(
            "The local inner-loop adapter is scaffolded only; implement and review "
            "the spec-validation stage before it can run an experiment."
        )
