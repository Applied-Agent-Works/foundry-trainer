# Experiment specifications

This directory contains source-controlled experiment contracts. It does not
contain generated caches, raw traces, or result reports; those stay disposable
under the parent project's ignored `var/` directory.

## Directory roles

```text
experiments/
  schema/       Versioned machine-validation contracts.
  historical/   Immutable descriptions of experiments already completed.
  drafts/       Proposed experiments that are still being refined.
  approved/     Human-approved future runs that the inner-loop runner may execute.
```

`historical/` is deliberately separate. A historical reproduction spec records
what actually happened and can become a smoke-test oracle for a new runner. It
is not automatically eligible for execution merely because it exists.

An `approved/` spec is a bounded execution authorization: the runner may test
only its declared candidates, suite, and controls. It may not expand a bracket
after seeing a result. A completed spec is never edited in place; a changed
question gets a new versioned file.

## First artifact

[`historical/carrot_investment/seed_opportunity_coarse_v1.json`](./historical/carrot_investment/seed_opportunity_coarse_v1.json)
records the already-completed static seed-opportunity bracket. Its expected
classifications and aggregate outcomes are regression expectations for the
first real inner-loop runner—not fresh evidence by themselves.

Its [narrative reconstruction](./historical/carrot_investment/seed_opportunity_coarse_v1.md)
and [historical notebook](./historical/carrot_investment/seed_opportunity_coarse_v1.ipynb)
are human-facing companions. They load or explain the canonical JSON; neither
is an execution authority.

The contract for this first schema version is
[`schema/experiment-spec-v1.schema.json`](./schema/experiment-spec-v1.schema.json).

## Approved smallest-matched smoke test

[`approved/carrot_investment/seed_opportunity_baseline_smoke_v1.json`](./approved/carrot_investment/seed_opportunity_baseline_smoke_v1.json)
is a separate, human-approved infrastructure envelope. It pins the historical
target and baseline parameter controls, but bounds cache creation to seed 42 in
both seats at 720 steps. Both seats are required to retain the runner's
matched-suite invariant; the materializer nevertheless processes one selected
cache entry at a time. It is not a candidate evaluation, an aggregate evidence
claim, or an authorization to edit Kaggriculture policy source.

The contract passed every pre-simulation adapter gate. The sibling simulator
checkout is installed editable into the local virtual environment, without
changing either source checkout. Its first action, seed 42 / seat 0, has run
once and produced an ignored local cache. The runner reopened that cache and
passed every structural/provenance check. The matching seat-1 baseline has now
also run and passed the same reopen checks. Both caches are reusable only for
this exact target and smoke contract. During separately reviewed notebook work,
the declared candidate values were evaluated against these caches and all eight
fast/clean-audit pairs passed; those are one-seed smoke facts only, not a policy
recommendation. Crucially, this contract's purpose still says it does **not**
authorize candidate evaluation. A reusable end-to-end runner must use a new,
separately approved candidate-evidence contract rather than treating prior
interactive approvals as durable execution authority. No policy-source change
has occurred.

## Approved candidate-evidence smoke test

[`approved/carrot_investment/seed_opportunity_candidate_evidence_smoke_v1.json`](./approved/carrot_investment/seed_opportunity_candidate_evidence_smoke_v1.json)
is the human-approved successor contract. It preserves the exact pinned target,
seed-42/two-seat/720-step suite, and already-declared 10/40/60/80 candidate
envelope. Its stated purpose is candidate evaluation with a required
clean audit for every match and one immutable local evidence packet only after
all audits pass.

This exact envelope is now authorized for bounded local candidate evaluation.
It still does not authorize source-policy mutation, candidate expansion,
interpretation as a ranking, or replacement for the historical 60-match
evidence. The next implementation artifact is the separate end-to-end notebook
that wires this approved contract through `run()`; no execution has occurred
at promotion time.

For the conceptual entity relationships and experiment lifecycle that this
directory implements, see [architecture diagrams](../docs/architecture-diagrams.md).
