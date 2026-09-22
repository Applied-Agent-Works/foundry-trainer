# Memoization experiment — handoff copy

This is a copy of the Kaggriculture fixture included for the receiving Foundry
agent. Its original location is `../kaggriculture/memoization-experiment/`.
It still imports the Kaggriculture `agents` package, so it is reference material
until this project creates an explicit target-project binding.

This directory contains the disposable work on timing Kaggriculture matches,
recording decision traces, and eventually resuming a match from a cached game
state after a candidate policy first differs from its baseline.

It is intentionally outside the game, agent, and submission paths. Nothing
here is imported by `main.py` or selected as a live Kaggle policy.

## Contents

- `profile_step8.py` runs local timing samples and records or validates traces.
- `kaggriculture_playground.ipynb` is the experimental copy of the matched
  evaluation notebook.
- `results/` contains generated timing reports and charts (ignored by Git).
- `trace-cache/` contains generated compressed traces (ignored by Git).

The commands below describe the original Kaggriculture fixture. Do not run them
from this repository unchanged; first adapt the harness to the chosen target
binding and document that adaptation.

```bash
.venv/bin/python memoization-experiment/profile_step8.py \
  --opponent conveyor --seeds 42-44 --record-traces

.venv/bin/python memoization-experiment/profile_step8.py \
  --opponent conveyor --seeds 42-44 --replay-traces
```

The present trace replay is a validation cache: it proves that the current
policy matches the recorded actions, or reports its first different action.
It does not yet restore the simulator state and run only the remaining suffix.
That checkpoint/resume capability remains an experiment in this directory.

Open the notebook from the repository root as well, so its direct imports
resolve the local `agents` package.
