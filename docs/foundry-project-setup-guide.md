# Foundry setup guide: Carrot refinement control plane

## Purpose

This document is the implementation guide for turning this repository into a
Microsoft Foundry-supported refinement control plane for Kaggriculture’s carrot
agent. It is not a guide for moving the game, its rules, or its live policy
into Foundry.

The system has two authorities:

```text
Kaggriculture (system under test)            Foundry refinement project
---------------------------------            --------------------------
explicit carrot policy                         inspect bounded evidence
local Kaggriculture simulator                  evaluate analyst behavior
checkpoint/resume counterfactual executor     propose one falsifiable experiment
mechanical outcome + audit truth               explain limits and alternatives
human applies any policy edit                  never edits the target policy
```

The local evaluator is the authority for whether a policy parameter helped.
Foundry is the authority for neither game action selection nor numerical game
outcomes. Its useful job is to make high-quality, reviewable recommendations
from structured evidence.

This distinction is essential: an LLM evaluator may judge whether a refinement
agent followed its instructions, cited evidence, proposed exactly one allowed
parameter, and stated uncertainty. It must not substitute its judgment for the
local matched-simulation result.

## What already exists

The local substrate is in place:

- explicit target binding and source fingerprints in
  [`src/kaggriculture_eval/binding.py`](../src/kaggriculture_eval/binding.py);
- local checkpoint/resume execution in
  [`src/kaggriculture_eval/checkpoint.py`](../src/kaggriculture_eval/checkpoint.py);
- a 140-match timing/trace baseline runner in
  [`scripts/baseline_timing_sweep.py`](../scripts/baseline_timing_sweep.py);
- deterministic late/early suffix demonstration in
  [`scripts/parameter_divergence_demo.py`](../scripts/parameter_divergence_demo.py);
- the required apples-to-apples timing rules in
  [`timing-contract.md`](./timing-contract.md).

Kaggriculture’s authoritative agent and refinement boundaries remain in
[`kaggriculture-agent-architecture.md`](../../kaggriculture/kaggriculture-agent-architecture.md)
and
[`foundry-refinement-architecture.md`](../../kaggriculture/foundry-refinement-architecture.md).

## Non-negotiable guardrails

1. Kaggriculture stays local and independently runnable. Do not package the
   game policy, game rules, or Kaggle submission entry point into the Foundry
   agent.
2. One experiment changes one named `CarrotParameters` field. Fixed game facts,
   seed suite, opponent, and configuration are controls, not tunables.
3. The Foundry agent proposes structured experiments; a human decides whether
   to edit the target parameter.
4. The local evaluator executes the candidate and writes the mechanical
   outcome. Foundry never fabricates or overwrites it.
5. Exact checkpoint reuse requires a deterministic opponent. For a stochastic
   opponent, save/replay opponent actions and label the result
   `frozen-trajectory`; require fresh clean audits separately.
6. Do not provision Azure, deploy a model, create a connection, add a
   credential, or enable a paid evaluation feature until the authorization
   gate below is approved.

## Target architecture

### 1. Local evidence plane

The local evaluator remains the execution plane:

```text
human-selected parameter override
  -> baseline observation replay
  -> no divergence: exact baseline outcome reuse
  -> divergence: checkpoint restore + forward suffix simulation
  -> equivalent direct baseline + clean candidate audit
  -> immutable experiment package
```

The generated package must include the target revision and hashes, complete
configuration, opponent identity/determinism, seeds, seats, parameter old/new
value, divergence distribution, suffix lengths, outcomes, timing contract,
acceptance threshold, and audit status. Keep raw checkpoints/traces disposable
under ignored `var/`; export only the bounded evidence required for review.

### 2. Foundry analyst plane

The first hosted agent should be a **refinement analyst**, not a game player.
It receives a static experiment package and returns a constrained JSON response:

```json
{
  "assessment": "retain_baseline | test_candidate | inconclusive | investigate",
  "evidence_cited": ["seed/seat/metric references"],
  "single_hypothesis": {
    "parameter": "one CarrotParameters field",
    "current_value": 0.30,
    "proposed_value": 0.35,
    "prediction": "measurable local effect"
  },
  "alternative_explanations": ["..."],
  "limits": "..."
}
```

The agent must reject requests to alter game facts, change multiple parameters,
use a different seed suite, or claim that a candidate is successful before a
local clean audit passes.

