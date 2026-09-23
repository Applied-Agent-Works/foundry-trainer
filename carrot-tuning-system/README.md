# Carrot tuning system: project orientation and continuity guide

## Read this first

This directory is the beginning of an automatic, evidence-driven system for
experimenting with Kaggriculture's explicit carrot-policy parameters. It is
not an automatic policy editor, an unconstrained optimization loop, or a
replacement for Kaggriculture. Kaggriculture remains the system under test.

Before implementing, evaluating, or proposing an experiment, read this whole
document and then the cited evaluation documents in the parent project. The
detail is intentional. The project owner needs enough reconstruction of the
reasoning to return after an interruption and know what was being built, why
the results are trustworthy, and what the next safe action is.

For a compact index of recurring discussions and their supporting evidence, see
the [question-and-answer ledger](./QUESTION_LEDGER.md).

For a high-level executable mock of the intended inner loop, outer evals and
reasoning loop, and graph-integration seam, see the
[initial system-model notebook](./notebooks/01_system_model.ipynb).

For the step-by-step implementation workbench that exercises the real local
adapter framework, see the
[local inner-loop adapter notebook](./notebooks/02_local_inner_loop_adapter.ipynb).

The source-controlled historical JSON remains the canonical experiment record.
The notebooks load it for explanation and direct-check work; they do not
generate, replace, or authorize that record.

### How to maintain explanatory notebooks

The system-model notebook is a design and teaching artifact, not the canonical
runner contract. Build and revise it one concept at a time: explain the
purpose and boundary in Markdown, place the executable source of truth in a
focused code cell, then use a separate presentation-only cell for a compact,
human-readable summary. The presentation cell may be cleared or hidden without
changing the model or evidence it displays. Comments belong where they answer a
reader's likely “why?” about an invariant, safety boundary, or deliberately
mocked behavior—not on every line. The reusable `iterative-notebook-authoring`
skill preserves this convention for future notebook work.

For a visual reference to the system boundaries, execution sequences, core
records, graph interactions, and experiment lifecycle, see the
[architecture diagrams](./docs/architecture-diagrams.md).

For the exact line between completed local evidence, current architecture
artifacts, and the next real implementation slice, see the
[current-state snapshot](./docs/current-state-and-next-slice.md).

## Why this document is unusually detailed

This project began after a productive period of design and implementation was
interrupted by roughly an hour of pervasive technical problems. The work was
not conceptually unclear; the interruptions consumed the working context that
made the next steps feel obvious. Returning later required redoing useful work
mostly to reconstruct the original train of thought and re-establish trust in
the results.

That is a recurring delivery risk, not a personal failure. Future agents must
treat documentation as continuity infrastructure:

- Explain the reasoning chain, not only the final command and outcome.
- State what was held constant and why that makes a comparison credible.
- Separate measurements from inferences and recommendations.
- Record what was ruled out, including failed assumptions or misleading timing
  comparisons.
- End every substantive document with the concrete next safe step and the
  decision that still belongs to the human.
- Prefer a patient reconstruction over a terse handoff when the owner asks for
  documentation or returns after an interruption.

Use this document as the exemplar for future project documents. A future agent
should make it possible to answer: “What was I trying to prove? Why do I trust
this number? What would make me change my mind? What should I do next?”

## The system being built

The desired system has two deliberately separate planes and two connected
loops. The earlier wording that described only an “experiment control system”
was too narrow: the intended destination is an evidence-driven calibration
cycle, not a collection of unrelated one-off runs.

```text
INNER LOOP: local, fast, deterministic calibration
  bounded parameter candidates
      -> checkpoint replay / restored suffix
      -> matched reward and divergence evidence
      -> clean full-suite audits
      -> evidence packet
                         |
                         v
OUTER LOOP: Foundry eval and reasoning
  evals loop reviews aggregate passes, regressions, coverage, and audit state
      -> passes structured evidence to the reasoning agent
      -> reasoning agent explains what the evidence means and proposes the
         next bounded set of tests
      -> approved experiment specification returns to the inner loop
                         |
                         v
human governs experiment envelopes and source-policy application
```

