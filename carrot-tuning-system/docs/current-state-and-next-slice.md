# Current state and next implementation slice

## Why this snapshot exists

This page is the “where were we?” answer after the project moved from an
audited local evaluator toward a structured Carrot Tuning system. It records
the difference between evidence already earned, architecture now written down,
and code that still needs to be built. That distinction matters: a notebook can
make an architecture feel tangible, but it is not the same thing as a runner
that has reproduced the evidence.

Read the [continuity guide](../README.md) first for the full project intent,
then use this page to resume the immediate implementation sequence.

## What is already real and trusted

### 1. Local Kaggriculture evidence engine

The parent project already contains a real local checkpoint/resume evaluator.
It explicitly binds to the sibling Kaggriculture target, records the target
revision and hashes, stores a pre-decision checkpoint for every baseline turn,
replays candidate observations to first divergence, restores and simulates a
suffix when needed, and clean-audits each fast result with a full rerun.

The evaluator has already produced the following trusted evidence against the
deterministic conveyor opponent over seeds 42–71 in both seats (60 matches per
candidate):

- A ±10% one-parameter screen: all 22 directions were inert on this suite and
  all 1,320 clean audits passed.
- A decision-margin analysis: the carrot graph is threshold-based; the
  smallest observed plant-minus-pass margin was +9.72 and the median was
  +39.02.
- A coarse preference bracket: static `seed_opportunity_value` 10 was inert;
  40, 60, and 80 harmed mean reward by 52.37, 837.73, and 1623.28
  respectively; `pass_utility=25` also harmed reward. All 360 coarse-screen
  audits passed.

The conclusion remains narrow: retain the static carrot-only values 20 and 0
for this exact suite. This is not a global optimum claim and does not yet test
context-aware values supplied by other decision graphs.

### 2. The architecture notebook is an executable mock

[`01_system_model.ipynb`](../notebooks/01_system_model.ipynb) now provides a
walkthrough of the intended control flow:

- frozen dataclasses for a bounded `ExperimentSpec` and matched suite;
- a mocked inner-loop result populated from historical carrot evidence;
- a deterministic evals classification step;
- a mocked reasoning proposal for the next bounded question; and
- a sketch of how a later planner could supply a context-aware
  `seed_opportunity_value`.

It is deliberately explanatory. Its classes and frozen example values are not
the canonical runner contract, and cells that display JSON should be treated
as presentation or loaded from a file—not as a substitute for schema
validation. The canonical machine-readable record is the experiment JSON
described below.

The separate [local adapter workbench](../notebooks/02_local_inner_loop_adapter.ipynb)
starts the next phase. It prototypes one small adapter function at a time,
explains and exercises it, then moves a reviewed version into the real adapter.
It is a guided design/testing surface, not a notebook-only runner or an
authorization to run Kaggriculture.

Its first notebook prototype, `read_spec`, now reads one requested JSON file
and separates unreadable-file failures from malformed-JSON failures. The value
it returns is deliberately not trusted until schema validation accepts it.
The second prototype now loads and self-checks the checked-in Draft 2020-12
schema, then returns a structured pass/fail result with every contract issue.
The historical contract passes with zero issues; a missing required `suite`
appears as a structured schema-rule failure. These are contract-shape facts
only, not lifecycle authorization or a simulator run.

The workbench now also has an implementation checklist. Its first two
prototype stages are checked because their reviewed `read_spec` and
`validate_spec_schema` functions have moved into [the local runner](../evaluator/runner.py).
The explicit target-binding prototype was reviewed and moved into the source
runner. Its three recorded facts all match the explicit sibling checkout; a
nonexistent target path returns a structured binding failure.

The lifecycle-authorization prototype was reviewed and moved into the source
runner. It safely rejects the historical record because archival evidence is
not rerun permission, while an in-memory `approved` status can continue to
later local checks.

The local-control prototype was reviewed and moved into the source runner. It checks
the declared namespace, field, actual baseline default, bounded candidate
envelope, deterministic opponent, complete matched suite, checkpoint/audit
settings, and governance locks against the explicitly bound target. The
historical contract passes; an in-memory envelope containing its baseline value
fails.

The deterministic baseline-cache plan was reviewed and moved into the source
runner. It derives
one content-addressed cache group from every reuse-relevant contract and target
fact, then plans one path per seed/seat match. It does not create directories or
files, call `baseline_match`, or run Kaggriculture.

