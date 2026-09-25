# Kaggriculture local counterfactual evaluator

This repository evaluates the sibling Kaggriculture carrot policy without
modifying it.  It is local only: it has no cloud configuration, credentials,
connectors, model calls, candidate search, or automatic policy mutation.

The Foundry-facing control plane and the parallel Wheat/Watermelon tuner
projects live under [`carrot-tuning-system/`](carrot-tuning-system/),
[`wheat-tuning-system/`](wheat-tuning-system/), and
[`watermelon-tuning-system/`](watermelon-tuning-system/). This root package
remains the shared deterministic evaluator and simulator-proof test surface.

## Agent starting points

Repository-wide rules are in [AGENTS.md](./AGENTS.md). Before changing a tuner,
read that tuner's local instructions: [Carrot](./carrot-tuning-system/AGENTS.md),
[Wheat](./wheat-tuning-system/AGENTS.md), or
[Watermelon](./watermelon-tuning-system/AGENTS.md). Carrot Foundry work also
starts with its [Foundry transition handoff](./carrot-tuning-system/docs/foundry-transition-handoff.md)
and [next-agent handoff](./carrot-tuning-system/docs/next-agent-foundry-notebook-handoff.md).
Those Carrot instructions contain the standing low-cost cloud-build authority;
the other tuner projects remain local-only.

The initial proof records a deterministic baseline against the target's
`conveyor` opponent, saves a pre-action simulator checkpoint for every turn,
and evaluates one human-specified `CarrotParameters` change.  A candidate is
replayed against baseline observations until its first different action.  If it
never differs, the baseline outcome is reused byte-for-byte; otherwise a fresh
simulator restores the saved pre-action state and runs only the suffix.

See [binding and provenance](docs/binding-and-provenance.md) and the
[validation plan](docs/validation-plan.md).  Generated baseline caches and
reports belong in ignored `var/` and may be deleted at any time.

## Minimal proof

Use the target project's existing local environment explicitly:

```bash
../kaggriculture/.venv/bin/python scripts/checkpoint_regression.py --prove
```

The proof uses seed/seat pairs `(42, 0)`, `(42, 1)`, `(43, 0)`, and `(43, 1)`,
the target revision recorded in its report, the deterministic `conveyor`
opponent, and 144 steps.  It audits all three cases with clean full reruns:

* unchanged default parameters (exact baseline reuse);
* `pass_utility: 0.0 -> 50.0` (a deliberately late divergence); and
* `pass_utility: 0.0 -> 100.0` (an intentionally early divergence).

These are proof fixtures, not recommendations to apply to Kaggriculture.

## Executable local runs

All commands use the target project's already-installed local environment and
write only disposable, ignored artifacts under `var/`.

```bash
# Recreate the original 140-match, full-season timing and decision-trace sweep.
../kaggriculture/.venv/bin/python scripts/baseline_timing_sweep.py

# Demonstrate a late and an early one-parameter divergence, each checked
# against a clean full rerun using the deterministic pass opponent.
../kaggriculture/.venv/bin/python scripts/parameter_divergence_demo.py

# Run the small four-match checkpoint/resume proof suite.
../kaggriculture/.venv/bin/python scripts/checkpoint_regression.py --prove

# Compare seed_opportunity_value 20 versus 80 over seeds 42–51 and both seats.
../kaggriculture/.venv/bin/python scripts/compare_seed_opportunity_values.py

# Pit the 20 and 80 policy variants directly against one another on five seeds.
../kaggriculture/.venv/bin/python scripts/head_to_head_seed_opportunity_values.py

# Compare the 0.30 and 0.40 opponent-supply belief variants head to head.
../kaggriculture/.venv/bin/python scripts/head_to_head_seed_opportunity_values.py \
  --parameter supply_high_given_one_to_three_ripe --left-value 0.30 --right-value 0.40

# Run the fixed 22-candidate, 60-match (+/-10%) sensitivity matrix.  Every
# checkpoint result receives a clean full-suite audit; this is not a search.
../kaggriculture/.venv/bin/python scripts/perturbation_sensitivity_suite.py --workers 4

# Read the observed investment-decision margins from the 60-match cache.
../kaggriculture/.venv/bin/python scripts/decision_margin_report.py

# Run the fixed coarse preference bracket (seed opportunity 10/40/60/80 and
# pass utility -25/+25), again with a clean audit for every match.
../kaggriculture/.venv/bin/python scripts/perturbation_sensitivity_suite.py \
  --screen coarse-preferences --workers 4
```

