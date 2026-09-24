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

## Verified starting state

At the handoff, the local machine has Azure CLI, `azd`, and the Foundry agent
extensions installed and authenticated to a Pay-As-You-Go subscription. The
owner has created the `foundry-trainer` project at
`https://foundry-trainer-resource.services.ai.azure.com/api/projects/foundry-trainer`.
A read-only Foundry MCP query confirmed that the project is reachable and had
no registered agents at the time of inspection. This repository has no
`azure.yaml`, Foundry deployment manifest, infrastructure, applied
model-deployment request, cloud connection, credential, or prompt agent. It
now has a local source-controlled `analyst/` boundary package and a successful
`evidence-analyst-luna-v1` model deployment recorded in [07. Evidence Analysis
Foundry Component Build](../notebooks/07_foundry_component_build.ipynb), but no
prompt agent or model client. The environment is therefore ready to begin
prompt-agent setup.

This is important for modifiability: the evaluator and the local analyst
boundary are normal source-controlled Python. The deployable Foundry analyst
has not been created, so there is no remote system to modify or imply as
existing before a reviewed source configuration and explicit cloud approval
exist.

## Provisional model and response boundary

The reviewed local workbench records `gpt-5.6-luna` as the provisional first
candidate for the constrained evidence-analyst role. Its catalog release is
2026-07-09, its lifecycle is general availability, and its published retirement
date is 2028-01-11. This is a model-selection hypothesis for a bounded,
descriptive task—not a deployment request or an assertion that capacity exists
in a particular region. A read-only Azure deployment check found no existing
model deployment in the project resource.

The provisional source-controlled instruction permits only explanation of
packet-backed facts. It has no tools, repository mount, web search, simulator
access, or source-edit authority. The local response gate binds every response
to a submitted packet checksum, preserves the evidence-brief limitations,
requires permitted citations and `pending_human_review`, and refuses unknown
fields such as a proposed candidate value. This proves contract shape and hard
stops locally; it does not prove a model's language grounding. Fixed-fixture
Foundry evaluations and an LLM-as-judge rubric remain the later language-quality
check.

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

## Required editable system shape

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
    tests/                  # simulator-free contract and guard tests
    datasets/               # small redacted analyst smoke/regression inputs
  notebooks/
    06_evidence_analyst.ipynb  # reviewed local analyst boundary and teaching history
    07_foundry_component_build.ipynb  # desired state and reviewed cloud steps
  docs/                     # decision record, runbook, retention/RBAC notes
```

The first agent API should accept a packet plus an explicit schema/version and
return only a structured descriptive response: assessment, packet-backed
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
Standard is unavailable. The exact smallest supported Data Zone Standard
deployment configuration was approved, applied, and read back successfully in
notebook 07. Model invocation and prompt-agent creation remain separate later
approvals.

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

Use a new focused conversation for the Foundry phase. Its immediate task is
recorded in the [next-agent Foundry notebook handoff](./next-agent-foundry-notebook-handoff.md):
read the governing documents, study the local FrontierWeekHack claims sample
without running or changing it, and set up notebook 07 one reviewable component
at a time. The parent [Foundry setup guide](../../docs/foundry-project-setup-guide.md)
is a reference, not permission to provision.

Suggested opening request:

> Read `carrot-tuning-system/docs/next-agent-foundry-notebook-handoff.md`.
> Use the FrontierWeekHack claims repository only as a read-only SDK-pattern
> sample, then extend `07_foundry_component_build.ipynb` with the next
> reviewable, non-mutating Foundry component. Preserve the no-tools prompt-agent
> boundary and do not deploy, create an agent, invoke a model, or alter Azure
> without a fresh explicit approval. Keep the local evaluator as the only
> scoring authority.

For the submission window, prioritize the smallest deployable vertical slice
over extra local tuning. Keep any work on the farming agent in a separate
bounded experiment notebook/contract so it can continue during the following
week without destabilizing the Foundry submission.

The model deployment is now applied and verified. Prompt-agent creation, fixture
invocation, and analyst-behavior evaluation remain separate reviewed actions.
Each must be recorded with its actual result; none should be represented as
completed in advance.
