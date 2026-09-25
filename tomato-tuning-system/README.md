# Tomato Tuner scaffold

This directory defines a bounded local tuner for Kaggriculture's ongoing
`TOMATO` graph. The original draft contract remains fail-closed; the approved
copy records the human decision to run one bounded first pass.

The scaffold fixes one provisional parameter, `future_price_multiplier`, a
deterministic Tomato conveyor opponent, seeds 42 and 43, both player seats,
720 turns, checkpoint/resume, and independent clean audits. The point-price
multiplier is a transparent policy assumption, not a calibrated probability.

The tests in `tests/test_ongoing_crop_tuner_scaffolds.py` verify explicit
binding, complete provenance, crop-specific opponent behavior, in-memory
parameter injection, fail-closed draft controls, and restored-suffix versus
clean-run agreement. The simulator checks are marked `simulator` and remain
outside the default fast suite.

Run the approved first pass from the repository root with a disposable output
directory:

```bash
../kaggriculture/.venv/bin/python scripts/run_tomato_first_pass.py \
  --spec tomato-tuning-system/experiments/approved/tomato_crop/future_price_multiplier_smoke_v1.json \
  --target-root ../kaggriculture \
  --cache-root var/tomato-tuning-system/first-pass-20260925/cache \
  --report-dir var/tomato-tuning-system/first-pass-20260925/report
```

The canonical local receipt from the approved run is
`var/tomato-tuning-system/first-pass-20260925/report/`.
The run does not mutate Kaggriculture or automatically promote a candidate;
human review is still required before changing any policy baseline.