The first script is a baseline/timing fixture. The second demonstrates the
incremental counterfactual mechanism. The third is the small automated
correctness proof. None changes Kaggriculture source or selects parameters.

Counterfactual performance reports follow the [timing contract](docs/timing-contract.md):
each includes a direct equivalent baseline, a clean candidate run, and a
separate replay/restore/suffix breakdown. Profiling-harness timings are never
used as the comparison baseline.

For the planned one-field positive/negative sensitivity screen, see the
[carrot parameter perturbation plan](docs/carrot-parameter-perturbation-plan.md).

## Watermelon first pass

The parallel local MELON tuner lives in
[`watermelon-tuning-system/`](watermelon-tuning-system/). Its first approved
proof binds the same sibling Kaggriculture checkout explicitly, checkpoints
before each decision, reuses no-divergence baselines, restores divergent
suffixes, and clean-audits every candidate. See its
[first-pass result](watermelon-tuning-system/docs/first-pass-result.md) and
run it with:

```bash
RUN_ID=20260924-next

../kaggriculture/.venv/bin/python scripts/run_watermelon_first_pass.py \
  --spec watermelon-tuning-system/experiments/approved/melon_investment/future_price_multiplier_smoke_v1.json \
  --target-root ../kaggriculture \
  --cache-root var/watermelon-tuning-system/runs/$RUN_ID/cache \
  --report-dir var/watermelon-tuning-system/runs/$RUN_ID/report
```

The current generated Watermelon receipt path is
[melon-future-price-multiplier-smoke-v1.json](var/watermelon-tuning-system/canonical-20260924/report/melon-future-price-multiplier-smoke-v1.json).
It is ignored run output and is not present in a fresh checkout until the
approved command generates it; no new reproduction is implied by this link.

## Wheat first pass

The parallel local WHEAT tuner lives in
[`wheat-tuning-system/`](wheat-tuning-system/). Its first approved proof uses
the same checkpoint/resume and clean-audit controls over seeds 42 and 43 in
both seats. See its
[first-pass result](wheat-tuning-system/docs/first-pass-result.md) and run it
with:

```bash
RUN_ID=20260924-next

../kaggriculture/.venv/bin/python scripts/run_wheat_first_pass.py \
  --spec wheat-tuning-system/experiments/approved/wheat_crop/future_price_multiplier_smoke_v1.json \
  --target-root ../kaggriculture \
  --cache-root var/wheat-tuning-system/runs/$RUN_ID/cache \
  --report-dir var/wheat-tuning-system/runs/$RUN_ID/report
```

The current generated Wheat receipt path is
[wheat-future-price-multiplier-smoke-v1.json](var/wheat-tuning-system/canonical-20260924/report/wheat-future-price-multiplier-smoke-v1.json).
It is ignored run output and is not present in a fresh checkout until the
approved command generates it; no new reproduction is implied by this link.

## Foundry submission package

The current submission package lives in [`submission/`](submission/) and is
documented in [submission/README.md](submission/README.md). Its build packages
the promoted analyst/evaluator source, redacted receipts, and the Blazor review
surface. The package records Evidence Analyst v2, Evidence Analyst Judge v1,
and Proposal Drafter v3 as review-only roles; it does not copy notebooks,
credentials, raw packets, or the Kaggriculture checkout.

## Ongoing-crop tuner scaffolds

The current branch also contains bounded first-pass scaffolds for the ongoing
crop graphs:

- [Strawberry Tuner](strawberry-tuning-system/README.md) — canonical reviewed
  receipt under `var/strawberry-tuning-system/runs/20260925-strawberry-v3/`;
  candidate `0.05` produced a paired delta of `-745.00`, while `0.8` and `1.2`
  were inert, with all four clean audits passing.
- [Tomato Tuner](tomato-tuning-system/README.md) — approved first-pass receipt
  under `var/tomato-tuning-system/first-pass-20260925/`; candidate `0.05`
  produced a paired delta of `-438.50`, while `0.8` and `1.2` were inert, with
  all four clean audits passing.

These are four-match infrastructure proofs, not policy promotions. Both remain
bounded to one point-estimate parameter, fixed seeds/seats, checkpoint/resume,
and independent clean audits.
