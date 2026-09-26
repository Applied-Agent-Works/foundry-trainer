# Current state and next slice

## What is complete

The Watermelon Tuner now has a first local implementation with:

- explicit MELON target binding;
- an approved single-parameter experiment contract;
- full baseline checkpoint materialization;
- replay-until-first-divergence;
- exact baseline reuse for no divergence;
- restored-suffix simulation after divergence;
- independent clean candidate audits; and
- an immutable, provenance-rich JSON summary writer.

The reviewed `MELON_ADAPTER` is the only Watermelon binding seam. The exact
three-file target hash set is enforced in the contract, cache identity,
baseline payload, cache validation, and report.

The first pass is intentionally smaller than the full Carrot system. It proves
the core mechanical invariant before adding evidence-analyst or Foundry work.
The observed outcome is preserved in the
[first-pass result](./first-pass-result.md).

The latest re-pinned generated receipt path is
[`melon-future-price-multiplier-smoke-v1.json`](../../var/watermelon-tuning-system/runs/20260926-repin-003649/report/melon-future-price-multiplier-smoke-v1.json),
against Kaggriculture revision `3d8249e0de84002156500c6ee708d51925133169`.
It is ignored run output and is absent from a fresh checkout until the
approved command generates it.
Earlier generated receipts are historical/superseded and remain disposable.

## Controls held constant

The first contract fixes target revision and hashes, the deterministic MELON
conveyor opponent, seeds 42 and 43, both player seats, 720 turns, and one
in-memory `future_price_multiplier` override at a time. No target source is
modified. Caches and reports are disposable under `var/`.

## Remaining first-pass limitations

1. The public MELON decision wrapper accepts only an observation. The reviewed
   `MELON_ADAPTER` explicitly names the target's one-time-crop helper and
   parameter module; this is the accepted adapter seam, not an ambient import
   or policy edit.
2. The first pass uses the point estimate described by the handoff. It does
   not yet record a probability distribution, resolved sale-price labels, or
   calibration metrics.
3. The default policy's lifecycle limitations remain: one active crop, no
   generalized multi-tile scheduling, no fertilizer strategy, no last-day
   delivery guard, and no dynamic future market simulation in the policy.
4. The first suite is an infrastructure smoke envelope, not enough evidence
   for a policy promotion decision.

## Acceptance criteria for this slice

- the contract validates;
- target revision and all recorded hashes match;
- every baseline match has a non-empty pre-decision checkpoint trace;
- every candidate has either `reused-baseline` or `restored-suffix` mode;
- every cached result exactly matches its clean rerun;
- the report records divergence, suffix, outcome, and audit facts; and
- no Kaggriculture source file changes.

## Next human-owned decision

Review the first report, then approve a second contract with a larger held-out
seed suite and a deliberately late-divergence case. Do not silently change the
target policy from this tuner.