### Inner loop: deterministic calibration

The inner loop is the high-throughput engine. It can adjust declared policy
parameter values **in memory** across a bounded candidate set and quickly show
whether reward is improving, unchanged, or reversing. It uses the existing
checkpoint/resume mechanism to avoid repeating a baseline prefix when a
candidate follows the same decisions. It still keeps a clean full-suite audit
alongside every fast cached result, so speed is never purchased by silently
lowering the evidence standard.

The word “automatic” here means automatic execution of a bounded candidate
schedule, result aggregation, audit, and evidence packaging. It does not mean
writing a selected value into Kaggriculture source. Parameter changes remain
ephemeral evaluator inputs until a human explicitly applies a reviewed policy
change.

### Outer loop: evals and reasoning

The outer loop interprets the inner-loop evidence rather than game-playing by
intuition. Its evals component asks whether the completed passes were valid and
informative: Were audits clean? Did candidates actually diverge? Is the reward
effect consistent by seat? Did the suite exercise the intended decision
regime? Is an apparent improvement merely noise, a tradeoff, or a regression?

It sends a structured evidence packet—not raw chat history—to a reasoning
agent. The reasoning agent explains its interpretation, identifies what is
still unknown, and proposes the next bounded parameter bracket, opponent
regime, seed suite, or confirmation experiment. That proposal becomes the next
experiment specification after the appropriate human approval. Then the inner
loop runs again.

The Foundry-facing component is eventually intended to host this outer evals
and reasoning loop. It is not the score oracle. The local Kaggriculture
evaluator is the score oracle: it runs the actual target engine under matched
conditions and produces the evidence on which reasoning rests.

This separation prevents a persuasive language-model explanation from being
mistaken for a valid game evaluation, and it prevents an automated experiment
planner from silently changing a policy because a single noisy result looked
promising.

## Scope and non-negotiable boundaries

The system may:

- create and execute locally stored, human-approved bounded parameter
  schedules, including a bracket or directional sequence for one parameter;
- bind explicitly to a Kaggriculture checkout and record its revision/hashes;
- cache baseline simulator states and use checkpoint/resume evaluation;
- perform independent clean reruns as audit oracles;
- generate local evidence reports and Foundry-ready review inputs; and
- recommend a next experiment or a human review decision.

The system must not:

- modify Kaggriculture policy source, game rules, submission entry point, or
  agent architecture on its own;
- treat game constants, such as seed cost or crop yield, as policy parameters;
- use Azure provisioning, cloud storage, credentials, external connectors, or
  model calls until a separate explicit authorization is given;
- conduct an unbounded, unreviewed parameter search, write a value into target
  source, or use interim results to expand a candidate envelope without a new
  approved specification; or
- call a candidate better without a matched local result and its clean audit.

## What has already been demonstrated

The parent project, [foundry-trainer](..), contains a local proof evaluator.
It explicitly binds to the sibling Kaggriculture target rather than relying on
the current working directory or a generic `agents` import. The binding records
the Kaggriculture Git revision plus SHA-256 hashes of the carrot policy and
game engine.

### Checkpoint/resume proof

For a fixed seed, seat, opponent, and configuration, a baseline run stores the
complete JSON-safe simulator state immediately before each decision, the
observation, and the baseline action. A candidate policy then replays stored
observations until its first action divergence.

- If it never diverges, the exact baseline outcome is reused.
- If it diverges, a fresh environment restores the saved pre-action state at
  that divergence and simulates the remaining suffix forward.
- Every fast result is compared with a clean full candidate rerun. A mismatch
  invalidates the fast result.

The implementation corrected a subtle engine behavior: the Kaggle environment
uses the length of its step history to assign the next observation step. State
restore must therefore reconstruct the completed-prefix step placeholders as
well as restore the state itself. Without that, a restored suffix can silently
restart its step counter and yield an invalid comparison.

The proof covers all three required shapes: unchanged/no divergence, an
intentional late divergence, and an intentional early divergence. See the
parent [validation plan](../docs/validation-plan.md) and
[checkpoint evaluator](../src/kaggriculture_eval/checkpoint.py).