The cache-state preflight prototype was reviewed and moved into the source
runner. It reads only filesystem
presence for the planned paths. It partitions them into present and missing
entries, while stating that a present file is not valid until a later cache
payload check accepts it. It creates no files and runs no game.

The structural cache-payload validator was reviewed and moved into the source
runner. It validates an already-decoded cache payload's
structure and provenance before reuse. It checks cache version/kind, the bound
target fingerprint, planned match identity, checkpoint-record shape, and
outcome shape. The notebook exercises it with an explicitly illustrative
in-memory mapping and rejects a mismatched seed; it does not itself open a gzip
file or claim simulator evidence.

The gzip-reader handoff was reviewed and moved into the source runner. It reads
one present gzip cache through the existing
parent cache reader and passes the decoded mapping to the structural validator.
Its notebook exercise uses temporary synthetic gzip fixtures that are removed
at the end of the cell: one passes structurally while one decoded wrong-seed
fixture fails. No simulator is imported for the pure gzip helpers, and no game
is run.

The fail-closed cache-preparation prototype was reviewed and moved into the
source runner. It turns cache facts into a preparation
plan. It marks an entry reusable only after presence, successful gzip decoding,
and structural validation; missing, unreadable, invalid, and skipped-present
entries are marked for later materialization with a reason. The actual current
group has 60 materialization decisions and no reuse decisions. This records no
side effect and runs no game.

The one-entry materializer was reviewed and moved into the source runner. It
accepts only a previous `materialize` action, refuses a non-materialize action,
and refuses to overwrite an existing cache before calling the proven parent
baseline evaluator and writer. The runner exposes that function but `run()`
does not orchestrate it yet, so merely validating a contract cannot trigger a
simulator call or filesystem write. Focused guard exercises demonstrate both
refusals without importing or running the simulator.

A separate [approved smallest-matched smoke contract](../experiments/approved/carrot_investment/seed_opportunity_baseline_smoke_v1.json)
now turns that reviewed function into a bounded next operation. It pins the
same target and baseline controls as the historical record, but declares only
seed 42 in both seats at 720 steps. The two-seat suite is intentional: the
runner's matched-suite control rejects a one-seat envelope, rather than silently
weakening the comparison invariant. Its notebook preflight passes schema,
fingerprint, lifecycle, local controls, cache planning, and preparation; both
cache entries were missing and are selected one at a time, beginning with seat
0. The sibling `kaggle-environments` checkout was then installed editable into
the local virtual environment only; no source checkout was changed. The first
selected action (seed 42 / seat 0) has now executed once. It wrote an ignored
local gzip baseline cache containing 719 checkpoints, with decision/opponent
rewards 8849.0 / 8729.0. The runner immediately reopened that file and passed
all five structural/provenance checks, so it is a reusable baseline-cache
candidate for this exact bound target and match. This establishes only the
cache-writing/readback boundary—no candidate evaluation, clean audit, aggregate
claim, source mutation, or evidence packet occurred. The matching seed 42 /
seat 1 action has now also executed once. It recorded
719 checkpoints with decision/opponent rewards 8809.0 / 8789.0, and immediate
reopening passed the same five checks. The approved smallest-matched suite
therefore now has two reusable baseline caches and zero remaining baseline
materialization actions. This is still only cache-infrastructure evidence: no
candidate, clean audit, aggregate, policy change, or evidence packet exists.
The next reviewed implementation slice is to run only the contract's declared
candidates through checkpoint replay/suffix evaluation and require a clean
full-run audit for each match. The detailed boundary and proposed notebook
sequence are in [candidate evaluation and audit slice](./candidate-evaluation-and-audit-slice.md).

The workbench has now begun that slice with a deliberately small candidate
selection gate. It accepts the checked-in contract's `10.0` value for
`seed_opportunity_value` and returns only its one-field in-memory override;
the focused `25.0` example is rejected because it is not declared. This proves
input-envelope enforcement only. It does not read a baseline cache, create
parameters, replay a candidate, run a clean audit, or make an evidence claim.
The next reviewable component is the one-match checkpoint/replay wrapper that
will consume this already-selected override.

That wrapper has now been exercised in the notebook for the declared `10.0`
override against the validated seed 42 / seat 0 cache. It replayed every stored
action, found no divergence, and returned a `reused-baseline` fast result with
zero suffix actions and the cached 8849.0 / 8729.0 outcome. Its audit status is
explicitly `not-run`. This is an unaudited implementation fact, not evidence
that candidate 10 is equivalent or preferable. The next component must perform
the identical-condition clean full rerun and compare it to this fast result.

