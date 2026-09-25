# Foundry transition handoff

## Purpose of the next phase

The local evaluator is complete for its current bounded role. It is the
mechanical authority for target binding, cache validation, checkpoint/replay
evaluation, clean audit, immutable evidence writing, and the narrow planning
operations documented in [current-state-and-next-slice.md](./current-state-and-next-slice.md).

The next phase is **not** a broader carrot experiment. It is to build the
first real Microsoft Foundry component: a stateless refinement analyst. The
analyst receives a bounded, immutable local evidence packet and returns a
validated, reviewable recommendation. It never runs Kaggriculture, scores a
game, writes a cache or packet, edits target policy, expands an experiment, or
has a tool that can reach the sibling source checkout.

The earlier [Foundry setup guide](../../docs/foundry-project-setup-guide.md)
remains the architectural plan. This handoff records the actual starting state
and the editable seams required to turn that plan into a deployed development
system.

## Current verified state

The local machine is authenticated to the owner-created `foundry-trainer`
project at
`https://foundry-trainer-resource.services.ai.azure.com/api/projects/foundry-trainer`.
The latest recorded [Notebook 07](../notebooks/07_foundry_component_build.ipynb)
readbacks show an active `evidence-analyst-luna-v1` deployment:
`gpt-5.6-luna` `2026-07-09`, `DataZoneStandard`, capacity 6 (6,000 TPM),
`Microsoft.DefaultV2`, and `NoAutoUpgrade`. They also show no-tools prompt
agent `evidence-analyst`, version 2, using the source-controlled
`evidence-analyst-v2` contract, plus no-tools prompt agent
`experiment-proposal-drafter`, version 3, using the source-controlled
`proposal-drafter-v3` instructions and the same model deployment. Notebook 08
also created no-tools `evidence-analyst-judge`, version 1, and invoked it once
with a redacted brief/analyst-response pair; its deterministic gate passed
overall score `1.0` with `pending_human_review`.

One fixed redacted evidence brief completed successfully and passed the local
deterministic response gate. Its `pending_human_review` state remains open; it
does not authorize a policy change or another invocation. The telemetry path
has a disabled Agent Insights monitor, an Application Insights project
connection, and prerequisite role readbacks, but a bounded on-demand insights
run failed with a Foundry `Forbidden` dependency error. That blocker—not agent
creation—is the current cloud stop point.

Notebook 07 also ran a disposable reproduction of the Microsoft claims
monitor sample. Temporary agent `carrot-sample-tracing-repro-v1` returned a
redacted response and was deleted, along with its conversation. That green
sample-path result isolates the remaining red failure to Agent Insights
analysis rather than ordinary tracing or agent invocation.

It subsequently reproduced the newer Azure SDK Agent Insights sample: a
temporary external agent emitted fictional spans, Logs Query confirmed
ingestion, and a preview-enabled Agent Insights monitor was run. That run
returned the same dependency `Forbidden` after ingestion, and cleanup left no
temporary agents or monitors. The current blocker is therefore independent of
our real-agent trace shape and ordinary App Insights ingestion.

The Agent Insights investigation is now closed as abandoned/deferred. Do not
retry the preview run, change roles, or add telemetry resources. The supported
next quality path is the staged Foundry Evaluations/LLM-as-judge workbench,
with the deterministic local gate remaining authoritative.

### Standing low-cost build authority

