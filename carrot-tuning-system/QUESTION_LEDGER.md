# Carrot tuning system: question-and-answer ledger

This is a compact memory aid, not the authoritative experimental record. Add
new entries as questions arise; link to the detailed document or result that
supports the answer. Read the [continuity guide](./README.md) for full context
before acting on a short answer here.

## Project purpose

### What are we building?

A repeatable local evidence system for testing explicit Kaggriculture carrot
policy parameters, followed later by a Foundry-facing analyst/review layer.
The local evaluator produces the authoritative game evidence; the analyst
helps formulate and explain bounded experiments. See [system overview](./README.md#the-system-being-built).

### Is this an automatic policy optimizer?

It is an automatic bounded calibration system: its inner loop runs an approved
schedule of in-memory parameter candidates and measures their direction of
effect. Its outer evals/reasoning loop interprets accumulated evidence and
proposes the next approved schedule. It does not write target policy source;
the human decides whether to apply a policy change. See [two-loop architecture](./README.md#the-system-being-built) and [boundaries](./README.md#scope-and-non-negotiable-boundaries).

### Does the system modify Kaggriculture?

No. Candidates are one-field, in-memory `CarrotParameters` overrides.
Kaggriculture's policy source, game rules, entry point, and architecture remain
unchanged. See [scope](./README.md#scope-and-non-negotiable-boundaries).

## Evaluation mechanics

### How can a candidate run faster without producing an invalid game result?

The baseline stores state immediately before every decision. The candidate
replays cached observations until its first different action. If no action
differs, it reuses the exact baseline outcome. If one differs, it restores the
pre-decision state and simulates the remaining suffix with the candidate.
Every result is checked against a clean full rerun. See the [checkpoint/resume proof](./README.md#checkpointresume-proof).

### What is a clean audit, and why is it required?

It is a fresh, full candidate simulation using the same seed, seat, opponent,
and configuration. It is the oracle used to verify a cached/replayed result.
A cache result is unusable if it does not match its audit. See [why trust the results](./README.md#why-the-results-are-trustworthy-enough-to-proceed).

### Why do seed and seat both matter?

They control different aspects of a match. A matched suite uses identical game
seeds and runs each candidate from both player seats, so reward deltas are
paired rather than casually compared across different games. See [earned parameter evidence](./README.md#parameter-evidence-earned-so-far).

### Why use a fixed deterministic opponent instead of policy-versus-policy games?

Two carrot policies affect the same market, making their rewards interdependent.
A fixed opponent makes baseline and candidate outcomes comparable under matched
conditions. The current suite uses the deterministic carrot conveyor opponent.
See the parent [parameter perturbation plan](../docs/carrot-parameter-perturbation-plan.md).

### Why can’t we compare the cached evaluator’s time with the old 140-match timing sweep?

They use different execution paths: the old sweep uses the high-level
environment runner and trace machinery, while the evaluator uses a direct step
loop. Compression was not the per-match bottleneck. Compare only like-for-like
direct timing components. See [timing lesson](./README.md#timing-lesson-that-must-not-be-lost) and the parent [timing contract](../docs/timing-contract.md).

## What the experiments found

### Which parameters are probabilities of a positive carrot outcome?

None of the current fields is directly `P(planting is profitable)` or
`P(planting improves final reward)`. The three
`supply_high_given_*_ripe` values are genuine conditional probabilities, but
they estimate the adverse event “opponent supply is high before our sale.” The
remaining belief fields shape the model's three-way low/normal/high future
price distribution; they are not themselves probabilities. Price multipliers
change payoff conditional on a price state, while `seed_opportunity_value` and
`pass_utility` are utility preferences. See the target
[parameter definitions](../../kaggriculture/agents/carrot/shared.py#L56) and
[belief-to-utility calculation](../../kaggriculture/agents/carrot/shared.py#L185).

### Can we establish a calibrated probability of a positive outcome today?

Not yet. The parameters are transparent initial beliefs, but the current
experiments measure policy reward after changing them—not whether a stated
probability matched an observed future outcome. We need to define the outcome
first: for example, a future sale-price category, positive incremental reward
relative to passing at this checkpoint, or final-season reward. These are
different labels and answer different questions.

### What tests would establish it?

Use two complementary tests. First, a stratified observational calibration
study: record each eligible decision's predicted low/normal/high distribution
and its later realized, explicitly defined sale-price label; report Brier score
or calibration curves by ripe-opponent bucket, demand regime, and clamp state.
Second, a causal checkpoint-fork study: restore selected pre-decision states,
force plant versus pass for one turn, then resume the same policy and fixed
opponent to season end. The paired final-reward difference labels whether that
specific action was actually beneficial in that state. Run both branches with
clean audits.

The selection must cover zero, one-to-three, and four-plus visible ripe
opponent carrots; low and high carrot demand; future-shop possible and
impossible; and cases where the price probabilities are clamped. The existing
conveyor suite alone may not cover every regime, so add deterministic opponent
scenarios designed to create those states. Only after these labels exist should
we describe a belief parameter as calibrated toward a positive outcome.

### Did the ±10% parameter screen find anything?

It found that all 22 nonzero parameter directions were inert at that scale for
the conveyor opponent and seeds 42–71 in both seats: zero action divergences,
zero reward changes, and 1,320 passing clean audits. That does not show the
parameters are irrelevant; it shows the perturbations did not cross a decision
threshold. See the [detailed finding](./README.md#parameter-evidence-earned-so-far) and [raw report](../var/results/perturbation-sensitivity-60/summary.json).

### Why did early and late divergence have surprisingly similar timings before?

The apparent comparison mixed a high-level profiling harness with the direct
checkpoint evaluator. Once equivalent direct executions were compared, early
divergence correctly required a long simulator suffix; gzip trace writing was
not the explanation. See [timing lesson](./README.md#timing-lesson-that-must-not-be-lost).

### Should experiment inputs use a universal 0–1 control scale?

Not for the first local runner. The declared values already have different
meanings: some are probabilities, some multipliers, and some coin-scale utility
terms. A universal normalized number would hide those units and can make the
approved envelope harder to audit. The initial experiment specification should
therefore name the parameter and record its actual resolved value. If a later
human-facing control needs normalization, give each parameter a versioned,
monotonic mapping with explicit endpoint semantics, and record both the input
and resolved raw value in the evidence packet.

### Are the carrot policy’s decisions continuous or threshold-based?

Threshold-based. The investment branch plants only when
`plant_utility > pass_utility`. The baseline decision-margin study observed a
minimum margin of +9.72 and median of +39.02, explaining why small changes
often have no visible effect. See the [margin report](../var/results/decision-margin-60/summary.json).

### What happened when `seed_opportunity_value` was changed substantially?

With a baseline mean reward of 6469.02: value 10 was unchanged; 40 produced a
mean paired delta of -52.37; 60 produced -837.73; and 80 produced -1623.28.
All 240 seed-opportunity clean audits passed. On this suite, the evidence
supports retaining 20, not increasing it. See the [coarse preference report](../var/results/coarse-preferences-60/summary.json).

### What happened when `pass_utility` was changed?

`-25` was inert because every observed investment margin was positive. `+25`
suppressed profitable planting in 28 of 60 matched games and produced a mean
paired reward delta of -210.50. See the [coarse preference report](../var/results/coarse-preferences-60/summary.json).

### Does this prove that baseline values are globally optimal?

No. It supports only the specified Kaggriculture revision, deterministic
conveyor opponent, seed/seat suite, and candidate values. Different opponents
or market regimes may exercise the belief/price parameters differently. See
[evidence limits](./README.md#why-the-results-are-trustworthy-enough-to-proceed).

## Foundry and automation

### What is Foundry for in this project?

Eventually, it hosts the outer evals and reasoning loop: evaluate aggregate
experiment evidence, identify uncertainty or missing controls, and explain the
next bounded test schedule. It receives structured evidence packets from the
local inner loop; it is not the game scorer and must not auto-edit the policy.
See [system overview](./README.md#the-system-being-built), [evidence-packet contract](./README.md#evidence-packet-contract-for-the-outer-loop), and the parent [Foundry setup guide](../docs/foundry-project-setup-guide.md).

### Are we provisioning Azure or using credentials now?

No. Local evidence infrastructure comes first. Azure provisioning, cloud
storage, connectors, credentials, model calls, and Foundry deployment require
separate explicit approval. See [immediate next safe step](./README.md#immediate-next-safe-step).

### What can be parallelized safely?

After one immutable baseline cache exists, complete candidate suites can run in
separate processes because each has independent replay, suffix, clean audit,
and report output. Four local workers have been demonstrated safely. Do not
have concurrent workers write the same cache or result file. See [parallelism plan](./README.md#parallelism-plan).

### How are experiments recorded now?

The canonical record is a source-controlled versioned JSON specification,
validated by [schema v1](./experiments/schema/experiment-spec-v1.schema.json).
It pins the target fingerprint, graph, one-field candidate envelope,
deterministic suite, checkpoint/audit requirements, and governance boundaries.
The notebook may explain or load a spec, but it is not the execution authority.
See the [experiment guide](./experiments/README.md) and [current-state snapshot](./docs/current-state-and-next-slice.md).

### Where does the local inner-loop adapter live?

It belongs in the `evaluator/` package in this project, not in a notebook and
not as a rewrite of the parent evaluator. That adapter owns specification and
governance validation, explicit target checks, bounded orchestration, and
evidence-packet writing. It calls the proven parent binding and checkpoint
evaluator only after those checks pass. The current
[`evaluator/runner.py`](./evaluator/runner.py) now reads a requested JSON file
and validates its schema-v1 shape, then binds only the supplied target checkout
and compares its revision, policy hash, and engine hash to the contract. It
then enforces lifecycle authorization and the declared local controls before
baseline-cache or simulator work. Later stages remain separately reviewed.

### How do we test the first adapter stages before adding pytest?

Use the [local adapter workbench](./notebooks/02_local_inner_loop_adapter.ipynb)
to prototype one narrow function, explain and exercise it, and only then move
its reviewed form into the actual Python entry point. The first source check
showed that the historical contract passes schema v1, its recorded target
fingerprint matches the explicit sibling checkout, and a missing required
`suite` or changed engine hash is rejected. The same `run()` call then refuses
the historical record because `historical_reproduction` is archival evidence,
not rerun permission; it does not run a simulator or write a report. We are
not adding tests at that early notebook stage; once the adapter accumulated
several reusable gates, the fast pytest suite below became the complementary
regression check.

The workbench's first function prototype is now `read_spec`: it reads the
historical JSON into a value for the later schema gate and distinguishes an
unreadable file from malformed JSON. It deliberately makes no assertion about
the contract's shape, lifecycle, or target.

`validate_spec_schema` is the second prototype. It self-checks the checked-in
Draft 2020-12 schema, then returns a structured result instead of printing raw
validator diagnostics. The historical contract passes with zero issues; a
missing required `suite` is represented as a `required` rule failure. This
still establishes contract shape only—not lifecycle authorization, target
identity, or a simulator result.

### How do we keep track of the adapter stages?

The [local adapter workbench](./notebooks/02_local_inner_loop_adapter.ipynb)
contains the implementation checklist. A checked item means its notebook
prototype was reviewed and the reusable function was moved into
[`evaluator/runner.py`](./evaluator/runner.py); it does not grant permission to
run an experiment. The reviewed single-entry baseline materializer is now in
the source runner, but the runner's top-level `run()` deliberately does not
orchestrate that side effect yet.

That target prototype now binds the explicit sibling checkout and presents the
expected and observed Git revision, carrot-policy hash, and engine hash. All
three match the historical contract. A nonexistent target path becomes a
structured binding failure; it does not fall back to an ambient directory or
environment-selected target. It awaits review before being transferred into the
reusable runner.

The reviewed target and lifecycle functions have now moved into
[`evaluator/runner.py`](./evaluator/runner.py). The lifecycle function
interprets only the schema-valid lifecycle status: the historical contract
returns “not authorized” because it is archival evidence, while an in-memory
`approved` status returns “authorized for the next local stage.” Neither case
authorizes source-policy mutation or starts a simulator.

The reviewed local-control function now checks the controls that remain after
target identity and lifecycle: actual parameter field/default, a nonempty
unique candidate envelope that excludes the baseline, the fixed opponent,
matched seed/seat suite, checkpoint/audit settings, and governance locks. The
historical contract passes every control. An in-memory candidate envelope that
contains its baseline fails, demonstrating that the check is not merely a
summary.

The reviewed baseline-cache planner derives a deterministic, content-addressed
cache group from the target fingerprint, baseline parameter, suite, and
checkpoint policy. It lists 60 cache paths for the historical suite, but creates
no directory or cache file and does not run a baseline game.

The reviewed cache-state preflight reads only whether those planned paths are
present or missing. It finds 60 missing paths in the current local state. A
present path remains untrusted until a payload-validation stage accepts its
contents; the preflight does not open a cache or materialize a baseline.

The reviewed structural cache-payload validator validates an already-decoded
cache mapping against the target fingerprint and its exact planned seed/seat
match before reuse. Its notebook example is a clearly labeled in-memory
structural shape, not a cache file or simulator result; changing the example's
seed makes validation fail.

The reviewed gzip-reader handoff reads a present cache with the parent
`read_baseline` helper and sends the decoded mapping to that validator. Its
exercise uses temporary synthetic files that are removed before the cell exits:
a matching fixture passes while a decoded wrong-seed fixture fails. The parent
cache module lazy-loads simulator-only imports, so this pure read/write boundary
remains testable without running Kaggriculture.

The reviewed preparation planner turns the cache state and reader results into
an explicit plan. It permits reuse only when a present file decoded and passed
every structural check; every other entry is marked for later materialization
with a reason. The current historical group has zero reusable entries and 60
later-materialization decisions. A compact in-memory mixed example demonstrates
one reuse and two materializations without creating files or running a game.

The reviewed materializer handles exactly one selected missing cache. It
refuses a non-`materialize` action and refuses to overwrite an existing path
before it calls the proven baseline evaluator and writer. Focused guard cases
exercise those two failures without importing or running the simulator. A new
[approved smallest-matched smoke contract](./experiments/approved/carrot_investment/seed_opportunity_baseline_smoke_v1.json)
now passes the runner's schema, target, lifecycle, and local-control gates. It
contains only seed 42, both required seats, and 720 steps; the first selected
entry is seed 42 / seat 0. It does not authorize candidate evaluation or policy
source mutation. The sibling `kaggle-environments` checkout is now installed
editable into the local virtual environment only, leaving both source checkouts
unchanged. The notebook then executed exactly the first selected action, seed
42 / seat 0, once. It produced an ignored local gzip baseline cache with 719
checkpoints and decision/opponent rewards 8849.0 / 8729.0; immediate reopening
passed all five structural/provenance checks. That is cache-infrastructure
evidence only, not a candidate comparison, clean audit, aggregate result, or
policy source change. The next decision still belongs to the human: execute and
reopen the matching seed 42 / seat 1 cache, or stop with this first verified
cache boundary. That action has now been approved and executed: it recorded 719
checkpoints with decision/opponent rewards 8809.0 / 8789.0, and reopening again
passed all five structural/provenance checks. Both seed-42 seats are now valid
reusable caches for this exact approved contract. The next reviewed slice is
bounded candidate checkpoint/replay evaluation with clean audits, not a source
change or candidate-envelope expansion. The exact one-match workflow, audit
stop condition, and proposed notebook progression are documented in the
[candidate evaluation and audit slice](./docs/candidate-evaluation-and-audit-slice.md).

The first notebook gate for that slice now accepts the declared `10.0` override
and rejects undeclared `25.0` before it can read a cache or start a simulator.
It is a notebook prototype pending review and has not been promoted into the
runner; it proves only envelope enforcement, not candidate evidence.

The first fast checkpoint/replay exercise now applies the declared `10.0`
override to seed 42 / seat 0. It found no action divergence and reused the
validated baseline outcome with zero suffix actions. Its status is still
`not-run` for audit, so it is not candidate evidence or a basis for a ranking.
The next required component is the matching clean full rerun and comparison.

That clean rerun has now completed for `10.0`, seed 42, seat 0. Its 719-action
independent full run produced the same 8849.0 / 8729.0 outcome as the fast
result, so this one audit passed. It is audited evidence for one matched game,
not a two-seat or aggregate conclusion. The next bounded action is the same
candidate's fast-result/audit pair for seat 1. That pair and the six remaining
declared pairs have now run as one bounded batch. All eight candidate/seat
audits passed. Values 10.0, 40.0, and 60.0 reused the baseline in both seats;
80.0 diverged at turn 107 and used a 612-action restored suffix in both seats.
These are per-match, one-seed smoke facts—not a mean, ranking, or reason to
revise the historical aggregate conclusion. The notebook now prototypes a
strict local smoke evidence packet: exact candidate/seed/seat coverage and
passing audits are required, per-match fast-path/timing/provenance facts are
retained, and paired aggregates are labeled descriptive only. The visible
`80.0` smoke delta therefore cannot override the historical 60-match result or
authorize a policy change. That evidence shape and its fail-closed immutable
local writer are now in the reusable adapter. A temporary-fixture
write/reopen passed, while a second same-path write was refused; no durable
packet was created. The already-prototyped bounded candidate-evaluation/audit
wrapper is now in the reusable adapter as well. It rejects undeclared values
before cache access and refuses a duplicate audit before simulation. The next
component is orchestration of reviewed components through `run()`, not
additional candidate values or a source change.

### Is the local-adapter notebook finished, and has pytest earned its keep?

Yes. The [local adapter workbench](./notebooks/02_local_inner_loop_adapter.ipynb)
has completed its component-design role: its reviewed loader, target/control
gates, cache boundaries, one-entry materializer, candidate helpers, evidence
model, and immutable writer are all in [`evaluator/runner.py`](./evaluator/runner.py).
It should remain a component record rather than grow into an end-to-end log.

The transition to `run()` exposed a needed stop: the existing
[baseline-only smoke contract](./experiments/approved/carrot_investment/seed_opportunity_baseline_smoke_v1.json)
explicitly says it does not evaluate candidates. Its candidate fields and the
prior interactive notebook approvals are not durable authority for an automatic
full candidate/evidence execution. The next operation needs a new
source-controlled, human-approved candidate-evidence contract and a new
end-to-end-run notebook.

Pytest has now earned its keep because multiple reusable safety gates must stay
aligned as `run()` is wired. It is now the required pre-real-system regression
gate between a completed component workbench and real-system integration. The
fast suite in
[`tests/test_local_inner_loop_adapter.py`](../tests/test_local_inner_loop_adapter.py)
now exercises declared-value and out-of-suite rejection before cache access,
validated-cache refusal, duplicate/mismatched-audit refusal before a clean
rerun, exact evidence coverage, malformed cache/spec input, JSON round-trip,
aggregate safety, and packet-overwrite refusal. Its synthetic records are only
contract fixtures, not game evidence. The default command,
`.venv/bin/python -m pytest -q`, passed 19 tests and deselected the one
explicitly marked simulator regression; actual Kaggriculture games stay in
approved smoke commands or notebooks.

### What is the next execution authority after the baseline-only smoke contract?

The human-approved
[candidate-evidence smoke contract](./experiments/approved/carrot_investment/seed_opportunity_candidate_evidence_smoke_v1.json)
is a separate bounded authorization for exactly seed 42 in seats 0 and 1, 720 steps, and the
already-declared `seed_opportunity_value` values 10, 40, 60, and 80. Its future
operation would require a clean audit for every candidate/match pair and would
permit one immutable local evidence packet only after all audits pass. It does
not authorize a source edit, candidate expansion, a ranking, or a historical
reproduction claim.

The human approved this exact envelope on 2026-09-23. No candidate evaluation
occurred at approval time. The next artifact is the separate end-to-end notebook
that wires this contract through `run()`; it must stop on any failed preflight,
clean audit, or immutable-packet guard. Its
[first preflight-only section](./notebooks/03_spec_driven_smoke_run.ipynb) is
deliberately unrun and does not inspect caches or evaluate a candidate yet.

### How should future notebook agents preserve this workflow?

The reusable `iterative-notebook-authoring` and
`notebook-first-component-development` skills have been revised from this work.
They now give a constrained agent an explicit sequence: inspect the real
workspace and its instructions first; change one bounded concept; separate
model code from presentation; test a meaningful guard before external work;
wait for explicit review before source promotion; and record what actually ran.
They also require an agent to stop when a contract's purpose/lifecycle conflicts
with a technically possible operation, to use temporary artifacts for writer
tests, to avoid fabricating stored notebook output, and to start a new notebook
when the work changes from component design to an approved end-to-end run.

### Can the adapter be debugged directly without a notebook?

Yes. [`evaluator/runner.py`](./evaluator/runner.py) has a small direct command
entry point for its current contract-and-target boundary. From the repository
root, run `PYTHONPATH=src:carrot-tuning-system .venv/bin/python
carrot-tuning-system/evaluator/runner.py <spec-path> --target-root
../kaggriculture`, or use VS Code's Run Python File/debugger with those
arguments. The historical record deliberately stops at lifecycle authorization
and before simulation, making breakpoints in the loader, schema checks,
fingerprint comparison, and lifecycle gate safe.

### Is the historical experiment JSON generated from a notebook?

No. The [historical specification](./experiments/historical/carrot_investment/seed_opportunity_coarse_v1.json)
is the source-controlled canonical record, created from the completed local
coarse-evaluation evidence. The [system-model notebook](./notebooks/01_system_model.ipynb)
and [adapter workbench](./notebooks/02_local_inner_loop_adapter.ipynb) load it
for explanation and direct checks. The real adapter now reads and validates it
before checking the target fingerprint, lifecycle authorization, and local
controls, baseline-cache planning, cache-state inspection, structural
cache-payload validation, gzip cache reading, and cache preparation decisions,
then stops before baseline-cache creation or simulation; neither notebook
generates, replaces, or authorizes the record.

### Why is historical material separate from approved future experiments?

Historical records preserve what was actually run and become regression
oracles; their presence alone must not authorize a rerun. Draft and approved
directories serve different purposes: a draft is still being shaped, while an
approved specification is the only bounded schedule a future runner may
execute. See the [historical seed-opportunity record](./experiments/historical/carrot_investment/seed_opportunity_coarse_v1.json).

### Is step 9.1 of the system-model notebook fully implemented?

It is complete as a design and source-control artifact: schema v1, a validated
historical coarse-bracket spec, a narrative, and a historical notebook exist.
It is not yet a runnable spec-driven evaluator. The next implementation is a
local loader/validator and runner that reads this JSON and calls the proven
parent checkpoint evaluator. See [current status and acceptance criteria](./docs/current-state-and-next-slice.md#the-next-narrow-implementation-slice).

### Where are the diagrams, and what are they for?

The [architecture diagrams](./docs/architecture-diagrams.md) are visual
continuity aids: system authority boundaries, checkpoint/audit sequence,
outer-loop interaction, conceptual entities, multi-graph integration, and
experiment lifecycle. They complement the detailed documents; they do not
override schema or evaluator behavior.

### How should the system-model notebook be read and maintained?

It is an executable explanatory mock, not the execution authority. Each
substantial concept should have a short description of its purpose and limits,
focused code that is the source of truth, and—when raw output would obscure the
idea—a separate presentation-only Markdown view. That view can be cleared or
hidden without changing the specification or evidence. Add comments in response
to real reader confusion, especially to explain safety boundaries and why a
mock does not perform a real policy or evaluator action. See the [notebook
convention](./README.md#how-to-maintain-explanatory-notebooks) and the
[system-model notebook](./notebooks/01_system_model.ipynb).

## Next work

### Why keep tuning carrots if future decisions include other graphs?

Carrots are the first complete vertical slice: they let us prove the evaluator,
audit, evidence packet, and outer reasoning loop against a small transparent
decision graph. The current graph mostly reduces to plant versus do not plant,
so it is not the final strategic model. Future graphs may make a locally sound
carrot decision globally unattractive, which is why every experiment must
distinguish local graph metrics from whole-season reward. See [why carrots remain the first slice](./README.md#why-carrots-remain-the-right-first-vertical-slice).

### How should multiple decision graphs fit into the system?

Each graph owns a bounded action set, eligibility condition, parameters,
explanation, and scenario coverage contract. A higher-level action selector
eventually resolves which graph applies in a state. The local evaluator remains
generic, while graph adapters expose graph-specific margins and calibration
forks. See [graph-aware Foundry architecture](./README.md#architectural-implication-for-the-foundry-project).

### Why is `seed_opportunity_value` especially important for integration?

It is the carrot graph's current shadow price for preserving an owned seed and
its related future option. In a multi-graph agent, a crop-selection,
land-allocation, or higher-level planning graph can eventually provide that
opportunity value from the current farm context. The carrot graph then compares
its own expected return against an explicit alternative rather than a permanent
fixed number. The current result supports static 20 for the tested conveyor
suite only; it does not make 20 a global truth. See [the integration seam](./README.md#seed_opportunity_value-is-the-first-graph-integration-seam).

### What should we implement next?

A versioned, human-approved experiment-spec schema and a local runner in this
directory. Its first smoke specification should reproduce an existing coarse
candidate and clean audit through the explicit target binding. See [immediate next safe step](./README.md#immediate-next-safe-step).

### What should we test after that?

Use a deliberately different fixed opponent or market regime to determine
whether the currently inert belief/price parameters become decision-relevant.
Do not widen values arbitrarily or start open-ended searching without a
predeclared, human-approved specification.