### Timing lesson that must not be lost

An earlier timing question revealed that two different execution paths had
been compared accidentally:

- the original 140-match timing sweep uses the high-level environment runner,
  wrappers, and trace writing; and
- the checkpoint evaluator uses a direct manual simulator step loop.

Those are not interchangeable baselines. Compression was not the explanation
for the apparent difference: trace compression occurred after the timed match.
The correct comparison is direct equivalent baseline versus direct clean
candidate versus replay/restore/suffix timings, as specified in the parent
[timing contract](../docs/timing-contract.md). Never compare a cached direct
counterfactual against the older high-level profiling harness and attribute the
difference to simulator work being skipped.

### Parameter evidence earned so far

All results below use a deterministic carrot conveyor opponent, seeds 42–71,
both seats, and 720 turns: 60 matched full-season games per candidate.

1. A fixed ±10% screen evaluated all 22 nonzero explicit parameter directions.
   Every candidate had zero action divergence and zero reward change. All
   1,320 clean audits passed. This did **not** mean the parameters are useless;
   it meant those small moves did not cross a decision threshold for this
   opponent/suite.

2. A read-only margin analysis inspected 40,260 eligible investment-gate
   observations. The baseline always chose plant. The smallest observed
   `plant_utility - pass_utility` margin was +9.72 and the median was +39.02.
   That identified the policy as threshold-based and justified a wider,
   predeclared preference-bracket test.

3. A coarse, clean-audited screen then found:

| One in-memory override | Mean reward | Mean paired delta | Interpretation |
|---|---:|---:|---|
| baseline | 6469.02 | — | Reference result. |
| `seed_opportunity_value=10` | 6469.02 | 0.00 | Still below every relevant threshold. |
| `seed_opportunity_value=40` | 6416.65 | -52.37 | Some profitable planting is suppressed. |
| `seed_opportunity_value=60` | 5631.28 | -837.73 | Substantial harmful suppression. |
| `seed_opportunity_value=80` | 4845.73 | -1623.28 | Harmful in every matched game. |
| `pass_utility=-25` | 6469.02 | 0.00 | No action change because all observed margins were positive. |
| `pass_utility=25` | 6258.52 | -210.50 | Removes profitable planting in 28 of 60 games. |

All 360 coarse-screen clean audits passed. The supported conclusion is narrow:
for this opponent and suite, retain `seed_opportunity_value=20` and
`pass_utility=0`. It is not a claim that those values are globally optimal.

The raw aggregate reports are in the parent ignored `var/` directory:

- [±10% sensitivity result](../var/results/perturbation-sensitivity-60/summary.json)
- [decision-margin result](../var/results/decision-margin-60/summary.json)
- [coarse preference result](../var/results/coarse-preferences-60/summary.json)

## Why carrots remain the right first vertical slice

Carrots are not expected to be the final strategic center of Kaggriculture.
The current carrot graph has one meaningful economic branch: invest/plant or
do not invest/plant. Its belief model, price estimate, and preference values
all eventually feed that single threshold. The recent margin and bracket
experiments made this visible: once a parameter is large enough to move the
plant/pass threshold, it can materially change reward; otherwise it can appear
inert even when it changes an intermediate belief.

That limitation is a reason to use carrots as the first system example, not a
reason to abandon them. The carrot slice is small enough to validate every
layer of the future platform against actual simulator behavior:

```text
interpretable belief graph
  -> explicit parameter(s)
  -> action utility / decision threshold
  -> game consequences
  -> matched counterfactual evaluation
  -> clean audit
  -> outer-loop interpretation and next test proposal
```

Once this workflow is trusted for carrots, it becomes the reusable pattern for
additional decision graphs: crop selection, market sell-versus-hold, fertilizer
use, land expansion, farm-hand allocation, animals, and any later strategic
choice. The eventual agent should not be thought of as one giant parameter
table. It is a collection of decision graphs, each responsible for a bounded
action choice, with a higher-level action selector resolving which graph is
currently relevant.

