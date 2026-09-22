# Carrot parameter positive/negative perturbation plan

## Goal

Measure the local sensitivity of every explicit `CarrotParameters` field without
changing Kaggriculture’s game facts, source policy, seed suite, configuration,
or opponent. Each experiment compares exactly one in-memory candidate value with
the unchanged value from the same baseline cache.

This is a **sensitivity map**, not an automatic optimizer. It tells us which
assumptions actually change actions and which direction is promising enough for
a later, human-selected confirmation experiment.

## Core comparison rule

Do not tune through a policy-versus-policy head-to-head match. Both variants
would affect the shared market, making their reward interdependent. Instead,
compare each candidate against the same fixed deterministic opponent:

```text
baseline policy value      vs deterministic conveyor, fixed seed/seat suite
one parameter candidate   vs deterministic conveyor, identical seed/seat suite
```

The first implementation suite should use the target’s deterministic carrot
conveyor opponent, seeds 42–71, and both seats: 60 paired full-season matches
per candidate. The existing five-seed/two-seat suite is only a smoke screen.

## Controls held constant

Every candidate record must preserve:

- target source revision and policy/engine hashes;
- 720-turn configuration and all other `CarrotParameters` values;
- opponent identity and revision (`carrot_conveyor_agent`);
- seeds 42–71 and player seats 0/1;
- checkpoint schema and evaluator version;
- experiment metrics and acceptance rule.

The actual Kaggriculture seed price, crop yield, growth days, market rules, and
other game facts are not parameters in this plan.

## Candidate matrix

Use a relative ±10% perturbation for every nonzero field in the initial screen.
The proposal is deliberately symmetric around the old value and changes no
other field.

| Parameter | Baseline | Negative candidate | Positive candidate | Meaning |
|---|---:|---:|---:|---|
| `supply_high_given_zero_ripe` | 0.05 | 0.045 | 0.055 | Belief in high opponent supply with no ripe evidence. |
| `supply_high_given_one_to_three_ripe` | 0.30 | 0.27 | 0.33 | Belief in high supply with modest ripe evidence. |
| `supply_high_given_four_plus_ripe` | 0.70 | 0.63 | 0.77 | Belief in high supply with strong ripe evidence. |
| `low_price_multiplier` | 0.60 | 0.54 | 0.66 | Assumed low-price scenario relative to observed price. |
| `high_price_multiplier` | 1.20 | 1.08 | 1.32 | Assumed high-price scenario relative to observed price. |
| `low_price_base` | 0.15 | 0.135 | 0.165 | Prior low-price probability weight. |
| `low_price_supply_weight` | 0.65 | 0.585 | 0.715 | How strongly high supply implies low price. |
| `high_price_base` | 0.05 | 0.045 | 0.055 | Prior high-price probability weight. |
| `high_price_demand_weight` | 0.02 | 0.018 | 0.022 | How strongly demand evidence implies high price. |
| `high_price_supply_penalty` | 0.30 | 0.27 | 0.33 | How strongly high supply reduces high-price belief. |
| `seed_opportunity_value` | 20.0 | 18.0 | 22.0 | Policy preference for retaining an owned seed. |
| `pass_utility` | 0.0 | see exception | see exception | Utility of choosing not to plant. |

`pass_utility` has no meaningful relative ±10% change because its baseline is
zero. Do not silently substitute a scale. Before testing it, choose and record
an absolute symmetric pair—for example `-5.0` and `+5.0`—with the reason for
that scale. It is a policy preference, not a belief.

For probability fields, reject any candidate outside `[0, 1]`. Preserve the
conditional-table ordering `zero <= one_to_three <= four_plus`; if a future
perturbation would violate it, choose a smaller human-approved increment rather
than altering multiple table fields together.

## Execution sequence

### 1. Create one baseline cache

Run and preserve one full baseline cache for the 60-match conveyor suite. It
must include a pre-action checkpoint for every decision and an equivalent direct
baseline audit for every match.

### 2. Run 22 fast candidate screens

There are 11 nonzero fields × two directions = 22 initial candidates. For each:

1. Construct the one-field override in memory; never edit Kaggriculture source.
2. Replay baseline observations to each match’s first action divergence.
3. Reuse exact no-divergence outcomes; otherwise restore the checkpoint and run
   only the forward suffix.
4. Record first-divergence distribution, suffix lengths, candidate outcomes,
   and paired deltas.
5. Run a clean full-suite audit with the same deterministic opponent and verify
   every fast outcome against its clean counterpart.

Do not run the `pass_utility` candidates until their absolute scale has been
selected. That leaves 22 planned candidates, not 24.

### 3. Classify the result

Each candidate receives one of these statuses:

| Status | Rule |
|---|---|
| `inert-at-scale` | No action divergence in all 60 matches; retain the exact outcome reuse and clean audit. |
| `directional-signal` | Diverges and shows a predeclared positive paired effect without safety regressions. |
| `directional-harm` | Diverges and has a predeclared negative paired effect or safety regression. |
| `inconclusive` | Mixed results, insufficient effect size, failed audit, or unchosen acceptance threshold. |

No `directional-signal` result changes the target policy. It merely identifies a
candidate for a second, independently predeclared confirmation suite.

### 4. Confirm only promising directions

For a promising field, do not immediately search every possible value. First
repeat the baseline/candidate comparison on a disjoint confirmation suite (for
example seeds 72–101, both seats) with the same opponent and metrics. Then,
and only with human approval, test a small local bracket around the promising
value.

## Metrics to record

For every candidate and every seed/seat:

- baseline and candidate final reward, win/loss, and paired reward delta;
- decision counts and available crop lifecycle metrics;
- first divergence turn, suffix action count, and reuse/suffix mode;
- equivalent direct baseline time, candidate clean time, replay time, suffix
  time, and checkpoint-capture time as defined in
  [`timing-contract.md`](./timing-contract.md);
- baseline/candidate source revision, parameter old/new values, and audit
  status.

Aggregate: mean and median paired delta, win/tie/loss counts, seat-specific
means, divergence percentiles, no-divergence count, and audit pass count.
Keep calibration metrics separate from economic reward whenever a prediction
label is available.

## Acceptance rule to choose before running

Do not call any value better until a human records a rule. A reasonable
starting template is:

```text
Candidate is a confirmation candidate only if:
  every clean audit passes,
  mean paired reward delta is positive,
  neither seat has a negative mean paired delta beyond the agreed tolerance,
  no new lifecycle/safety failure appears, and
  the effect repeats on the disjoint confirmation suite.
Otherwise: retain baseline or mark inconclusive.
```

The exact reward tolerance, confidence method, and minimum practical effect
must be selected before interpreting results. This plan intentionally does not
invent them after seeing outcomes.

## Expected deliverables

1. One versioned baseline cache manifest.
2. One JSON report per perturbation candidate.
3. One aggregate sensitivity table sorted by parameter and direction.
4. One clean-audit report per candidate.
5. A human decision log: `retain_baseline`, `confirmation_candidate`, or
   `inconclusive`.

All generated caches and reports remain disposable under ignored `var/`.
