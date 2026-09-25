# Wheat Tuner: first local pass

This directory is the Wheat counterpart to the Carrot Tuner. It evaluates the
standalone Kaggriculture wheat crop graph; it does not tune wheat as animal
feed, choose among all crops, or alter Kaggriculture source.

The first pass:

1. validates one approved JSON contract;
2. binds explicitly to `agents/wheat/shared.py` in the sibling checkout;
3. checkpoints the baseline before every decision;
4. replays each declared candidate until its first action divergence;
5. reuses the exact baseline outcome when there is no divergence, otherwise
   restores the pre-divergence simulator state and runs the suffix;
6. independently clean-reruns every candidate and requires matching outcomes;
7. writes an immutable, provenance-rich local summary.

The contract tests the provisional `future_price_multiplier` parameter at
`0.05`, `0.8`, and `1.2` against the deterministic wheat conveyor over seeds
42 and 43 in both seats. The point estimate is not a calibrated probability
model; this pass only tests whether the explicit policy threshold is sensitive
to the declared values.

Run it from the repository root:

```bash
../kaggriculture/.venv/bin/python scripts/run_wheat_first_pass.py \
  --spec wheat-tuning-system/experiments/approved/wheat_crop/future_price_multiplier_smoke_v1.json \
  --target-root ../kaggriculture \
  --cache-root var/wheat-tuning-system/repair-first-pass-cache \
  --report-dir var/wheat-tuning-system/repair-first-pass
```

The report and baseline caches are disposable under ignored `var/`. Existing
valid reports are never overwritten. Any mismatch between a cached result and
its clean audit stops the run.

The completed smoke result is summarized in
[docs/first-pass-result.md](./docs/first-pass-result.md); the current boundary
and next decision are in
[docs/current-state-and-next-slice.md](./docs/current-state-and-next-slice.md).
The pinned checkout and dirty-source warning are recorded in
[docs/source-provenance.md](./docs/source-provenance.md).

## Known limits

The target wheat files are currently uncommitted in the sibling checkout, so
the first report must be treated as tied to the recorded source hashes and
working-tree state. The wrapper exposes `wheat_decision_agent(obs)` without a
parameter argument; the reviewed `WHEAT_ADAPTER` explicitly binds
`agents/one_time_crop.py`, its `PointPriceParameters`, and the bound `WHEAT`
facts for in-memory candidate injection. No target-policy edit is needed.

The crop-only graph also excludes animal-feed value, multi-tile scheduling,
fertilizer, market buying, and calibrated future-price distributions.
