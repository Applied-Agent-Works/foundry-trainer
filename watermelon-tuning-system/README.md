# Watermelon Tuner: first local pass

This directory is the first local evaluator for Kaggriculture's one-time
`MELON` decision graph. It is intentionally parallel to the Carrot Tuner, but
it does not copy Carrot's beliefs into the melon model. The source-controlled
Kaggriculture handoff remains the authority for melon facts and limitations:
[`melon-decision-network.md`](../../kaggriculture/tuning-handoffs/watermelon-tuning-system/source/melon-decision-network.md).

## What this first pass proves

The first pass is an end-to-end local proof, not a search system. It:

1. reads and validates one approved JSON experiment contract;
2. binds explicitly to the sibling Kaggriculture checkout and verifies its
   revision plus MELON policy and engine hashes;
3. runs a complete baseline for each fixed seed and seat and stores the
   pre-decision simulator state;
4. replays each declared candidate against baseline observations until its
   first action divergence;
5. reuses the exact baseline outcome when no action diverges, or restores the
   saved pre-divergence state and runs the remaining suffix;
6. independently reruns every candidate from a clean simulator and requires
   the fast result to match that audit; and
7. writes a provenance-rich local summary without changing Kaggriculture.

The approved first-pass parameter is `future_price_multiplier`, the explicit
point-estimate assumption used by the provisional one-time-crop policy. The
baseline is `1.0`. The candidate envelope intentionally contains both a
likely no-divergence change (`0.8`) and a deliberately low value (`0.05`) that
should cross the plant-versus-PASS threshold. A no-divergence candidate is a
valid result; it means the change did not cross a realized policy threshold.

## What is not being claimed

- `future_price_multiplier` is not a calibrated probability.
- The candidate values do not establish a global optimum.
- The small suite is not a competition score or a substitute for a larger
  held-out audit.
- The tuner does not edit the MELON source or create a Foundry resource.
- The copied/source snapshot is not automatically the simulator used by a
  run; the explicit target binding records the actual checkout and engine.

## Run the first pass

From this repository root, with the Kaggriculture virtual environment
available:

```bash
RUN_ID=20260924-next

../kaggriculture/.venv/bin/python scripts/run_watermelon_first_pass.py \
  --spec watermelon-tuning-system/experiments/approved/melon_investment/future_price_multiplier_smoke_v1.json \
  --target-root ../kaggriculture \
  --cache-root var/watermelon-tuning-system/runs/$RUN_ID/cache \
  --report-dir var/watermelon-tuning-system/runs/$RUN_ID/report
```

Choose a new unique `RUN_ID` for each reproduction; never point a new run at
an existing incompatible report directory.

The command is bounded by the contract. It can only use the declared
parameter, candidates, deterministic conveyor opponent, seeds, seats, and
720-step configuration. Existing valid baseline caches are reused; a report
with an existing filename is never overwritten.

The generated report is disposable and ignored. The contract, provenance
notes, runner, tests, and explanatory notebook are source-controlled.

The approved contract records exactly three target source hashes:
`agents/melon/shared.py`, `agents/one_time_crop.py`, and `kaggriculture.py`.
Those same three values are included in cache identity, baseline cache
payloads, cache validation, and the final report.

The recorded first proof is summarized in
[`first-pass-result.md`](./docs/first-pass-result.md); the ignored JSON report
contains the per-match details.

The latest re-pinned generated receipt path is
[`melon-future-price-multiplier-smoke-v1.json`](../var/watermelon-tuning-system/runs/20260926-repin-003649/report/melon-future-price-multiplier-smoke-v1.json).
It was reproduced against Kaggriculture revision
`3d8249e0de84002156500c6ee708d51925133169`; the older
`canonical-20260924` receipt remains historical.
Because `var/` is ignored, a fresh checkout does not contain this receipt
until the approved command generates it; no new reproduction is implied here.
Earlier `first-pass/`, `first-pass-v2/`, and `repair-pass-20260924/` receipts
are historical/superseded copies and must not be treated as the current audit
artifact.

## Source and policy seam

Kaggriculture's provisional MELON wrapper currently exposes
`melon_decision_agent(obs)` without a parameter argument. The explicit
`MELON_ADAPTER` therefore names the target's reusable one-time-crop helper and
parameter module as the candidate-injection seam, while retaining the
wrapper's stable policy identity for provenance. The crop-neutral binding has
no preferred crop and records hashes for both `agents/melon/shared.py` and
`agents/one_time_crop.py`.

## Trust boundary

The fast path is only an optimization. The clean rerun is the oracle. If a
checkpoint result and clean rerun disagree, the runner stops with a failed
audit and does not write a successful report. State restoration preserves the
simulator state and absolute step history needed by Kaggle's environment; it
does not continue using the stale observation stream after divergence.

## Next safe step

After the first-pass report is inspected, add a second deterministic opponent
or a held-out seed suite only as a new approved contract. Then add outcome
traces for melon sale-price assumptions. Do not introduce Foundry reasoning or
automated candidate generation until the local evidence packet shape and
human-review boundary are agreed.