The owner has authorized agents to execute the reviewed, idempotent notebook
cells that build this project's low-cost Foundry path: no-tools prompt-agent
versions, model deployments at or below the existing 6,000-TPM Data Zone
Standard envelope, and small fixed-fixture Foundry Evaluation artifacts/runs.
The exact rules and exclusions live in [Carrot's agent instructions](../AGENTS.md).
This removes the earlier bottleneck where an agent could design a notebook but
felt unable to run its declared resource cell. It does not authorize identity
or authentication changes, new Azure service types, capacity expansion,
scheduled monitoring, or the deferred Agent Insights repair.

The evaluator and local `analyst/` boundary remain normal source-controlled
Python. The prompt-agent definition, local response gate, and notebook action
history make the remote slice modifiable without granting it simulator, source,
or policy authority.

## Model and response boundary

The reviewed local workbench records `gpt-5.6-luna` as the selected first
model for the constrained evidence-analyst role. Its catalog release is
2026-07-09, its lifecycle is general availability, and its published retirement
date is 2028-01-11. This is a model-selection hypothesis for a bounded,
descriptive task—not a deployment request or an assertion that capacity exists
in a particular region. The deployment is now active as
`evidence-analyst-luna-v1` with the verified DataZone Standard capacity
recorded above.

The provisional source-controlled instruction permits only explanation of
packet-backed facts. It has no tools, repository mount, web search, simulator
access, or source-edit authority. The local response gate binds every response
to a submitted packet checksum, preserves the evidence-brief limitations,
requires permitted citations and `pending_human_review`, and refuses unknown
fields such as a proposed candidate value. This proves contract shape and hard
stops locally; it does not prove a model's language grounding. The single
accepted fixture is a smoke result. Fixed-fixture Foundry evaluations and an
LLM-as-judge rubric remain the later language-quality check.

## Promoted local analyst boundary

The reviewed workbench behavior is now reusable source in
[`analyst/contracts.py`](../analyst/contracts.py),
[`analyst/policy.py`](../analyst/policy.py), and
[`analyst/instructions.py`](../analyst/instructions.py). The package has no
Foundry client or entry point by design: adding a cloud integration would be a
separate reviewed step, not a mechanically equivalent promotion. The notebook imports the package to
replay the accepted smoke-packet and unknown-field-refusal cases, while the
parent fast suite has eight simulator-free source tests. These checks prove
boundary preservation; they do not invoke a model or establish hosted behavior.

## Required editable system shape and current location

Build the first Foundry component as a **prompt agent**, not a Python hosted
agent. Keep its instructions, local gates, and deployment configuration in
reviewed source/notebook artifacts rather than portal-only prompts or untracked
configuration. Do not create a hosted `main.py`, container registry, compute
runtime, `azure.yaml`, or `infra/` directory merely to deploy this first model.

```text
carrot-tuning-system/
  analyst/
    instructions.py         # versioned analyst instructions
    contracts.py            # request/response JSON validation
    policy.py               # one-change and evidence-boundary checks
  tests/test_evidence_analyst.py  # simulator-free contract and guard tests
  notebooks/08_foundry_evaluation_workbench.ipynb  # fixed redacted fixtures/rubric
  notebooks/09_foundry_orchestration_workbench.ipynb  # optional role handoff
  notebooks/
    06_evidence_analyst.ipynb  # reviewed local analyst boundary and teaching history
    07_foundry_component_build.ipynb  # desired state and reviewed cloud steps
  docs/                     # decision record, runbook, retention/RBAC notes
```

The first agent API accepts a packet plus an explicit schema/version and
returns only a structured descriptive response: assessment, packet-backed
citations, limitations, and a `pending_human_review` state. It has no
experiment-planning or governance-review authority. Local unit tests must
reject unknown fields, claims not supported by an audit-passing packet, missing
citations, dropped limitations, and requests to change target source or invoke
a simulator.

The deliberate design choice is that Foundry receives a submitted, redacted
packet, not a filesystem path. The agent has no local repository mount, shell,
web-search tool, arbitrary connector, or policy-edit tool. That preserves the
local evaluator as the score authority and makes the remote component safely
replaceable or redeployable from source.

Foundry Evaluations will assess this analyst workflow with a fixed, redacted
fixture set. Deterministic tests establish contract compliance and hard-stop
behavior; a custom LLM-as-judge rubric assesses response grounding, audit
discipline, uncertainty, boundedness, and usefulness. The judge is not the
game evaluator: it never determines simulator outcomes, audit status, or a
policy value. Application Insights/OpenTelemetry will record redacted packet
identity, version, role transitions, decision status, and refusal reasons for
debugging and later trace-based evaluation.

## What was decided, and what remains blocked

The current [development provisioning decision record](./foundry-provisioning-decision-record.md)
now resolves the project/region, low-cost prompt-agent posture, redacted trace
policy, network posture, model/fallback, intended RBAC, $5 monthly
ceiling, and dedicated `rg-foundry-trainer-eastus2` resource group. The move
and the required Application Insights workspace-reference repair are complete.
The `foundry-trainer-monthly-5-usd` budget is live with actual-cost alerts at
50%, 80%, and 100% sent to the owner. A read-only model-capacity check found
East US 2 Data Zone Standard available for `gpt-5.6-luna` while Regional
Standard is unavailable. Notebook 07 records the approved deployment,
prompt-agent version 2, and one fixed-fixture invocation as separate completed
boundaries. The still-open review boundary is the accepted response; the
current technical blocker is the bounded Agent Insights run.

## Delivery horizons and scope protection

There are two different deadlines, and they must not be conflated:

1. **Foundry project submission: tonight.** The submission should demonstrate
   a real, modifiable control-plane vertical slice: the trusted local evidence
   boundary, a source-controlled no-tools prompt-agent implementation/deployment
   plan, and—once the exact deployment record is approved—a development deployment
   with a bounded smoke interaction. The submission does not need a broader
   carrot experiment, a contextual graph implementation, or a policy change.
2. **Farming-agent work: one week.** The actual agent, additional scenarios,
   graph integration, and parameter tuning have a later iteration window. They
   should improve the local evidence plane only through new bounded contracts
   and clean audits; they are not a reason to rush placeholder model logic into
   the Foundry project.

The submission can therefore be honest and useful without claiming that the
prompt agent has tuned the farmer. Foundry demonstrates governed evidence
interpretation; the local evaluator demonstrates game mechanics; later farming
work uses the same contracts to improve the agent deliberately.

## Recommended next conversation

Use a focused conversation only after reading the current
[next-agent Foundry notebook handoff](./next-agent-foundry-notebook-handoff.md).
The parent [Foundry setup guide](../../docs/foundry-project-setup-guide.md) is
a reference, not an alternative action surface. The next agent should not
restart component 2, recreate the analyst, or repeat the completed
evaluation/judge runs. It may prepare a human-review packet for the existing
scores, or invoke the verified proposal-drafter only after a new redacted
fixture invocation review. The deferred telemetry permission blocker still
requires a new explicit owner decision.

For the submission window, prioritize the smallest deployable vertical slice
over extra local tuning. Keep any work on the farming agent in a separate
bounded experiment notebook/contract so it can continue during the following
week without destabilizing the Foundry submission.

The model deployment, prompt-agent creation, and one fixture invocation were
separate reviewed actions and have recorded actual results. Preserve that
separation for every future mutation and do not represent a failed telemetry
operation as successful trace analysis.
