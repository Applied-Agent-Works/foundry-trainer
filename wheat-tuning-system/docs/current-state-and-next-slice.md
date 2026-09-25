# Wheat Tuner current state and next slice

## Complete

The first local Wheat Tuner vertical slice is complete:

- explicit wheat target binding and provenance checks;
- source-controlled approved contract;
- four baseline caches over seeds 42/43 and seats 0/1;
- checkpoint before every decision;
- replay to first divergence;
- exact baseline reuse for no divergence;
- restored suffix for divergence;
- clean full-run audit for every candidate match; and
- immutable, provenance-rich local JSON summary.

The detailed result is in [first-pass-result.md](./first-pass-result.md).

## Remaining limitations

The target wheat wrapper accepts only an observation. The reviewed
`WHEAT_ADAPTER` is the explicit evaluator seam: it binds the target's
`one_time_crop.py` helper, `PointPriceParameters`, and `WHEAT` facts for
in-memory candidate injection. This keeps the Kaggriculture wrapper unchanged
and keeps the evaluator crop-neutral.

The provisional `future_price_multiplier` is a point-estimate assumption, not
a calibrated probability distribution. The first pass also excludes feed,
fertilizer, multi-tile care, market buying, and crop selection.

The sibling Kaggriculture wheat files are uncommitted. The first pass is
therefore tied to the complete recorded source-hash set and should not be
treated as a clean-release benchmark until that target is frozen.

## Next gate

A human should choose a new bounded contract for a held-out seed suite,
threshold refinement, or price calibration. Do not expand candidates,
automatically edit policy source, or add Foundry reasoning from this result.