That clean component has now been exercised. The independently simulated
`10.0`, seed-42/seat-0 candidate match ran 719 actions and returned the same
decision/opponent outcome, 8849.0 / 8729.0, as the fast `reused-baseline`
result; the audit status is `passed`. This makes this one candidate/match pair
audited evidence, but it does not support a two-seat, aggregate, or ranking
claim. The next bounded action is the identical declared candidate against the
already validated seed-42/seat-1 cache, with its own clean audit.

That seat-1 pair and the six remaining declared candidate/seat pairs have now
completed as one explicit bounded batch. Every fast result matched its clean
audit. Values 10.0, 40.0, and 60.0 had no action divergence in either seat and
reused their respective baseline outcomes; 80.0 diverged at turn 107 in both
seats and used a 612-action restored suffix, with clean audits passing. These
are eight audited per-match smoke facts over one seed, not an aggregate
comparison or a replacement for the historical 60-match coarse result. The
workbench now defines an in-memory local smoke evidence-packet shape. Its
builder rejects incomplete, duplicate, undeclared, unaudited, or fast/clean
mismatched coverage; it retains target provenance, per-match fast-path and
timing facts, and descriptive paired aggregates. The displayed aggregate is
explicitly non-conclusive for one seed/two seats and cannot authorize an
interpretation, source change, or further execution. That shape and its
fail-closed immutable local writer have now been promoted into
the reusable adapter. A temporary-fixture exercise wrote/reopened JSON and
confirmed duplicate-destination refusal; it did not create the durable smoke
artifact. The already-prototyped bounded candidate-evaluation/audit wrapper is
now also in the reusable adapter. Its declared-value gate and duplicate-audit
guard were exercised without running a simulator; the eight audited matches
remain the actual game evidence. An attempted transition to `run()` found a
real authority conflict: the current approved smoke contract expressly permits
baseline-cache work but says it does not evaluate candidates. `run()` must not
use candidate-value fields or prior notebook approvals to broaden that scope.

The component workbench is complete. The next safe slice is a new,
source-controlled, human-approved candidate-evidence smoke contract and a
separate end-to-end-run notebook. The required pre-real-system regression gate
has passed: a fast simulator-free pytest suite covers the promoted source
boundaries: declared-value/matched-suite guards,
cache-validation refusal, audit guards, evidence coverage, cache/spec edge
cases, packet JSON round-trip, and overwrite/safety refusal. The real simulator
regression is explicitly marked and excluded from the default suite. No
candidate run, source-policy mutation, packet overwrite, or outer-loop
interpretation is authorized by this transition.

The
[candidate-evidence smoke contract](../experiments/approved/carrot_investment/seed_opportunity_candidate_evidence_smoke_v1.json)
is now human-approved. It carries only the pinned target, seed-42/two-seat/
720-step suite, and declared 10/40/60/80 envelope already reviewed in the
workbench. It authorizes only the specified local candidate/evidence operation;
no simulator work occurred at approval time. The next implementation artifact
is the separate end-to-end-run notebook that wires this exact contract through
`run()` and stops on any failed preflight, audit, or packet-write guard. Its
new [preflight and cache section](../notebooks/03_spec_driven_smoke_run.ipynb)
has now run only read-only gates: the contract passed preflight and both
seed-42 caches decoded and passed structural/provenance validation. The
contract explicitly anchors that reuse to the baseline-only contract identity.
The source `run()` orchestration is now complete for the bounded batch: it
returns only after each cache has been revalidated immediately before use and
each of the eight declared candidate/seat pairs has completed its clean audit.
The exact one-seed batch ran once. Values 10.0, 40.0, and 60.0 reused their
baseline outcome in both seats; 80.0 first diverged at turn 107 and ran a
612-action restored suffix in both seats. All eight clean audits passed. This
is one-seed smoke evidence only. The pure packet builder has now accepted the
real in-memory batch and verified exact eight-match audited coverage before it
created descriptive aggregates. Values 10.0, 40.0, and 60.0 each have a mean
paired delta of 0.0; 80.0 has +937.0 across its two matches, with two divergent
matches and 1,224 total suffix actions. These facts are neither a ranking nor a
recommendation. No interpretation, source-policy mutation, candidate expansion,
or durable packet has occurred. The next review gate is immutable local packet
writing and reopen/overwrite-refusal verification. The writer created the
contract-named ignored local JSON file exclusively. Its initial notebook
verification compared a deserialized JSON list with an in-memory tuple and
raised after the write; the corrected cell normalized through canonical JSON,
then reopened the exact in-memory packet successfully. It verified 6,105 bytes
and SHA-256 `3c9d7f17ea48be41d821c5d6832fa61eb8473645c0f5688877a6812cebc3505a`,
and a second write was refused. The end-to-end smoke notebook is complete.
Its narrow outcome is durable local infrastructure evidence, not a candidate
ranking, a replacement for historical evidence, or a source-policy decision.
The next human-owned choice is to stop here or approve a separate versioned
confirmation envelope.

