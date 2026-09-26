# Tomato Tuner current state and next slice

## Complete

The approved first pass is complete for its narrow local scope:

- explicit `TOMATO_ADAPTER` target binding;
- revision and three-file source-hash verification;
- seeds 42 and 43 in both seats at 720 steps;
- checkpoint-before-every-decision baseline caches;
- first-divergence replay and restored suffix;
- independent clean audits; and
- immutable local receipt under the ignored `var/` tree.

The latest re-pinned reviewed receipt is under
`var/tomato-tuning-system/runs/20260926-ongoing-004808/report/` and records
Kaggriculture revision `3d8249e0de84002156500c6ee708d51925133169`.

## Observed first-pass facts

The baseline mean reward was `3438.50`. Candidate `0.05` diverged in all four
matches and produced a paired delta of `-438.50`; candidates `0.8` and `1.2`
were inert with paired delta `0.00`. All twelve candidate-match audits passed.

These are mechanical smoke facts, not a calibrated probability result, global
optimum, or policy-promotion recommendation.

## Next human-owned decision

Choose a larger held-out suite, a deliberately selected intermediate value, or
a separate realized-price calibration record. Do not expand candidates,
change source policy, or add Foundry work from this first pass automatically.
