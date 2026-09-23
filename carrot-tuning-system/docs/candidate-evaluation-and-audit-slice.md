# Next adapter slice: bounded candidate evaluation and clean audits

## Purpose

This note defines the next implementation slice for the local inner-loop
adapter after the approved baseline caches have been created and reopened. It
is still work inside the local adapter, with the notebook as the review surface
and [`evaluator/runner.py`](../evaluator/runner.py) as the reusable source.

The purpose is to obtain a trustworthy per-match result for one **already
declared** candidate value. The result must say whether the candidate reused
the baseline because its actions never diverged, or restored a baseline
checkpoint and simulated the remaining suffix. It must then compare that fast
result with a clean, full candidate rerun.

This note is a design boundary, not permission to run a candidate yet.

## What is ready

The approved smoke contract pins one target revision and two matched baseline
caches for seed 42, seats 0 and 1, at 720 steps. Both cache files have been
read back and passed their structural/provenance checks. The parent evaluator
already provides the proven primitives:

- `evaluate_cached(...)` replays a cache and either reuses its outcome or
  restores the first divergent checkpoint and runs the suffix;
- `clean_rerun(...)` runs the entire candidate match from the beginning; and
- `audit_cached(...)` compares the fast and clean results and reports a
  pass/fail audit status.

The adapter has not yet wrapped those primitives in its bounded experiment
contract. That wrapper is the next component to design.

### Current first exercise

The notebook now contains a first, notebook-only fast wrapper. It applied the
declared `10.0` override to the validated seed 42 / seat 0 cache. The replay
found no action divergence, so it returned `reused-baseline` with zero suffix
actions and audit status `not-run`. This confirms only the fast-path boundary;
the clean full rerun and comparison remain a separate component.

That component has now run once for this exact match. The independent
719-action candidate rerun returned the same 8849.0 / 8729.0 outcome as the
fast result, so the seed-42/seat-0 audit passed. The matching seat remains a
separate action; no aggregate or candidate classification follows from this
single audited match.

### Completed bounded batch

After that one fully explained example, the seven remaining approved pairs ran
in one bounded batch. All eight candidate/seat clean audits now pass. Values
10.0, 40.0, and 60.0 replayed without action divergence for both seats. Value
80.0 first diverged at turn 107 and used 612-action restored suffixes for both
seats, with matching clean outcomes. The batch is intentionally rendered as
per-match facts only; no mean, ranking, aggregate classification, or policy
recommendation has been computed.

## The one-match workflow

For exactly one candidate value and exactly one validated cache entry:

1. Select the value from `specification["parameter"]["candidate_values"]`.
   Do not derive, round, search for, or add values.
2. Build the one-field in-memory override—for example,
   `{"seed_opportunity_value": 10.0}`. This creates a `CarrotParameters`
   instance in memory; it never writes Kaggriculture policy source.
3. Call `evaluate_cached(...)` with the explicit binding, validated cache, and
   fixed conveyor opponent. Record the mode, first divergence turn, suffix
   action count, outcome, and timing components.
4. Call `clean_rerun(...)` with the *same* seed, seat, steps, override, target,
   and opponent. This is the independent score oracle for the fast path.
5. Call `audit_cached(...)`. A mismatch stops the experiment: its candidate
   result is unusable and no aggregate conclusion may be made.
6. Return a structured per-match record. Do not aggregate, classify the
   candidate, write an evidence packet, or begin the next candidate in this
   component.

## Boundaries that must remain explicit

- The candidate list is `[10.0, 40.0, 60.0, 80.0]`; no other value is in
  scope.
- The smoke suite contains only seed 42 in seats 0 and 1. It is not the
  historical 60-match coarse suite and cannot reproduce its aggregate claims.
- Every candidate/seat fast result needs its own matching clean audit.
- A `reused-baseline` fast path still needs its clean audit. “No divergence” is
  not a waiver from independent confirmation.
- The target binding and cache provenance must match before evaluation. A
  cache from another revision, seat, or seed is not a substitute.
- Candidate parameters are in-memory evaluator inputs. Neither this slice nor
  a successful audit authorizes a source edit.

## Proposed notebook progression

Stay in [`02_local_inner_loop_adapter.ipynb`](../notebooks/02_local_inner_loop_adapter.ipynb).
The next reviewable cells should:

1. explain and prototype a one-match `evaluate_candidate_from_cache` wrapper;
2. show a focused in-memory rejection case for an undeclared override;
3. add the clean-rerun/audit wrapper and display its per-match facts; and
4. only after review, promote those wrappers into `evaluator/runner.py`.

The first live exercise should be one declared value (`10.0`) against one
already validated baseline cache. The matching second seat should be a separate
review step. Only after both seats audit cleanly should we discuss the next
declared candidate or aggregation.

## Success and stop conditions

Success for the first component means: the wrapper accepts only a declared
one-field override, produces a fast result, produces its identical-condition
clean rerun, and returns an explicit passing audit. It does **not** mean the
candidate is good or that the wider historical experiment has been reproduced.

Stop immediately if contract validation, cache validation, fast evaluation,
clean rerun, or audit fails. Preserve the failure facts for diagnosis; do not
try another value, mutate policy source, widen the suite, or explain the
mismatch away.
