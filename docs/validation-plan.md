# Checkpoint/resume validation plan

The fixed proof suite is the cartesian product of seeds `42,43` and evaluated
player seats `0,1`, using target policy `carrot_decision_agent`, deterministic
target opponent `carrot_conveyor_agent`, and 144 simulator steps.

For every baseline turn, cache the pre-action observation, baseline action,
opponent action identity, and a JSON-safe complete environment-state snapshot.
Each cache manifest records cache schema, target revision and fingerprints,
engine configuration, opponent, seed, seat, action count, and final outcome.

For each human-selected one-parameter candidate, report the parameter name,
old/new values, first-divergence turn, suffix length, reuse/suffix-run mode,
candidate outcome, and audit status.  The evaluator rejects unknown or
multi-parameter overrides.  It does not write any target source file.

The proof requires a clean full rerun for every suite member in each case:

1. Default parameters: no divergence; cached baseline outcome is reused and
   must equal the clean candidate run.
2. `pass_utility=50.0`: deliberately late divergence; restored suffix outcome
   must equal the clean candidate run and be shorter than the whole match.
3. `pass_utility=100.0`: intentionally early divergence; restored suffix
   outcome must equal the clean candidate run and be nearly the full match.

The command writes a self-contained JSON report under ignored `var/results/`.
Future candidate evaluations must retain a clean full-suite audit beside the
fast cached loop; cached evidence alone is not acceptance evidence.