## Evaluator completion phase

The smoke-run notebook has completed its execution role. The next local work is
the [evaluator-completion workbench](../notebooks/04_evaluator_completion.ipynb),
which begins by characterizing the current source boundary: `run()` returns an
audited `LocalCandidateBatch`, while exact-coverage packet construction and
immutable writing remain separately reviewed source helpers. The first
completion component will make that handoff explicit in reusable source without
rerunning the smoke suite or touching its existing packet.

That first completion component is now complete. The reusable
[`complete_local_candidate_batch`](../evaluator/runner.py) function accepts an
already-audited `LocalCandidateBatch`, builds the exact-coverage descriptive
packet from its retained preflight/baseline/audit facts, and invokes the
existing immutable writer once. It returns a frozen completed-run record that
retains the input batch, packet, and writer receipt. Packet validation precedes
directory creation, so an incomplete batch cannot create an evidence directory;
an already-existing packet destination is refused rather than overwritten. The
notebook exercises this only with synthetic results in a temporary directory.
No simulator ran, cache was created, durable smoke packet was touched, or
interpretation was made. `run()` deliberately remains an audited-batch boundary
until the later command/API and repeat-semantics design is complete. The fast
simulator-free suite now has 25 passing tests and one explicitly deselected
real-simulator regression.

The attempted next component—baseline-only preparation orchestration—has an
intentional contract-model stop. Schema v1 contains no machine-readable field
for operation authority. The completed baseline-only and candidate-evidence
contracts describe their differing permissions only in natural-language
`purpose` fields, and the evaluator must not parse prose or recognize an ID as
an authorization shortcut. The Book 4 prototype therefore refuses operation
authority before a materializer can be reached. No simulator, cache creation,
or source change occurred. The next material decision is whether to introduce
a new versioned schema and contract that declares an explicit baseline-cache
preparation operation; completed contracts remain immutable either way.

The owner approved that contract-model improvement. Schema v1 now accepts an
optional machine-readable `execution_authorization.operations` list and the
source evaluator exposes a fail-closed operation gate. Existing completed
contracts were not edited, so their absent field grants nothing. A new
[baseline-preparation v2 contract](../experiments/approved/carrot_investment/seed_opportunity_baseline_preparation_v2.json)
declares only `baseline_cache_preparation`, is now approved, and rejects
`candidate_evidence_run`. Its explicit baseline-cache anchor points to the
original smoke cache identity. The real read-only plan decoded and validated
both seed-42 caches as reusable, selecting no materialization action; no
simulator or cache write occurred. The schema and source tests cover missing,
allowed, and denied operation authority.

The planning-only baseline-preparation orchestrator is now present in source.
[`LocalInnerLoopAdapter.plan_baseline_preparation`](../evaluator/runner.py)
requires schema validation, explicit target binding, approved lifecycle,
`baseline_cache_preparation` authorization, local controls, and validation of
every present cache. It returns a frozen selection containing at most the first
missing seed/seat action in contract order. A present invalid cache is a hard
diagnostic stop and cannot be replaced; the materializer remains unwired, so
the planner cannot create a cache. Notebook and test exercises use only
synthetic approved fixtures and temporary paths. The default suite reports 29
passing tests and one deselected real-simulator regression. The next component
is explicit repeat/existing-artifact semantics for immutable evidence packets.

That repeat boundary is now implemented as a read-only inspection helper.
[`inspect_local_smoke_evidence_packet_repeat`](../evaluator/runner.py) compares
the expected canonical bytes with a contract-named destination and reports
`missing`, `exact_match`, or `conflict`. Exact bytes are not silently reused as
a rerun success, and differing bytes are a stop; the exclusive writer continues
to refuse every pre-existing destination. The Book 4 exercise uses temporary
synthetic evidence only, with no real packet inspection or modification. The
default suite now has 30 passing tests and one deselected real-simulator
regression. The final remaining completion component is a clear command/API
boundary with those same fail-closed distinctions.