### Architectural implication for the Foundry project

The Foundry-facing project should be graph-aware from the beginning. An
experiment spec and its evidence packet should identify:

- `decision_graph_id` — for example, `carrot_investment` rather than merely
  “carrot parameters”;
- the graph's available actions and action-selection condition;
- the parameter namespace owned by that graph;
- the local outcome/utility metric and the final-season reward metric;
- the scenarios that exercise the graph; and
- interactions or precedence rules with other graphs.

For carrots, the initial graph contract is intentionally simple:

```text
decision_graph_id: carrot_investment
eligible state: empty/available carrot planting opportunity with a seed
actions: invest-and-plant, preserve-option/do-not-invest
decision statistic: plant_utility - pass_utility
policy result: farmer and market actions consistent with the selected branch
```

### `seed_opportunity_value` is the first graph-integration seam

`seed_opportunity_value` is more than a carrot preference knob. In the current
isolated graph, it is a static shadow price for keeping an already-owned carrot
seed available for a later opportunity. That is why raising it suppresses
planting: the carrot graph is being told that consuming the seed now gives up a
more valuable alternative.

When multiple decision graphs arrive, this is the right kind of parameter to
revisit. It can become a context-aware input representing the value of the
best credible competing use of the seed, tile, money, farmer time, and near
future action capacity. For example, a crop-selection or land-allocation graph
may determine that preserving a tile/seed option is valuable in a particular
state; the carrot-investment graph then incorporates that value instead of
pretending its alternative is always worth a fixed 20 coins.

The ownership boundary matters:

- the carrot graph should still compute its own expected carrot return;
- other graphs or a higher-level planner may provide an explicit opportunity
  value with provenance; and
- the action selector resolves the final competing action, rather than allowing
  a carrot-local static parameter to silently stand in for the whole farm plan.

The present evidence says only that a static value above 20 harmed this
carrot-versus-conveyor suite. It does not say that the correct future,
context-specific opportunity value is always 20. Treat the static parameter as
the first tested interface contract, not as a permanent global constant.

The evaluator stays generic: it evaluates declared candidate parameters and
records outcomes. Graph-specific adapters provide eligibility, explanation,
utility margins, scenario coverage, and any forced-action forks needed for
calibration. The outer evals/reasoning loop compares evidence at both levels:
“Did this graph improve its local decision?” and “Did that improvement help
the whole farm?”

This prevents a future local optimization from being mistaken for a global
policy improvement. A carrot graph can be well-calibrated yet lose to a better
crop, market, or farm-hand graph in the same state. That is a question for the
future graph-selection layer, not a reason to weaken the carrot evidence
standard.

## Why the results are trustworthy enough to proceed

Trust comes from matched controls and independent verification, not from a
single large score.

- Each candidate changes exactly one in-memory `CarrotParameters` field.
- Kaggriculture source is untouched.
- The target revision and relevant source hashes are preserved.
- The opponent, seeds, seats, turn limit, and configuration stay constant.
- Candidate and baseline games are paired by the same seed and seat.
- Cached outcomes are reused only when the candidate takes exactly the same
  action path through the cached baseline observations.
- Any action change restores the actual simulator state and replays the
  remaining game, so downstream market and opponent consequences are present.
- A separate clean full rerun validates every cached outcome.

The evidence is still intentionally bounded. It supports claims only about the
recorded target revision, deterministic conveyor opponent, fixed seed suite,
and specified candidate values. It does not yet establish robustness against
other opponent behaviors, different seed distributions, or later target code.

## Proposed build structure

This new directory will grow into a self-contained project with this shape:

```text
carrot-tuning-system/
  README.md                 # this continuity guide and project charter
  AGENTS.md                 # instructions for future agents
  evaluator/                # reusable local scoring API and cache contracts
  graphs/                   # graph contracts and adapters (carrot first)
  experiments/              # versioned, human-approved experiment specs
  reports/                  # report schemas/templates; generated output ignored
  analyst/                  # Foundry-facing hypothesis/review adapter
  docs/                     # governance, acceptance criteria, deployment plan
  tests/                    # evaluator and report-contract regression tests
```

