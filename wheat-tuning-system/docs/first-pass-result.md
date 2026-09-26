# Wheat Tuner first-pass result

## Result: ✅ complete and audited

The approved first-pass contract ran locally against Kaggriculture revision
`6ace5fed9018fef45642b41ea11d0bd741a508a4` with the deterministic wheat
conveyor opponent. It used seeds 42 and 43, both seats, and 720 steps. The
candidate parameter was `future_price_multiplier`, with baseline `1.0` and
declared values `0.05`, `0.8`, and `1.2`.

The generated JSON report is disposable but authoritative for this
run's recorded facts:
[`wheat-future-price-multiplier-smoke-v1.json`](../../var/wheat-tuning-system/canonical-20260924/report/wheat-future-price-multiplier-smoke-v1.json).
The path is ignored run output; it is not bundled in a fresh checkout.

| Candidate | Mean reward | Paired delta | Divergences | Suffix actions | Audits |
|---:|---:|---:|---:|---:|---|
| baseline `1.0` | 4019.50 | — | — | — | reference |
| `0.05` | 3000.00 | -1019.50 | 4 / 4 | 2876 | 4 / 4 passed |
| `0.8` | 4019.50 | 0.00 | 0 / 4 | 0 | 4 / 4 passed |
| `1.2` | 4019.50 | 0.00 | 0 / 4 | 0 | 4 / 4 passed |

The `0.05` candidate diverged at turn 0 in all four matches and ran a full
719-action restored suffix each time. The `0.8` and `1.2` candidates followed
the baseline action path in all four matches, so the exact baseline outcome was
reused. Every fast result matched an independent clean full rerun.

## Integration issue found and fixed

The Watermelon first pass exposed that the shared checkpoint engine could bind
one crop but still call `carrot_decision_agent` during a later clean rerun. The
shared core now routes baseline, replay, restored suffix, and clean-audit calls
through the explicitly bound crop adapter. Wheat uses that same corrected path;
the passing restored-suffix audits below are the direct regression evidence.

The simulator-marked Wheat regression also exercises a divergent candidate and
requires its clean rerun to match. This prevents a future refactor from fixing
only the fast path while silently returning to carrot-specific calls in the
audit path.

## What this supports

For this exact revision, deterministic opponent, two-seed/two-seat suite, and
720-step configuration:

- the wheat policy is sensitive to a sufficiently low future-price multiplier;
- the selected high-side change from `1.0` to `1.2` did not cross a realized
  plant/pass threshold;
- the selected low-side change from `1.0` to `0.8` also did not cross a
  realized threshold; and
- the checkpoint/replay/restored-suffix implementation agrees with clean
  simulation for all 12 candidate matches.

This does **not** establish that `1.0` is calibrated, globally optimal, or
robust to other opponents, market regimes, or held-out seeds. It also does not
evaluate wheat's later animal-feed opportunity value.

## Provenance and safety

The report records the explicit target root, revision, complete source-hash
set (wheat shared policy, `one_time_crop.py`, and engine), opponent, seeds,
seats, old/new values, divergence turns, suffix lengths, outcomes, timings,
and audit status. The reviewed `WHEAT_ADAPTER` is the policy seam: it injects
parameters through the explicitly bound helper and `WHEAT` facts without
modifying the Kaggriculture wrapper. Caches and the report remain under
ignored `var/wheat-tuning-system/`.

⚠️ The wheat policy files in the sibling Kaggriculture checkout were already
uncommitted draft files when this run began. The report's shared-policy hash
therefore matters: future reruns must bind to the same hash or fail closed.
Earlier `first-pass/` and `repair-first-pass/` receipts are
historical/superseded copies; the current generated receipt path is the one above.

## Next safe experiment

The next useful step is not automatic search. Choose one of:

1. repeat this contract on a larger held-out seed suite;
2. test a deliberately selected intermediate multiplier around the realized
   threshold; or
3. design a separate calibration record for predicted versus realized wheat
   sale-price regimes.

Each choice requires a new contract. Keep animal-feed value and multi-crop
selection outside this crop-only first pass.

## Latest re-pinned reproduction

On 2026-09-26 the same approved envelope was rerun against the current
Kaggriculture revision `3d8249e0de84002156500c6ee708d51925133169`, without
changing its candidates, controls, or policy source. The fresh receipt is
[`wheat-future-price-multiplier-smoke-v1.json`](../../var/wheat-tuning-system/runs/20260926-repin-003649/report/wheat-future-price-multiplier-smoke-v1.json).
All four candidate/seat matches passed their clean audits and the aggregate
results were identical to the historical receipt. The 2026-09-24 receipt is
retained as historical evidence.