The evaluator-completion workbench is now complete. Its final component exposes
only two CLI modes: `preflight` and `baseline-plan`. Neither has a simulator,
materializer, candidate-evaluation, or packet-write path. `preflight` stops
after the requested read/schema/lifecycle and optional target/control gates;
`baseline-plan` requires the fully gated baseline-preparation authority but
returns only one selected action or an explicit refusal. The notebook exercises
the real approved-contract preflight and verifies the command list, while the
source tests reject a nonexistent broad `run` command. The default suite now
has 32 passing tests and one deselected real-simulator regression. This closes
the evaluator as reusable infrastructure; it does not authorize new execution
or create new game evidence.

The owner also decided how this work should later behave under full automation:
eligible bounded decisions may proceed without an immediate pause, but each
must create a pending human-review record with its choice, evidence/contract
inputs, alternatives, authority, effects, and changed artifacts. Review flags
are not retroactive authority and do not relax the hard stops for undeclared
execution, overwrites/reuse, source-policy edits, scope expansion, or failed
guard recovery. The notebook skills now carry this rule for future agents.

The owner has granted a bounded phase-level autonomy envelope for this evaluator
work. Agents may move through explanatory notebooks, pure/in-memory prototypes,
source promotion, and simulator-free regression checks without asking for every
small component. They must still stop for a new/revised contract, a simulator
or baseline action not already approved, durable-artifact overwrite/reuse
semantics, source-policy mutation, scope expansion, or failed-guard recovery.
This replaces repetitive review with explicit material decision points; it does
not authorize silent scope growth.

The packet-builder section is now present in the end-to-end notebook. It calls
the already-reviewed pure source builder with the in-memory completed batch and
has a separate hideable renderer for the resulting per-candidate descriptive
facts. It deliberately stops with a clear kernel-state error rather than
silently rerunning the simulator if `CANDIDATE_BATCH` is unavailable after a
notebook restart. The source-level fixture tests continue to exercise the
builder's success, incomplete/duplicate coverage, failed-audit, wrong-target,
and writer-safety guards. The actual packet cell has now run in the notebook
kernel holding the completed batch and its hideable renderer displays the
validated descriptive facts. It still does not write a file; a restarted kernel
must not silently rerun the simulator merely to recreate the transient object.

### 3. Step 9.1 is complete as a design and source-control artifact

The notebook's step 9.1 called for one versioned, bounded experiment
specification. That contract now exists:

- [schema v1](../experiments/schema/experiment-spec-v1.schema.json) defines
  the allowed shape of one bounded local experiment;
- [historical coarse seed-opportunity spec](../experiments/historical/carrot_investment/seed_opportunity_coarse_v1.json)
  records the completed bracket, exact target fingerprint, suite, audit rules,
  governance restrictions, and expected aggregate classifications;
- [historical narrative](../experiments/historical/carrot_investment/seed_opportunity_coarse_v1.md)
  reconstructs why the result is credible; and
- [historical notebook](../experiments/historical/carrot_investment/seed_opportunity_coarse_v1.ipynb)
  reads the adjacent JSON and explains the record without rerunning a game.

The schema and historical record were validated with a JSON Schema
Draft 2020-12 validator. The historical expectations were checked against the
already-recorded coarse result.

This means the project has a real source-controlled contract and a credible
reproduction oracle. It does **not** mean the new Carrot Tuning directory yet
contains an implementation that parses this JSON and calls the evaluator.

### 4. Visual architecture is now documented

The [architecture diagrams](./architecture-diagrams.md) show the two-loop
context, inner-loop sequence, outer-loop interaction, conceptual entity
relationships, future multi-graph interaction, and experiment lifecycle. Use
them to regain orientation before editing evaluator, schema, or Foundry-facing
components.

## What is deliberately not built yet

- The [evaluator/](../evaluator/) directory now has reviewed reusable
  boundaries for specification/schema validation, explicit target binding,
  lifecycle/local-control gates, baseline-cache planning and validation,
  one-entry materialization, bounded candidate evaluation with mandatory clean
  audit, and fail-closed immutable local evidence writing. `run()` still stops
  before orchestration because the current approved contract is baseline-only;
  it must not turn technically available candidate helpers into unapproved
  simulator work.
