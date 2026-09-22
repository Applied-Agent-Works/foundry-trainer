# Target binding and provenance

The evaluator binds only to `/home/experiments/frontier-week/kaggriculture`
unless `KAGGRICULTURE_TARGET_ROOT` explicitly supplies another absolute target
directory.  The binding validates that directory and loads
`agents/carrot/shared.py` by an evaluator-owned, content-addressed module name.
It never imports a generic `agents` module and never depends on the current
working directory.

The target remains the system under test.  This project neither imports nor
changes its submission entry point, game policy source, game rules, or agent
architecture.  The binding records the target Git revision when available and
SHA-256 hashes for the loaded shared policy source and game module.

Material adapted for this evaluator originated in the handoff copy
`HANDOFF/memoization-experiment/profile_step8.py`, whose source provenance is
`../kaggriculture/memoization-experiment/profile_step8.py` at target revision
`6ace5fed9018fef45642b41ea11d0bd741a508a4` when this project was initialized.
That fixture provided trace capture/replay only; this evaluator adds explicit
JSON-safe simulator checkpoints and restoration.  The fixture itself remains
unaltered under `HANDOFF/`.

Checkpoint files contain the complete Kaggle environment state immediately
before the evaluated player's action.  They are restored into a newly-created
environment with the same configuration and episode seed.  Kaggriculture's
engine derives end-of-day randomness from the persisted episode seed and day,
so no mutable RNG state is omitted.  A restored environment receives the same
future action sequence as a clean run.

