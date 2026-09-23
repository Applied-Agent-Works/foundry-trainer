# Current state and next implementation slice

## Why this snapshot exists

This page is the “where were we?” answer after the project moved from an
audited local evaluator toward a structured Carrot Tuning system. It records
the difference between evidence already earned, architecture now written down,
and code that still needs to be built. That distinction matters: a notebook can
make an architecture feel tangible, but it is not the same thing as a runner
that has reproduced the evidence.

Read the [continuity guide](../README.md) first for the full project intent,
then use this page to resume the immediate implementation sequence.

## What is already real and trusted

### 1. Local Kaggriculture evidence engine

The parent project already contains a real local checkpoint/resume evaluator.
It explicitly binds to the sibling Kaggriculture target, records the target
revision and hashes, stores a pre-decision checkpoint for every baseline turn,
replays candidate observations to first divergence, restores and simulates a
suffix when needed, and clean-audits each fast result with a full rerun.

The evaluator has already produced the following trusted evidence against the
deterministic conveyor opponent over seeds 42–71 in both seats (60 matches per
candidate):

- A ±10% one-parameter screen: all 22 directions were inert on this suite and
  all 1,320 clean audits passed.
- A decision-margin analysis: the carrot graph is threshold-based; the
  smallest observed plant-minus-pass margin was +9.72 and the median was
  +39.02.
- A coarse preference bracket: static `seed_opportunity_value` 10 was inert;
  40, 60, and 80 harmed mean reward by 52.37, 837.73, and 1623.28
  respectively; `pass_utility=25` also harmed reward. All 360 coarse-screen
  audits passed.

The conclusion remains narrow: retain the static carrot-only values 20 and 0
for this exact suite. This is not a global optimum claim and does not yet test
context-aware values supplied by other decision graphs.

### 2. The architecture notebook is an executable mock

[`01_system_model.ipynb`](../notebooks/01_system_model.ipynb) now provides a
walkthrough of the intended control flow:

- frozen dataclasses for a bounded `ExperimentSpec` and matched suite;
- a mocked inner-loop result populated from historical carrot evidence;
- a deterministic evals classification step;
- a mocked reasoning proposal for the next bounded question; and
- a sketch of how a later planner could supply a context-aware
  `seed_opportunity_value`.

It is deliberately explanatory. Its classes and frozen example values are not
the canonical runner contract, and cells that display JSON should be treated
as presentation or loaded from a file—not as a substitute for schema
validation. The canonical machine-readable record is the experiment JSON
described below.

The separate [local adapter workbench](../notebooks/02_local_inner_loop_adapter.ipynb)
starts the next phase. It imports and directly exercises the real adapter
framework while each implementation stage is reviewed. It is a guided testing
surface, not a notebook-only runner or an authorization to run Kaggriculture.

### 3. Step 9.1 is complete as a design and source-control artifact

The notebook's step 9.1 called for one versioned, bounded experiment
specification. That contract now exists:

- [schema v1](../experiments/schema/experiment-spec-v1.schema.json) defines
  the allowed shape of one bounded local experiment;
- [historical coarse seed-opportunity spec](../experiments/historical/carrot_investment/seed_opportunity_coarse_v1.json)
  records the completed bracket, exact target fingerprint, suite, audit rules,
  governance restrictions, and expected aggregate classifications;
- [historical narrative](../experiments/historical/carrot_investment/seed_opportunity_coarse_v1.md)
  reconstructs why the result is credible; and
- [historical notebook](../experiments/historical/carrot_investment/seed_opportunity_coarse_v1.ipynb)
  reads the adjacent JSON and explains the record without rerunning a game.

The schema and historical record were validated with a JSON Schema
Draft 2020-12 validator. The historical expectations were checked against the
already-recorded coarse result.

This means the project has a real source-controlled contract and a credible
reproduction oracle. It does **not** mean the new Carrot Tuning directory yet
contains an implementation that parses this JSON and calls the evaluator.

### 4. Visual architecture is now documented