### 3. Foundry evaluation plane

Foundry evaluations score the **analyst agent’s output**, not Kaggriculture’s
economy. Start with a fixed dataset of historical/local synthetic evidence
packages and expected behavioral rubrics. Evaluate at least:

| Dimension | Pass condition |
|---|---|
| Boundary adherence | Never selects a game action or edits target code. |
| One-change discipline | Names exactly one allowed policy parameter. |
| Evidence grounding | Cites only fields present in the supplied package. |
| Outcome discipline | Does not call a candidate improved without local audit evidence. |
| Uncertainty | Supplies an alternative explanation or marks evidence inconclusive. |
| Human usefulness | Produces a falsifiable experiment and predicted metric direction. |

Use built-in Foundry evaluators for broad instruction/task adherence and safety
where appropriate, supplemented by a domain rubric for the six constraints
above. Treat Foundry evaluation scores as quality telemetry for the analyst;
they do not replace paired rewards, calibration, or audit status.

## Provisioning authorization gate

This guide intentionally stops before Azure mutation. Before running `azd
provision`, `azd up`, model deployment, or Foundry evaluation generation, write
and approve the following decision record:

| Required decision | Why it is needed |
|---|---|
| Azure subscription, owner, region | Determines identity, availability, and residency. |
| Budget and spending limit | Hosted agents, model calls, telemetry, storage, and evaluations can incur cost. |
| Agent/model choice and capacity | Foundry evaluations require an appropriate chat-completion judge model. |
| Data classification and retention | Defines whether experiment packages and traces may leave the local machine. |
| Network posture | Public access versus private-network design changes implementation. |
| Identity/RBAC plan | Determines who can deploy, invoke, inspect traces, and approve changes. |
| Deployment environments | At minimum separate development from any shared/demo environment. |
| Human approval workflow | Defines who can submit a local candidate and promote a retained parameter. |

Until this record exists, the only permitted workflow is the local one.

## Recommended implementation stages

### Stage 0 — stabilize local contracts

Complete before cloud work:

1. Version the experiment-package JSON schema and add schema validation.
2. Add explicit frozen-opponent action recording for stochastic baseline suites.
3. Preserve the equivalent-baseline timing contract in every candidate report.
4. Add calibration labels only when the event can be observed without future
   information leaking into an action-time record.
5. Build a small curated analyst-evaluation dataset from real local reports:
   clear improvement, no divergence, early/late divergence, audit failure,
   multi-parameter violation, and insufficient-evidence cases.

Exit criterion: a reviewer can reproduce any package locally and understand the
candidate/audit conclusion without Foundry.

### Stage 1 — scaffold without deployment

After the authorization gate but before provisioning, add this source layout:

```text
src/refinement_analyst/       hosted analyst code and instructions
  app.py
  contracts.py                request/response schema validation
  policy.py                   boundary and one-change checks
  tests/
  eval.yaml                   Foundry analyst-evaluation intent
  datasets/
    analyst-smoke.jsonl
    analyst-regression.jsonl
  .foundry/
    agent-metadata.yaml       local cache/remote references only
    datasets/
    evaluators/
    suites/
    results/
infra/                        reviewed infrastructure-as-code only
azure.yaml                    deployment manifest, added only when approved
docs/                         ADRs, threat model, retention, runbooks
```

Unit-test the response contract locally with no model invocation. Tests must
cover invalid parameter names, two-parameter proposals, unsupported claims,
missing citations, and `inconclusive` behavior.

### Stage 2 — establish the Foundry project

Once approved, use the Azure Developer CLI (`azd`) path for reproducible
infrastructure. Current Foundry guidance describes a project setup that creates
the Foundry account/project, Application Insights, managed identity, and role
assignments; hosted-agent deployment additionally uses a container registry.
Review the generated infrastructure before provisioning.

Preflight sequence:

1. Verify Azure CLI login, intended subscription, region capacity, and the
   required Contributor/Foundry Owner permissions.
2. Initialize an `azd` project in this repository only after a reviewed
   `azure.yaml`/infrastructure plan exists.
3. Provision a development environment first. Capture the generated project
   endpoint and resource identifiers through `azd env get-values`; do not copy
   secrets into source or manually duplicate azd-owned values.