Generated checkpoints, result payloads, timing logs, and temporary artifacts
must remain disposable and ignored. Experiment specifications, schemas,
documentation, and tests are source-controlled.

For the lifecycle and layout of source-controlled experiment contracts, see
[experiments/README.md](./experiments/README.md).

## The automatic workflow to implement next

The first automated workflow should implement the inner loop through a
deliberately bounded experiment specification, not a free-form request to
“find the best value.” A spec should declare:

- target binding/revision expectations;
- baseline cache identity and suite definition;
- one parameter, old value, and one or more preapproved candidate values;
- deterministic opponent identity and version;
- seeds, seats, steps, and checkpoint interval;
- required metrics and audit rules; and
- a human-owned decision status such as `screen`, `confirm`, or `retain`.

The runner should validate the spec, produce or validate the baseline cache,
evaluate each candidate, run all clean audits, write an immutable report, and
state only a constrained classification: `inert-at-scale`,
`directional-improvement`, `directional-harm`, `mixed-or-inconclusive`, or
`audit-failed`.

The evaluator may automatically run every predeclared candidate in its bounded
schedule. It must not add values beyond that envelope or write a policy file.
The outer evals loop consumes the report and produces a structured assessment;
the reasoning agent then drafts the next specification and explains why. A
human owns envelope approval and all source changes.

### Evidence packet contract for the outer loop

The inner loop should hand the outer loop a compact, machine-readable packet
containing at least:

- experiment-spec identity, target revision/hashes, and evaluator version;
- opponent, seeds, seats, steps, and baseline cache identity;
- every candidate value, paired reward statistics, seat split, win/tie/loss,
  divergence distribution, and suffix length distribution;
- clean-audit counts and any mismatch details;
- baseline-versus-candidate timing components under the timing contract;
- known limitations and whether the experiment met its predeclared purpose;
- a deterministic status that the reasoning agent cannot override.

The reasoning response should be a proposal and explanation, not an authority
to alter a result. Its suggested next experiment must name the hypothesis,
bounded candidate values, controls, success/failure criteria, and why it is
the best next uncertainty to resolve.

## Parallelism plan

There are two kinds of work, with different safety properties.

1. Baseline creation is typically sequential per match because it creates one
   deterministic cache set and needs straightforward progress/recovery. It is
   reusable afterward.
2. After the baseline is immutable, each candidate suite is independent. Its
   cached replay, restored suffix, and clean audit can run in separate local
   processes. The recent 22-candidate and six-candidate screens used four
   workers safely.

Do not parallelize two writers against the same cache or report destination.
Use one immutable baseline cache and separate candidate report files. Choose a
worker count based on local CPU and memory capacity; four workers are proven
here, not a universal requirement.

## Immediate next safe step

The versioned experiment-spec schema and historical coarse-bracket record now
exist. Implement the local **spec loader, validator, and inner-loop runner**
that call the already-proven parent evaluator through an explicit target
binding. Start with the historical record as a human-authorized reproduction
smoke test: it must produce the existing coarse classifications and passing
clean audits. Its output should conform to the evidence-packet contract above.

An intentionally inert framework now lives in [evaluator/](./evaluator/). It defines the
request boundary and the reviewed implementation sequence, but its only entry
point raises `NotImplementedError`: it does not read a specification, bind a
target, call the simulator, write a report, or modify source. The first
implementation task is therefore schema and lifecycle validation, with a
reviewed direct check, before any evaluator call is added.

For these initial stages, use the adapter workbench notebook to exercise the
real Python entry point directly and inspect its result. We are deliberately
not introducing a pytest dependency yet; reusable pytest coverage can follow
once the first behavior beyond the fail-closed framework is implemented.

Do not start Azure provisioning, deploy a Foundry agent, create credentials,
or add unbounded candidate generation yet. The first human decision is whether
the local spec-driven inner-loop workflow reproduces existing evidence clearly
enough to become the stable foundation for the Foundry evals and reasoning
outer loop.
