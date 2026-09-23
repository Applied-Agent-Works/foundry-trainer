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

For the conceptual entity relationships and experiment lifecycle that this
directory implements, see [architecture diagrams](../docs/architecture-diagrams.md).
