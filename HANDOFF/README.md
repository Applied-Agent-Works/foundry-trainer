# Handoff: Kaggriculture refinement trainer

## Why this project exists

This repository is the future **refinement control plane** for the local
Kaggriculture carrot agent. Its initial purpose is to make a rapid, evidence
based tuning loop for the agent's explicit named policy parameters (for
example, the carrot decision model's belief and utility values).

It is not a Kaggriculture submission, a replacement game engine, or a live
game-playing agent. Kaggriculture remains the system under test.

The long-term loop is:

```text
baseline local match suite
  -> cache traces and checkpointable simulator states
  -> propose one named parameter candidate
  -> cheaply find each match's first changed action
  -> reuse its unchanged prefix and simulate only its suffix
  -> aggregate evidence and accept, reject, or mark inconclusive
  -> periodically run a clean full-suite audit
```

The phrase "regression from the end" describes reuse of an already-completed
baseline trajectory. The actual counterfactual simulator still runs forward,
from the first changed action to the end of the match.

## Source project and authoritative documents

The sibling project is `../kaggriculture`. Before implementing policy-specific
logic, read:

1. `../kaggriculture/AGENTS.md`
2. `../kaggriculture/kaggriculture-agent-architecture.md`
3. `../kaggriculture/carrot-decision-network.md`
4. `../kaggriculture/foundry-refinement-architecture.md`

The last document is the current architecture for this project. It states the
control-plane boundary and is the source of truth until its relevant content
is deliberately migrated here.

## Included fixture to adopt

This handoff includes a source copy of the disposable fixture:

```text
HANDOFF/memoization-experiment/
```

The original remains in `../kaggriculture/memoization-experiment/` as its
provenance source. The included copy contains:

- `profile_step8.py`: local match timing, trace capture, and trace validation.
- `kaggriculture_playground.ipynb`: experimental matched evaluation notebook.
- `README.md`: existing invocation notes.
- `results/` and `trace-cache/`: generated, ignored artifacts.

Do not modify Kaggriculture's policy as part of adapting this fixture. First
establish a clean project layout here and explicitly preserve the provenance of
this copied material. Generated results and caches should remain disposable and
ignored by Git.

The existing harness has been verified to:

- run local reproducible matches using fixed seeds and both player seats;
- separately measure decision, opponent, and simulator/framework time;
- record compressed decision observation/action traces;
- replay a trace against a candidate policy to report exact reuse or the first
  divergent action; and
- retain the baseline outcome if every candidate action matches.

It does **not** yet checkpoint or restore simulator state. That is the first
substantive implementation milestone.

## Evaluation model and exactness rules

For a baseline match, retain enough data to restore the environment immediately
before every candidate-policy decision (or a documented checkpoint interval),
including the state, configuration, seed, player positions, and the action
history needed to reach that state.

For a candidate parameter change, evaluate the candidate against recorded
pre-action observations in chronological order:

1. If its action equals the recorded action, the prefix remains valid.
2. At the first unequal action, restore the state immediately before that
   action and simulate the remaining suffix forward.
3. If no action differs, reuse the recorded final outcome exactly.

Late divergence should be cheap because it simulates only a short suffix.
Early divergence should cost nearly a full match. Report the distribution of
first-divergence turns across the suite; do not call a candidate "late-stage"
from one favorable game.

Exact reuse requires a fixed game version/configuration/seed and a deterministic
opponent. The built-in random opponent is not deterministic across fresh runs.
Recording and replaying its actions creates a useful *frozen-trajectory*
counterfactual, but it does not test a new random draw. Clean full-suite audits
are therefore required to test fresh stochastic behavior and to refresh stale
caches.

## Initial data and experiment contract

Every candidate evaluation should record:

- baseline source revision and candidate source revision;
- one parameter name, its old value, and its new value;
- fixed configuration, opponent, seeds, and player positions;
- cache/schema/engine version and whether each result is reused or suffix-run;
- first-divergence turn and suffix length for every match;
- final reward, advantage, win/loss, status, lifecycle failures, and decision
  counts;
- available calibration metrics separately from economic reward;
- predeclared acceptance threshold and the final keep/reject/inconclusive
  conclusion; and
- audit-suite status.

One candidate changes one named belief or policy preference. Do not alter game
facts, several parameters at once, seeds, or the opponent while evaluating a
candidate.

## Boundaries and prohibitions

- The Kaggriculture agent must remain local, readable, and independent of
  Foundry, network access, LLMs, JEV, and cloud credentials during a match.
- This project must not mutate the target policy automatically. A human chooses
  whether to apply a proposed parameter change; local matched evidence decides
  whether it is supported.
- Do not provision Azure resources, add credentials, call external models,
  evaluators, storage, search, or connectors. No API keys, tokens, usage
  allocation, or spending budget have been authorized.
- An LLM is optional and advisory: useful for periodic hypothesis generation
  or explaining surprising aggregate evidence, never required to score every
  tuning iteration.
- Preserve reproducibility, explicit provenance, and the option to delete the
  experimental cache without affecting Kaggriculture.

## Suggested first task

Organize a local-only package in this repository around the existing fixture,
then implement and validate simulator-state checkpoint/resume for one fixed,
deterministic opponent and a small seed/seat suite. Prove that:

1. no-divergence candidates reproduce the baseline result without simulation;
2. a deliberately late parameter divergence resumes at the saved turn and
   matches a clean full rerun's outcome; and
3. an early divergence appropriately simulates most of the match.

Only after that proof should the trainer grow candidate-search, Foundry-hosted
agent, or LLM-advisory capabilities.
