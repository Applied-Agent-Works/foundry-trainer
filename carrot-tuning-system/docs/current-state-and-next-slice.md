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

> **Current-state marker — 2026-09-24:** the later sections headed
> **Current Foundry state superseding the historical receipts above** and
> **Newly staged capability slices** are authoritative. Earlier chronological
> paragraphs intentionally preserve deployment, rollback, and telemetry
> history; they are not current inventory.

> **Local shadow-integration marker — 2026-09-26:** Carrot, Wheat,
> Watermelon/MELON, Tomato, and Strawberry now have a descriptive graph
> registry and a non-mutating shadow-proposal seam in `src/kaggriculture_eval`.
> This slice does not choose
> between crops, change the applied game action, or alter the Foundry packet
> path. Their approved smoke contracts are now re-pinned to the current
> Kaggriculture revision, with fresh clean-audited receipts recorded separately
> from the historical runs.

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

## Current authoritative handoff: Foundry transition

The evaluator-completion workbench is complete. The local evaluator now has
reviewed, tested boundaries for contract/schema validation, target binding,
operation authorization, baseline-cache planning and validation, bounded
candidate evaluation with clean audits, immutable packet construction/writing,
repeat inspection, and an intentionally narrow CLI. The fast regression suite
has 32 passing tests and one separately marked real-simulator regression.

The approved baseline-preparation v2 contract was planned against the real
local cache group; both required seed-42 caches were structurally valid and
reusable, so it selected no materialization action. No simulator or cache write
occurred in that planning operation. The one-seed candidate smoke packet remains
bounded infrastructure evidence, not a policy recommendation.

The Foundry refinement analyst is now the active next workstream, not unfinished
evaluator work. The owner-created `foundry-trainer` project is reachable, and
the current deployment, no-tools prompt agent, invocation, and telemetry
blocker are recorded in the superseding section below. The full handoff—
including the modifiable source layout and remaining review boundaries—is the
[Foundry transition handoff](./foundry-transition-handoff.md).

The [evidence analyst workbench](../notebooks/06_evidence_analyst.ipynb) has
now established five pure prototypes: immutable submitted-packet and
analyst-response shapes, a deterministic eligibility gate, a compact
packet-backed brief, constrained analyst instructions, and a deterministic
structured-response gate. The workbench exercised those boundaries by reading
the existing immutable smoke packet and changing only in-memory copies to prove
failed-audit and proposed-value refusal. `gpt-5.6-luna` is the selected model
candidate and is now deployed as `evidence-analyst-luna-v1`; no model
invocation has occurred. Those reviewed behaviors are now
promoted into the local [`analyst/`](../analyst/) package and covered by eight
fast, simulator-free tests: accepted packet/brief construction; failed audit;
wrong packet binding; unknown planning field; uncited claim; dropped limitation;
non-pending review state; and source-controlled model/instruction status. That
source-promotion step invoked no simulator or model and wrote no evidence; it
also created no prompt-agent entry point. The next explicit review
boundary is the Foundry provisioning decision record. That record now exists:
the owner selected East US 2, a low-cost prompt-agent path, no tools or
connectors, and retained redacted 30-day traces for evaluation insight. The
owner also selected a $5 monthly ceiling and approved moving the Foundry
account/project, Log Analytics workspace, Application Insights component, and
alert rule into the dedicated `rg-foundry-trainer-eastus2` group. Azure
validated and completed that move; the resulting stale Application Insights
workspace reference was repaired and reread, while the workspace's 30-day
retention and enabled alert rule remained intact. A resource-group-scoped $5
monthly actual-cost budget now begins 2026-10-01, alerting the owner at 50%,
80%, and 100%. A read-only capacity check confirms the selected East US 2 Data
Zone Standard fallback for `gpt-5.6-luna`; Regional Standard is unavailable.
The Evidence Analysis Foundry Component Build now records the exact deployment
request, the approved Azure apply, and the successful readback. The no-tools
prompt agent has also been created and verified; there is still no tool,
connector, Knowledge index, or model invocation. See the
[provisioning decision record](./foundry-provisioning-decision-record.md).

