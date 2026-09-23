# Historical reproduction: coarse seed-opportunity bracket v1

## What question did this answer?

For the current carrot-investment decision graph, does changing the static
value assigned to preserving an already-owned carrot seed improve or harm
whole-season reward against the deterministic carrot conveyor opponent?

This is a historical record of a completed local experiment. Its canonical
machine-readable contract and aggregate regression expectations are in
[`seed_opportunity_coarse_v1.json`](./seed_opportunity_coarse_v1.json). The
companion [notebook](./seed_opportunity_coarse_v1.ipynb) provides a readable,
executable walkthrough of those recorded facts.

## Why this parameter mattered

The carrot graph reduces its economic choice to plant/invest now or preserve
the option. `seed_opportunity_value` is the graph's static shadow price for
retaining a seed for a later opportunity. The experiment therefore tested a
meaningful decision threshold, not a game-rule constant.

It does **not** prove that 20 is globally optimal. It supports a narrower
statement: for this exact target revision, opponent, seed/seat suite, and
static values, raising this preference above 20 harmed mean reward.

## Controls held constant

- Kaggriculture target revision and policy/engine hashes recorded in the JSON
  specification.
- Deterministic `carrot_conveyor_agent` opponent.
- Seeds 42–71, both player seats, 720 turns: 60 matched games per candidate.
- One in-memory `seed_opportunity_value` override at a time.
- No Kaggriculture source-policy, game-rule, entry-point, or architecture edit.

## Why the evidence is credible

Each candidate first replayed baseline observations. If it chose exactly the
same action at every decision, it reused the baseline outcome. At the first
different action, the evaluator restored the saved simulator state immediately
before that action and simulated the remaining suffix. Every cached result was
then compared against a clean full candidate rerun using the identical seed,
seat, opponent, and configuration.

All 360 candidate-match clean audits passed. The full generated report remains
disposable under the ignored parent `var/` directory; the JSON spec preserves
the contract and aggregate expectations needed for a future runner to
reproduce this test.

## Recorded outcome

| Candidate value | Mean reward | Mean paired delta | Classification |
|---:|---:|---:|---|
| Baseline 20 | 6469.02 | — | Reference |
| 10 | 6469.02 | 0.00 | Inert at this scale |
| 40 | 6416.65 | -52.37 | Directional harm |
| 60 | 5631.28 | -837.73 | Directional harm |
| 80 | 4845.73 | -1623.28 | Directional harm |

The policy is threshold-based: small changes can be inert until they suppress
planting in states where the expected carrot return remains worthwhile. This
experiment found no support for increasing the static parameter above 20 on
this suite.

## What this did not establish

- It did not test a context-aware opportunity value supplied by another graph.
- It did not test different deterministic opponents or market regimes.
- It did not claim a global optimum or authorize a source-policy change.
- It did not validate probability calibration for the price-belief model.

## What it should do for the new system

This experiment is the first inner-loop reproduction oracle. A real runner
should read the adjacent JSON, execute only after the appropriate approval,
and produce the same outcome classifications with passing clean audits. If it
cannot, repair the runner before adding Foundry reasoning, a second graph, or
automatic bounded brackets.
