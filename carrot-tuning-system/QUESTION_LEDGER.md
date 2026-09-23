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
[`evaluator/runner.py`](./evaluator/runner.py) is an intentionally inert
framework: it documents the sequence and refuses to run until each stage is
implemented and reviewed.

### How do we test the first adapter stages before adding pytest?

Use the [local adapter workbench](./notebooks/02_local_inner_loop_adapter.ipynb)
to call the actual Python entry point and present its result separately from
the code. At the current fail-closed stage, the useful assertion is that the
adapter refuses to bind a target, run a simulator, or write a report. We are
not adding a pytest dependency yet; introduce reusable test-suite coverage
after the first real behavior, schema and lifecycle validation, is implemented.

### Is the historical experiment JSON generated from a notebook?

No. The [historical specification](./experiments/historical/carrot_investment/seed_opportunity_coarse_v1.json)
is the source-controlled canonical record, created from the completed local
coarse-evaluation evidence. The [system-model notebook](./notebooks/01_system_model.ipynb)
and [adapter workbench](./notebooks/02_local_inner_loop_adapter.ipynb) load it
for explanation and direct checks. The framework does not read it yet because
its entry point intentionally stops before implementation; neither notebook
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