- The default pytest suite is intentionally simulator-free. Its fixture data
  verifies the reviewed adapter contracts rather than claiming new game
  evidence; the separately marked simulator regression and approved notebooks
  remain the places for actual Kaggriculture execution.
- No typed `ExperimentSpec` object exists; the reviewed adapter uses the
  source-controlled JSON mapping and checked-in JSON Schema directly.
- `run()` does not yet orchestrate the parent checkpoint evaluator. Its
  separately reviewed helpers may call it only when invoked explicitly under
  a contract that authorizes that operation.
- The reusable adapter has a local evidence-packet writer, but no durable
  candidate smoke packet has been created because the current contract does not
  authorize candidate evidence creation.
- No deterministic evals module exists yet; its notebook logic is illustrative.
- No Foundry agent, Azure resource, credential, connector, cloud storage, or
  model call has been created or used for this new project.
- No multi-graph action selector or contextual opportunity-value implementation
  exists. `seed_opportunity_value=20` is still only a static carrot parameter
  in the target policy.

These absences are intentional. Building the real local inner loop first is
the safeguard that keeps future Foundry reasoning grounded in verified game
evidence.

## The next narrow implementation slice

The next task is not “build Foundry” and not “search for a better carrot
value.” It is to replace one mock safely.

```text
historical experiment JSON
          ↓
validate schema + target fingerprint (complete)
          ↓
authorize lifecycle + validate local controls
          ↓
load/create matching baseline cache
          ↓
call proven checkpoint evaluator for exactly listed candidates
          ↓
require every clean audit to pass
          ↓
write a real EvidencePacket JSON
          ↓
compare classifications with historical expectations
```

### Acceptance criteria for that slice

The first runner is ready to move on only when it can:

1. Read the historical specification rather than hard-code the bracket.
2. Reject a malformed schema, unknown parameter, changed target hash, missing
   suite control, duplicate candidate, or unauthorized lifecycle status before
   running a simulator.
3. Use the explicit sibling-target binding and existing checkpoint evaluator;
   it must not import a generic `agents` package or edit Kaggriculture source.
4. Produce a durable local evidence packet with provenance, per-match results,
   aggregate paired outcomes, divergence/suffix facts, timing components, and
   clean-audit status.
5. Reproduce the historical classifications: 10 inert; 40/60/80 directional
   harm; all required audits passed.
6. Stop and report a mismatch rather than explain it away or choose a new
   candidate value.

### Evidence from the completed contract-and-target gates

The adapter successfully loaded and validated the historical
`carrot-seed-opportunity-coarse-v1` contract against schema v1. A temporary
copy with its required `suite` removed was rejected before target binding or
simulator execution. This demonstrates contract-shape validation only; it does
not authorize the historical lifecycle or reproduce an experiment.

The actual sibling Kaggriculture checkout also matched all three target facts
recorded by that historical contract: Git revision, carrot shared-policy hash,
and game-engine hash. A temporary contract with a changed expected engine hash
was rejected before simulator execution. This proves provenance matching, not
the experiment's aggregate outcome.

### Human decision after the slice

After this reproduction smoke test succeeds, the human decides whether to
accept the local spec-driven inner loop as the stable foundation. Only then is
the next bounded feature appropriate: a carrot graph-adapter contract for
eligibility, explanation, utility margin, and scenario coverage. Foundry-facing
reasoning remains later, behind the same evidence-packet boundary.

## How to resume after an interruption

1. Read the [continuity guide](../README.md) and this snapshot.
2. Look at the [architecture diagrams](./architecture-diagrams.md), especially
   the system context and inner-loop sequence.
3. Open the [historical narrative](../experiments/historical/carrot_investment/seed_opportunity_coarse_v1.md)
   or its notebook to remember what the first reproduction must match.
4. Read the [schema v1](../experiments/schema/experiment-spec-v1.schema.json)
   before designing a parser or runner API.
5. Keep generated output under ignored `var/`; do not copy disposable caches or
   result reports into the source-controlled contract directory.
6. If a proposed change would add a candidate value, change the opponent/suite,
   modify target policy, or use Foundry/Azure, stop and obtain the appropriate
   human approval first.

## Repository housekeeping note

The prior implementation and documentation foundation were merged into `main`.
The temporary agent branches and secondary worktree were removed after
verification that they had no unique unmerged commits. This is operational
cleanup, not experimental evidence; the authoritative project history remains
the Git log and the source-controlled historical records.