The next focused task is not another deployment. A successor should use the
[next-agent Foundry notebook handoff](./next-agent-foundry-notebook-handoff.md)
to review the fixed-fixture evaluation workbench, the optional orchestration
workbench, and the Agent Insights blocker before any new cloud action.
The context-holding agent acts as orchestrator: any subagent receives one
small bounded task, explicit allowed/prohibited actions, verification, and a
stop point; its report never grants authority for the next step.

Notebook 07 opens with a self-contained handoff that repeats the intended
prompt-agent boundary, authority map, current cloud posture, reviewed sequence,
and claims-sample limits. Component 2 now has a pure first slice: a frozen
read-only discovery plan derived from the validated desired-state record. It
names project identity/reachability, existing deployments, and existing prompt
agents as future observations while allowing no environment change, cloud
mutation, model invocation, or stored cloud output. A missing SDK remains an
environment prerequisite to record, not permission to install or repair
packages. The next human decision is which bounded action to authorize after
review: a pure local check, an environment change, or one authenticated cloud
read. None authorizes request construction or a cloud mutation. The notebook
also has a separate hideable descriptive renderer for the in-memory plan; it
has no stored output and cannot be mistaken for project inventory. Component 2a
now has a recorded local SDK-prerequisite result: `azure-ai-projects 2.7.0` and
`azure-identity 1.25.3` are present and their module specs are available. The
check performed no installation, Azure-client import, credential construction,
network access, or cloud read. The renderer records this as local metadata only.
Notebook 07 then executed the approved pure request record against the exact
account/project target. The project was reachable and returned zero model
deployments and zero prompt agents; no mutation or model invocation occurred.
The pure deployment-request construction, validation, and presentation slice
is now complete. It matches the approved model/configuration and empty
preflight, remains `pending_human_review`, and has made no Azure apply call.
The model deployment has since been approved, applied, and read back as
`Succeeded`. Component 5's no-tools prompt-agent definition was approved, and
component 6 created/read back agent `evidence-analyst` version `1` against the
verified deployment. Both resources were then manually rolled back. No model
invocation occurred; notebook 07 remains unchanged.

### Latest notebook-07 invocation diagnostic

The first fixed-fixture invocation is recorded as response
`resp_0435be6d6b422531006ab57296973c8195bbd983b98c4e609e`. The notebook now
retrieves that same response without invoking again and records status
`incomplete`, reason `max_output_tokens`, zero output characters, and 200 output
tokens spent on reasoning. The deterministic response gate correctly refuses
the empty body as invalid JSON. The trace cell also executes, but the installed
`azure-ai-projects` client has no `agent_insight_monitors` operation, so the
trace query fails closed with an actionable SDK-surface error. This is not
evidence that the agent produced no trace; it means the approved notebook path
does not yet expose a trace query. Do not rerun the model message or change the
environment until the owner reviews the response-budget and telemetry options.

The clean rebuild has now been executed through notebook 07. It recreated
deployment `evidence-analyst-luna-v1` at six Data Zone capacity units (6,000
TPM) and prompt agent `evidence-analyst` version 1. The new response completed
under a 5,000-token budget with 536 output tokens, but the deterministic gate
refused it because the model returned `summary`, `findings`, and
`unsupported_claims` rather than the source-controlled v1 response fields
`analyst_contract_version`, `packet_sha256`, `assessment`, and `citations`. The
next bounded repair is to make the prompt-agent instructions state that exact
JSON contract and then perform a separately reviewed agent-version update or
rebuild. No trace query was performed because the installed SDK still exposes
no `agent_insight_monitors` operation.

That prompt repair is now complete. The source-controlled instructions are
`evidence-analyst-v2` and state the exact six-field JSON object, including the
packet checksum, exact citations, required limitations, and prohibition on
extra fields. Notebook 07 created agent version 2 and reran the fixed fixture;
the response matched the local contract and the deterministic gate accepted it
with `review_status: pending_human_review`. The remaining error is isolated to
trace retrieval: the installed SDK still exposes no
`agent_insight_monitors` operation.

