# Local shadow integration for the one-time crop graphs

This slice prepares Carrot, Wheat, Watermelon/MELON, Tomato, and Strawberry to
be inspected together without changing the action applied to a Kaggriculture
simulator.
It does not modify Kaggriculture policy source and does not change the Foundry
packet or Foundry invocation path.

## Registry

[`graph_registry.py`](../../src/kaggriculture_eval/graph_registry.py) is a
descriptive catalogue of the three standalone graphs. Each entry names its
crop, lifecycle, parameter namespace, adapter, supported local stages, and
known limitations. The registry is not a crop selector and does not merge
parameters between graphs.

[`bind_registered_graphs`](../../src/kaggriculture_eval/graph_registry.py) binds
each entry to the same explicitly supplied Kaggriculture checkout. Binding
loads policy code and records provenance; it does not run a simulator.

## Shadow proposals

[`shadow.py`](../../src/kaggriculture_eval/shadow.py) evaluates each bound graph
against one observation and returns a `ShadowProposal` for each graph. A
proposal contains:

- the graph and crop identity;
- the complete action dictionary the graph would return;
- a coarse local label such as `plant`, `care-or-move`, or `pass`;
- the in-memory parameter values and any candidate override;
- the observation hash and target source provenance; and
- the graph's current limitations.

The function never steps a simulator, selects a winner, or applies one of the
actions. It is therefore safe to use in shadow mode while the existing policy
remains authoritative.

## Boundary

The current graph set contains three one-time-crop graphs and two ongoing-crop
graphs. They remain independent and keep their lifecycle-specific limitations.
A future crop-selection network may compare their proposals after care
feasibility, land, seed, labor, time, and market context are represented. That
selector is deliberately not part of this slice.

The local proposal shape is an integration diagnostic. It is not yet a Foundry
evidence packet and must not be sent to the Foundry analyst until its cross-
graph semantics and review boundary are explicitly approved.

## Re-pinned smoke evidence

The five approved crop envelopes were re-pinned to Kaggriculture revision
`3d8249e0de84002156500c6ee708d51925133169` and rerun on 2026-09-26. All five
completed with clean audits. The fresh ignored receipts are:

- `var/ui-runs/20260926-repin-003649/report/evidence-packets/carrot-seed-opportunity-candidate-evidence-smoke-v1.json`
- `var/wheat-tuning-system/runs/20260926-repin-003649/report/wheat-future-price-multiplier-smoke-v1.json`
- `var/watermelon-tuning-system/runs/20260926-repin-003649/report/melon-future-price-multiplier-smoke-v1.json`
- `var/tomato-tuning-system/runs/20260926-ongoing-004808/report/tomato-future-price-multiplier-smoke-v1.json`
- `var/strawberry-tuning-system/runs/20260926-ongoing-004808/report/strawberry-future-price-multiplier-smoke-v1.json`

These are still independent graph receipts. The shadow seam can now trace all
five proposals over shared observations without stepping the simulator.

The executed tracer is [`run_shadow_trace.py`](../../scripts/run_shadow_trace.py).
The first full trace used both seed-42 Carrot baseline-cache observation
streams (719 turns per seat), producing 1,438 shared observations and 1,320
coarse action-class disagreements across the five graphs. After adding
decision-phase and investment-window fields, the current report is
`var/shadow-traces/20260926-eligible/shadow-trace-v1.json`. It records the
graph-specific season and resource blocks explicitly. On this Carrot baseline
observation stream, there were no disagreements between graphs that were
simultaneously eligible for investment; that is a useful result, not a failure
of the tracer. A different shared observation suite is needed to exercise
actual crop-choice conflicts.

The synthetic diagnostic fixture
[`shadow_multi_eligible_v1.json`](../../tests/fixtures/shadow_multi_eligible_v1.json)
provides that second suite: all five graphs are eligible on an empty tile,
with different price scenarios. It produced three observations and two
genuine investment disagreements in
`var/shadow-traces/20260926-multi-eligible/shadow-trace-v1.json`. This is
deliberately diagnostic input, not simulator evidence.

## Shadow selector

[`select_shadow_proposal`](../../src/kaggriculture_eval/shadow.py) now compares
graph-specific utility margins for eligible planting proposals. It chooses the
highest positive margin with a stable graph-ID tie-break, or returns `PASS`
when none is positive. It only returns a selection record; it does not apply
the selected action.

On the synthetic fixture it selected MELON, STRAWBERRY, and MELON for the
three price scenarios. The largest observed utility margins were 1,420, 380,
and 1,420. These are policy-model values from the diagnostic fixture, not
simulator outcomes or a production recommendation.

The broader 12-scenario selector suite is defined in
[`shadow_selector_suite_v1.json`](../../tests/fixtures/shadow_selector_suite_v1.json)
and was executed by [`run_shadow_selector_suite.py`](../../scripts/run_shadow_selector_suite.py).
Its report is
`var/shadow-traces/20260926-selector-suite-v2/shadow-selector-suite-v1.json`.
It covered favorable, suppressed, single-crop, all-unattractive, late-season,
no-space, no-resource, and mid-season cases. The selector chose a crop in the
positive cases and returned `PASS` in the blocked or all-unattractive cases.

The approved held-out observation run used seeds 43, 44, and 45, both seats,
720 steps, and the deterministic Carrot conveyor. Its report is
`var/shadow-traces/20260926-heldout/heldout-shadow-trace-v1.json` and contains
4,314 simulator-captured observations. The selector returned MELON 2,880
times, WHEAT 864 times, and `PASS` 570 times. No observation contained a
simultaneous eligible-graph action conflict, and the selector applied no
actions. The current simulator regime therefore still does not exercise the
full crop-arbitration problem; the synthetic suite remains the deliberate
selector-conflict test.