4. Assign least-privilege roles. The local runner should have no standing
   authority to mutate Kaggriculture, and the hosted analyst should have no
   local filesystem path to the sibling repository.
5. Configure Application Insights retention deliberately. Log request IDs,
   schema version, redacted artifact IDs, and evaluation version—not raw local
   checkpoints by default.

Use a basic hosted-agent setup unless a reviewed need requires custom storage
or a private network. Do not accidentally enable a capability host merely by
turning on hosted-agent support.

### Stage 3 — deploy the analyst, not the simulator

Deploy one stateless analyst agent whose only input is an experiment package and
whose only output is the validated recommendation JSON. It must not have:

- a shell or file tool pointed at Kaggriculture;
- a tool that applies a parameter edit;
- a tool that launches local simulations;
- unrestricted web search, external connectors, or arbitrary storage access.

For the initial integration, a human exports a bounded local evidence package
and submits it to the analyst. Add an automated bridge only after its identity,
authorization, egress, data retention, and failure behavior have been reviewed.

### Stage 4 — evaluate the analyst

After deployment:

1. Create a smoke dataset with representative package requests and explicit
   expected behavior.
2. Run Foundry’s structured agent evaluation against the analyst.
3. Store versioned `eval.yaml`, datasets, evaluator configuration, and
   result summaries under the analyst root’s `.foundry/` folder.
4. Gate analyst releases on boundary adherence and one-change discipline before
   optimizing stylistic quality.
5. Compare analyst versions on the same fixed dataset. A better prose score is
   not sufficient if constraint adherence decreases.

Foundry’s current guidance supports structured `eval.yaml` evaluation after a
hosted agent is deployed. It also distinguishes local unit tests, local/deployed
integration tests, and longer-running structured evaluations. Use all levels:
local tests for contracts, local mechanical evaluation for Kaggriculture, and
Foundry evaluation for analyst quality.

### Stage 5 — controlled operational loop

Only after Stages 0–4 are reliable:

1. Local evaluator produces an evidence package.
2. Foundry analyst returns one recommendation or `inconclusive`.
3. Human reviews it and manually applies one target parameter change.
4. Local checkpoint/resume suite plus clean full-suite audit produce the
   decision evidence.
5. Human records retain/reject/inconclusive; Foundry receives the result later
   as a labeled analyst-quality example.

No automated loop may promote a policy change from analyst output alone.

## Operating runbooks

### Local candidate run

1. Choose one named parameter and predeclare the acceptance threshold.
2. Run the deterministic checkpoint/resume suite.
3. Confirm the equivalent direct baseline and clean candidate audit pass.
4. Export a redacted evidence package with artifact hashes, not raw checkpoint
   cache, unless a reviewer explicitly needs the latter.

### Analyst evaluation run

1. Select the Foundry development environment and analyst metadata overlay.
2. Reuse the pinned smoke/regression dataset and evaluator versions.
3. Run the structured analyst evaluation.
4. Review boundary/adherence failures before quality aggregate scores.
5. Save results with agent version, model/judge deployment, dataset version,
   evaluator version, and retention period.

### Incident/failure behavior

If Foundry is unavailable, an evaluation fails, a model quota is exhausted, or
an analyst response violates its schema, the workflow falls back to the local
evidence loop and records the analyst result as unavailable. It never falls
back to a different external provider and never bypasses the local clean audit.

## Definition of ready

The Foundry project is ready for a first controlled deployment only when:

- the provisioning authorization record is approved;
- local evidence packages are schema-validated and reproducible;
- the hosted analyst has contract tests and no target-policy mutation path;
- analyst evaluation datasets and boundary rubrics are versioned;
- RBAC, retention, logging, budget, region, and cleanup ownership are written
  down; and
- a human can demonstrate retain/reject/inconclusive decisions using local
  evidence even when Foundry is offline.

## Official references

- [Microsoft Foundry hosted agents](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agents)
- [Test a hosted agent](https://learn.microsoft.com/azure/foundry/agents/how-to/test-hosted-agent)
- [Evaluate your AI agents](https://learn.microsoft.com/azure/foundry/observability/how-to/evaluate-agent)
- [Run agent evaluations with the Azure Developer CLI](https://learn.microsoft.com/azure/foundry/observability/how-to/azure-developer-cli-evaluation)
- [Agent evaluators](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/agent-evaluators)