The trace path is now corrected to the installed SDK's beta namespace,
`client.beta.agent_insight_monitors`. Notebook 07 created disabled monitor
`monitor_1cc62eccddcf46ed826fa08ed497a92f` for `evidence-analyst` and read it
back successfully. The trace query now runs successfully and reports one
monitor with zero matching insights. No scheduled or manual insight-generation
run has been started; that remains a separate reviewed action with possible
model-token cost.

The first bounded on-demand run was attempted with a 168-hour lookback and a
deterministic operation ID. Foundry rejected it before analysis because the
project has zero valid Application Insights connections. Notebook 07 now
records that exact prerequisite error and a credential-free connection
inventory. No insights were generated. The next action is to create or attach
the reviewed Application Insights project connection, then rerun the same
bounded analysis.

That connection and its prerequisite permissions are now configured and read
back idempotently in notebook 07. The notebook also captured a new post-
connection fixed-fixture response. The Agent Insights run remains blocked by a
service-side `Forbidden` dependency error despite the connection and role
readbacks. The final notebook completion packet marks this with a red `❌` and
flags the next retry/repair decision with a yellow `⚠️`; it does not start
another billable iteration automatically.

The authorized chat-side diagnosis found that the project API reported the
managed-identity connection as `UnknownConnectionPropertiesV2`. The same named
connection was repaired in place to the service-accepted AppInsights `ApiKey`
shape using the existing connection string held only in memory; notebook 07 was
rewritten to reproduce that exact idempotent repair without storing the secret.
The bounded v9 run still returns the same Agent Insights dependency `Forbidden`,
so no further billable retry is being started automatically.

The Microsoft claims sample revealed two additional tracing requirements that
are now represented in notebook 07: tracing flags must be set before Azure SDK
imports, and the `AIProjectInstrumentor` plus Azure Monitor exporter must be
configured before the traced call. The sample also creates an account-level,
shared App Insights connection; notebook 07 now creates/reuses that same
account-level boundary. The exporter dependency is not installed in the current
environment, so the notebook records a red `❌` prerequisite error rather than
installing it automatically.

The chat-side diagnosis also identified the prompt agent's instance identity as
missing from App Insights RBAC. Notebook 07 now discovers that live identity
and idempotently assigns Monitoring Metrics Publisher, Monitoring Reader, and
Log Analytics Reader at the App Insights scope. The assignments were created
once and read back; the next Agent Insights attempt still returned `Forbidden`,
so no further billable retry is automatic.

The approved final tracing iteration installed the reviewed exporter packages,
configured tracing before Azure SDK imports, and captured a new accepted fixed-
fixture response `resp_0017cf238c7e43e4006ab5a9f35ce881969284d851b5b6fa99`.
The Agent Insights analysis still returns the same service-side `Forbidden`
dependency error. The notebook therefore stops with a red blocker rather than
spending another iteration.

The next bounded diagnostic followed the Microsoft claims sample directly:
tracing bootstrap, one temporary named agent, one redacted response, then
conversation/agent cleanup in `finally`. `carrot-sample-tracing-repro-v1`
returned a response and was fully removed. Therefore ordinary Foundry agent
invocation and tracing are proven; the remaining `Forbidden` is specific to
the Agent Insights analysis dependency or its preview/model compatibility.
The notebook records the sample result as green and keeps Agent Insights red;
no further retry is justified without a new owner decision.

The current Azure SDK Agent Insights sample was then reproduced in the same
notebook: a temporary external agent emitted fictional spans, the notebook
queried Azure Monitor Logs until all expected spans were ingested, and a
preview-enabled client created a temporary monitor and started one run. The
run returned the same `Forbidden` dependency error after ingestion succeeded.
The temporary agent and monitor cleanup readback found zero leftovers. This
isolates the blocker to the Agent Insights service dependency/model or preview
path, not to our real-agent trace production or ingestion timing.

