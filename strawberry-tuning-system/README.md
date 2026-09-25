# Strawberry Tuner scaffold

This directory defines a bounded local tuner for Kaggriculture's ongoing
`STRAWBERRY` graph. The approved contract is a first-pass proof, not a search
system or a policy-promotion decision.

The scaffold fixes one provisional parameter, `future_price_multiplier`, a
deterministic Strawberry conveyor opponent, seeds 42 and 43, both player seats,
720 turns, checkpoint/resume, and independent clean audits. The point-price
multiplier is a transparent policy assumption, not a calibrated probability.

The tests in `tests/test_ongoing_crop_tuner_scaffolds.py` verify explicit
binding, complete provenance, crop-specific opponent behavior, in-memory
parameter injection, fail-closed contract controls, and restored-suffix versus
clean-run agreement. The simulator checks are marked `simulator` and remain
outside the default fast suite.

## Run the approved first pass

Use a fresh ignored run directory for each reproduction:

```bash
RUN_ID=20260925-strawberry

../kaggriculture/.venv/bin/python scripts/run_strawberry_first_pass.py \
  --spec strawberry-tuning-system/experiments/approved/strawberry_crop/future_price_multiplier_smoke_v1.json \
  --target-root ../kaggriculture \
  --cache-root var/strawberry-tuning-system/runs/$RUN_ID/cache \
  --report-dir var/strawberry-tuning-system/runs/$RUN_ID/report
```

The generated report and baseline caches are disposable and ignored under
`var/strawberry-tuning-system/`. The runner refuses to overwrite a different
report at the same path and validates the target revision plus all three
source hashes before using a cache.

The canonical local receipt from the reviewed run is
`var/strawberry-tuning-system/runs/20260925-strawberry-v3/report/strawberry-future-price-multiplier-smoke-v1.json`.
The earlier `20260925-strawberry-v2` receipt is historical and superseded.

The original draft contract remains fail-closed for historical comparison at
`experiments/draft/strawberry_crop/future_price_multiplier_smoke_v1.json`.

This first pass does not establish an optimum. A later human review is still
required before expanding the seed suite, changing candidates, or adding
another opponent.