The [architecture diagrams](./architecture-diagrams.md) show the two-loop
context, inner-loop sequence, outer-loop interaction, conceptual entity
relationships, future multi-graph interaction, and experiment lifecycle. Use
them to regain orientation before editing evaluator, schema, or Foundry-facing
components.

## What is deliberately not built yet

- The [evaluator/](../evaluator/) directory is an intentionally inert framework only. Its
  `run()` entry point documents the reviewed sequence and raises
  `NotImplementedError`; it does not read a spec, bind a target, run a game,
  write a report, or mutate source.
- No pytest dependency is being introduced for this initial framework stage.
  The adapter workbench directly verifies the fail-closed entry point; reusable
  test-suite coverage follows after the first real adapter behavior exists.
- No real `ExperimentSpec` parser or validator is wired into a runner.
- No runner in `carrot-tuning-system/` invokes the parent checkpoint evaluator.
- No generic evidence-packet writer exists yet; the notebook's packet is a
  mock and the historical JSON is an archival record.
- No deterministic evals module exists yet; its notebook logic is illustrative.
- No Foundry agent, Azure resource, credential, connector, cloud storage, or
  model call has been created or used for this new project.
- No multi-graph action selector or contextual opportunity-value implementation
  exists. `seed_opportunity_value=20` is still only a static carrot parameter
  in the target policy.

These absences are intentional. Building the real local inner loop first is
the safeguard that keeps future Foundry reasoning grounded in verified game
evidence.

## The next narrow implementation slice

The next task is not “build Foundry” and not “search for a better carrot
value.” It is to replace one mock safely.

```text
historical experiment JSON
          ↓
validate schema + target fingerprint + local controls
          ↓
load/create matching baseline cache
          ↓
call proven checkpoint evaluator for exactly listed candidates
          ↓
require every clean audit to pass
          ↓
write a real EvidencePacket JSON
          ↓
compare classifications with historical expectations
```

### Acceptance criteria for that slice

The first runner is ready to move on only when it can:

1. Read the historical specification rather than hard-code the bracket.
2. Reject a malformed schema, unknown parameter, changed target hash, missing
   suite control, duplicate candidate, or unauthorized lifecycle status before
   running a simulator.
3. Use the explicit sibling-target binding and existing checkpoint evaluator;
   it must not import a generic `agents` package or edit Kaggriculture source.
4. Produce a durable local evidence packet with provenance, per-match results,
   aggregate paired outcomes, divergence/suffix facts, timing components, and
   clean-audit status.
5. Reproduce the historical classifications: 10 inert; 40/60/80 directional
   harm; all required audits passed.
6. Stop and report a mismatch rather than explain it away or choose a new
   candidate value.

### Human decision after the slice

After this reproduction smoke test succeeds, the human decides whether to
accept the local spec-driven inner loop as the stable foundation. Only then is
the next bounded feature appropriate: a carrot graph-adapter contract for
eligibility, explanation, utility margin, and scenario coverage. Foundry-facing
reasoning remains later, behind the same evidence-packet boundary.

## How to resume after an interruption

1. Read the [continuity guide](../README.md) and this snapshot.
2. Look at the [architecture diagrams](./architecture-diagrams.md), especially
   the system context and inner-loop sequence.
3. Open the [historical narrative](../experiments/historical/carrot_investment/seed_opportunity_coarse_v1.md)
   or its notebook to remember what the first reproduction must match.
4. Read the [schema v1](../experiments/schema/experiment-spec-v1.schema.json)
   before designing a parser or runner API.
5. Keep generated output under ignored `var/`; do not copy disposable caches or
   result reports into the source-controlled contract directory.
6. If a proposed change would add a candidate value, change the opponent/suite,
   modify target policy, or use Foundry/Azure, stop and obtain the appropriate
   human approval first.

## Repository housekeeping note

The prior implementation and documentation foundation were merged into `main`.
The temporary agent branches and secondary worktree were removed after
verification that they had no unique unmerged commits. This is operational
cleanup, not experimental evidence; the authoritative project history remains
the Git log and the source-controlled historical records.