This Agent Insights investigation is now **abandoned/deferred**. The durable
submission boundary is the deterministic evidence analyst plus ordinary
redacted tracing; no scheduled monitor or further on-demand insight run is
authorized. Future quality work should use the staged Foundry Evaluations and
LLM-as-judge workbench instead.

The next documentation hardening task is to retrofit notebooks 01–06 with the
same rehydration pattern now demonstrated in notebook 07: desired state,
preflight, validated request, idempotent create/reuse, readback, historical
receipt, and explicit drift/overwrite guards. This remains a TODO; it does not
authorize recreating the rolled-back Foundry resources.

### Current Foundry state superseding the historical receipts above

Notebook 07 subsequently rebuilt the reviewed resources and is the current
cloud source of truth. Its latest idempotent readbacks show deployment
`evidence-analyst-luna-v1` at `gpt-5.6-luna` `2026-07-09`,
`DataZoneStandard`, capacity 6 (6,000 TPM), and no-tools prompt agent
`evidence-analyst` version 2. One fixed redacted fixture response was accepted
by the deterministic local gate and remains `pending_human_review`.

The telemetry setup now also has a disabled Agent Insights monitor, a
project-managed Application Insights connection, and recorded role
prerequisites. The on-demand analysis run is **not** successful: Foundry
returned `Forbidden` for a required dependency, and the monitor query contains
zero matching insights. Do not retry, alter RBAC, enable scheduled monitoring,
or add a telemetry resource without a new bounded owner decision. Earlier
zero-inventory and rollback wording remains useful only as historical receipt.

### Standing authority for the next low-cost build slice

The owner has removed the earlier per-resource approval bottleneck for the
ordinary Carrot Foundry build path. An agent may execute an idempotent,
notebook-backed create/reuse/readback cell for the existing-envelope model,
no-tools agent, or small fixed-fixture Foundry Evaluation resource after the
cell declares its target, token budget, redacted data boundary, and guard. The
exact scope and exclusions are canonical in [AGENTS.md](../AGENTS.md). This is
not authority to repair Agent Insights, alter IAM/authentication, add Azure
services, raise capacity, enable spillover/auto-upgrade, or expand the agent's
tools or data access.

The [mock graduation protocol](./mock-graduation-protocol.md) governs the
remaining illustrative system-model components. It prevents a rush to replace
teaching code with unproven behavior: deterministic assessment is the next
local component, the reasoning mock graduates through the constrained Foundry
analyst, and contextual opportunity-value logic remains deferred until it has
authoritative inputs and calibration evidence.

The Foundry project submission is due tonight, while the farming-agent and
policy-tuning work has a separate one-week window. The immediate deliverable is
therefore a real, modifiable Foundry control-plane vertical slice, not a rushed
new carrot experiment or contextual-policy implementation. The later farming
work must continue through bounded contracts and clean audits without changing
the submission's authority boundaries.

The older sections below preserve the implementation history. Where their
"next slice" language conflicts with this handoff, this section is the current
source of truth.

## What remains deliberately bounded

- The [evaluator/](../evaluator/) directory has reviewed reusable boundaries
  for specification/schema validation, explicit target binding,
  lifecycle/local-control gates, baseline-cache planning and validation,
  one-entry materialization, bounded candidate evaluation with mandatory clean
  audit, and fail-closed immutable evidence writing. Its CLI remains narrow;
  it must not turn technically available helpers into unapproved simulator
  work.
- The default pytest suite is intentionally simulator-free. Its fixture data
  verifies the reviewed adapter contracts rather than claiming new game
  evidence; the separately marked simulator regression and approved notebooks
  remain the places for actual Kaggriculture execution.
- No typed `ExperimentSpec` object exists; the reviewed adapter uses the
  source-controlled JSON mapping and checked-in JSON Schema directly.
- The reusable adapter and smoke-run notebook have created the approved local
  candidate packet; a larger confirmation envelope is still a separate human
  decision.
- The first live Foundry Evaluation/LLM-judge run has completed in Notebook 08
  against one actual redacted packet/response row. It passed with aggregate
  score `0.9`, six dimension scores 4/4/5/5/5/4, and 2,994 judge tokens;
  human review remains pending. Notebook 09 remains the proposal-drafter
  workbench and its exact low-cost cloud-action record.
- The Foundry deployment, no-tools agent, and one redacted invocation are real
  and recorded in Notebook 07. Agent Insights analysis remains blocked by the
  recorded `Forbidden` dependency error.
- No multi-graph action selector or contextual opportunity-value implementation
  exists. `seed_opportunity_value=20` is still only a static carrot parameter
  in the target policy.

These absences are intentional. Building the real local inner loop first is
the safeguard that keeps future Foundry reasoning grounded in verified game
evidence.

## Historical next-slice record

The following section preserves the earlier pre-run implementation plan. It is
kept for provenance, but it is not the current next action.

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

### Canonical notebook execution policy

Notebook code cells are evidence-bearing actions, not merely drafts. Every
executable cell must run in dependency order. A missing approval, package,
credential, or resource precondition is handled by running the cell and
raising a descriptive fail-closed error that identifies the blocker and the
exact repair; the same cell is rerun after the repair. No cell is silently
deferred, labelled “intentionally not called,” or replaced by MCP, CLI, portal,
or a standalone script. Idempotent guards make reruns safe, but they never
replace execution. This is the standing rule for all future agents.

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

## Newly staged capability slices

Two follow-on workbenches are now present and have been executed locally:

1. [Notebook 08](../notebooks/08_foundry_evaluation_workbench.ipynb) reuses the
   promoted analyst contracts with the actual redacted packet and recorded
   response, proves the deterministic response gate, and completes one
   dataset-targeted Foundry Evaluation with aggregate score `0.9`. It does
   not invoke the analyst or claim a game-quality score.
2. [Notebook 09](../notebooks/09_foundry_orchestration_workbench.ipynb) now
   completes the local analyst-to-reasoning handoff, full one-parameter
   proposal contract, five deterministic refusal guards, and the live
   idempotent create/reuse/readback path. Discovery found zero endpoints; the
   apply created `experiment-proposal-drafter` version 1, a schema repair
   created version 2, and the final explicit JSON-contract repair created
   version 3. A live readback verified version 3; three redacted boundary
   cases (valid, incomplete, and authority-injection) all passed. It did not
   run a simulator or create a multi-agent workflow resource.

Both notebooks are design/prototype evidence, not new authority. Before any
cloud evaluation or second-agent deployment, the owner must review the visible
unchecked tasks, confirm the fixture/rubric and role boundary, and approve the
exact Foundry operation in its own notebook cell. Their code cells were run
locally in dependency order; the only initial repair was adding the required
`mean_candidate_decision_reward` field to the synthetic aggregate fixture in
Notebook 08. Notebook 09's local fixture is bound through the promoted analyst
response validator; its proposal envelope is explicitly fixture-only and does
not authorize a new experiment.

Notebook 08 has since been rebuilt as the full numbered evaluation notebook.
Its local cells load the actual packet at
`var/carrot-tuning-system/candidate-evidence-smoke/evidence-packets/` and the
actual `RECORDED_INVOCATION_OUTPUT` receipt from Notebook 07, verify the
checksum and deterministic response gate, construct one redacted JSONL row,
define the six-dimension ordinal judge rubric, and execute exact evaluator/run
cells. The evaluator and run were reused idempotently on the final rerun; the
one-row result completed with aggregate score `0.9`, pass label, and 2,994 judge
tokens. All notebook cells parse, compile, and retain actual local/cloud
outputs. Human review remains pending.

## Latest Foundry Evaluation readback — 2026-09-24

Notebook 08 now contains the actual cloud readback for the first fixed,
dataset-targeted evaluation. The exact evaluator and run were reused on the
final idempotent rerun; no duplicate billable run was created.

- Evaluation: `evidence-analyst-language-v1`
- Evaluation ID: `eval_b73c2e65f474419d9e2e39be5661d413`
- Run ID: `evalrun_19e057784a3448a0baed96708db3b6f7`
- Dataset hash: `2bcfd98a9b91f6637710e3cb63d67d58275accb7f681d9589463f0e4dadc8350`
- Status: `completed`; one item passed; zero errors
- Aggregate judge score: `0.9`; label: `pass`
- Judge token usage: 2,994 total tokens for the one item
- Dimension scores: grounding 4, citation discipline 4, limitation preservation 5,
  boundedness 5, review boundary 5, usefulness 4

The judge specifically praised the preserved smoke limitation, human-review
boundary, and refusal to rank or propose experiments. It noted that the
aggregate claims were cited at packet paths but that the underlying aggregate
contents were not independently visible in the supplied context. This is a
language-quality assessment of the analyst response, not a game result or
policy recommendation. Human review remains pending.

The current separation-of-concerns path is now also real: Notebook 08 created
or reused the distinct no-tools prompt agent `evidence-analyst-judge`, version
1, on the existing `evidence-analyst-luna-v1` deployment. It invoked that
agent once with the redacted brief and recorded analyst response. Response ID
`resp_08209bffa392b90c006ab5ed1e70388195967de3a666869f9c` passed the local
judge-response gate with overall score `1.0` and six dimension scores of 5.
The request hash is
`2b4eadb9ddf1f5d07b0884d51f8b4c1e5bedbec4851fbfff9e9d4915e2bbd1e5`.
The response remains `pending_human_review`. The prior direct Foundry
Evaluator run is historical evidence, not the current judge-agent path.

Notebook 08 then ran two judge-agent boundary cases. The valid response scored
`1.0` with all six dimensions at 5. A schema-valid overclaiming response scored
`0.46`, with boundedness at 1 and limitation preservation at 2. Wrong packet
binding and missing `pending_human_review` were rejected locally before any
agent call. These are judge-boundary results, not game-quality evidence; human
review remains pending.

## Packaging audit update — 2026-09-24

Notebook 03 now preserves its real immutable-packet guard failure and no longer
stores dependent success output from an earlier kernel state. Packet completion
remains visibly unchecked; no new simulator run or packet overwrite was
performed. The promoted Evidence Analyst tests use a source-controlled redacted
fixture rather than ignored `var/` state. Wheat and Watermelon receipts remain
ignored generated outputs, and Watermelon's next receipt now includes the same
top-level `audit_status` field already present in Wheat.

## Repository verification snapshot — 2026-09-25

The packaging/submission conversation added the receipt-backed Blazor demo,
backend build/publish checks, redacted fixture package, and current submission
manifest. The ongoing-crop scaffolds now include approved Strawberry and Tomato
first-pass contracts and canonical local receipts alongside Carrot, Wheat, and
Watermelon/Melon.

The current verification run reports **69 fast tests passed and 7 simulator
tests passed**. All notebooks compile and all JSON files parse when the .NET
`launchSettings.json` BOM is decoded as UTF-8-with-signature. The BOM is a
normal .NET-generated encoding marker, not a secret or content-integrity issue.

The working tree remains intentionally uncommitted while packaging and tuner
agents finish their shared-worktree changes. No generated `var/` receipt is a
source-controlled contract or a policy-promotion decision.

## Latest runtime Foundry invocation — 2026-09-25

The port-5000 backend made a real server-side call to the notebook-created
`evidence-analyst` agent using the completed temporal packet. This was not the
local `DemoConversationService` preview.

- Agent: `evidence-analyst`
- Response ID: `resp_0d6284bb803045f2006ab6e32a796481969f5866b01ef8f11b`
- Packet SHA-256: `06b6292692cc409bbc7f4d476d680cc385dded04ac9ceb988b3e2f148619f392`
- Result: completed; response retained `pending_human_review`
- Observed facts: two matches, both clean audits passed, paired decision delta
  `0.0`, and no first action divergence

The backend caches the response per run so pressing the feedback button again
does not send a duplicate model message. The response is descriptive only and
does not approve a policy change or a new experiment.
