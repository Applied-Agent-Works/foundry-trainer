# Next-agent handoff: Evidence Analysis Foundry Component Build

## Purpose

This handoff resumes the real, bounded Foundry evidence analyst—not a generic
Foundry setup exercise. The local evaluator remains the authority for target
binding, simulation, audit, immutable evidence, experiment envelopes, and
source-policy changes. Foundry receives only a redacted eligible evidence brief
and returns structured explanation for later human review.

Read [AGENTS.md](../AGENTS.md), [README.md](../README.md), the
[current-state snapshot](./current-state-and-next-slice.md), the
[Foundry transition handoff](./foundry-transition-handoff.md), the
[provisioning decision record](./foundry-provisioning-decision-record.md), and
the relevant Foundry entries in [QUESTION_LEDGER.md](../QUESTION_LEDGER.md)
before changing source or using a cloud-facing tool. The latest stored result
in [Notebook 07](../notebooks/07_foundry_component_build.ipynb) is the
source of truth for current cloud state.

## Current verified state — 2026-09-24

- Foundry account/project: `foundry-trainer-resource` / `foundry-trainer` in
  `rg-foundry-trainer-eastus2`, East US 2.
- Active model deployment: `evidence-analyst-luna-v1`, `gpt-5.6-luna`
  `2026-07-09`, `DataZoneStandard`, capacity 6 (6,000 TPM),
  `Microsoft.DefaultV2`, `NoAutoUpgrade`, no spillover.
- Active prompt agent: no-tools `evidence-analyst`, version 2, using the
  source-controlled `evidence-analyst-v2` instruction contract.
- Active judge agent: no-tools `evidence-analyst-judge`, version 1, using the
  source-controlled `evidence-analyst-judge-v1` contract on the same model
  deployment. One redacted judge invocation passed its deterministic gate with
  overall score `1.0` and remains `pending_human_review`.
- Active proposal-drafter: no-tools `experiment-proposal-drafter`, version 3,
  using `proposal-drafter-v3`; it has been created/reused, read back, and used
  for three redacted boundary tests that all passed.
- One fixed redacted fixture invocation completed. Its response satisfied the
  deterministic local response gate and remains `pending_human_review`.
- A disabled Agent Insights monitor, project-managed Application Insights
  connection, and recorded role preconditions exist. A bounded on-demand
  analysis run failed with Foundry `Forbidden` on a required dependency. The
  trace query itself found the monitor but zero matching insights.

The successful smoke response establishes one governed explanation path. It
does not rank candidates, approve an experiment, mutate source policy, prove
general quality, or authorize additional model invocations.

## Non-negotiable boundaries

- The agent has no tools, connectors, Knowledge index, repository mount, web
  search, simulator access, or source-policy authority.
- Never use a portal, MCP server, Azure CLI, or standalone script as a
  substitute for a reviewed notebook cell that creates, updates, provisions,
  or records a resource. Once the notebook has read back the exact resource,
  application code may use it through a reviewed runtime integration. Any
  runtime request must still preserve the redacted packet, authentication,
  response-gate, and human-review boundaries.
- Treat every model deployment, agent change, invocation, telemetry resource,
  role change, and insight-generation run as a separate bounded action. Make
  the relevant notebook cell idempotent: read/list first, reuse an exact match,
  and refuse drift rather than overwrite or duplicate.
- Package, virtual-environment, and lockfile changes are environment
  mutations. Do not perform them as a prerequisite to notebook design.
- Automated decisions require `review_status: pending_human_review` and a
  visible unchecked Markdown review task until the owner records a disposition.
- Keep Markdown explanation, focused code, and a hideable presentation-only
  card separate. The card consumes actual computed facts; it does not invent
  output or conceal an approval boundary.

## Standing build authority

The owner has already authorized the low-cost, notebook-backed Foundry build
path described in [Carrot's agent instructions](../AGENTS.md). After a
workbench has an exact desired-state record, local guard, declared small token
budget, idempotent apply, and readback predicate, execute that cell rather than
asking for another per-resource approval. This covers the existing-envelope
model deployment, no-tools prompt-agent versions, and small fixed-fixture
Foundry Evaluation artifacts/runs in this project only.

It does **not** cover an IAM/role or authentication change, new Azure service
or region, capacity increase, spillover/auto-upgrade, scheduled monitoring,
destructive cleanup, package/environment mutation, tools/connectors/Knowledge,
or a retry of the deferred Agent Insights investigation. Stop for the owner on
those boundaries.

## Immediate status and stop point

The Agent Insights investigation is now abandoned/deferred. The notebook
records the exact failure, the official seeded-trace reproduction, successful
ingestion, and cleanup. Do not retry it, modify roles, change the connection,
enable scheduled monitoring, or add telemetry resources. The submission
boundary is the deterministic evaluator plus ordinary redacted tracing.

If the owner chooses to defer telemetry, the fixed redacted evaluation and
separate judge-agent smoke path are now complete. The next product-quality
task is human review of their scores and limitations. The deterministic local gate remains authoritative for
packet eligibility, JSON schema, citations, limitations, prohibited fields,
and `pending_human_review`; an LLM judge assesses only groundedness, audit
discipline, uncertainty, boundedness, and usefulness.

That local task is now staged in [Notebook 08](../notebooks/08_foundry_evaluation_workbench.ipynb).
It consumes the actual redacted packet and Notebook 07 response receipt, rather
than invented evaluation inputs, and has a passing simulator-free execution.
The first dataset-targeted evaluation has now completed. The exact evaluator
`evidence-analyst-language-v1` and run
`evalrun_19e057784a3448a0baed96708db3b6f7` were reused on the final rerun. The
one actual row passed with aggregate score `0.9`; dimension scores were 4 for
grounding, 4 for citations, 5 for limitation preservation, 5 for boundedness,
5 for review boundary, and 4 for usefulness. The judge used 2,994 total tokens
and returned no errors. The response and score still require human review.

The current architecture also has a separate judge agent. Notebook 08 created
or reused `evidence-analyst-judge` version 1 on the existing
`evidence-analyst-luna-v1` deployment and invoked it once with the redacted
brief plus recorded analyst response. Response
`resp_08209bffa392b90c006ab5ed1e70388195967de3a666869f9c` passed the
deterministic judge gate with overall score `1.0` and six dimension scores of
5. Its `pending_human_review` state remains open. Do not use the original
direct evaluator run as the current agent architecture.

Notebook 08 also completed its boundary suite: wrong packet binding and
missing review status stopped before agent calls; the valid case scored `1.0`,
and the schema-valid overclaiming case scored `0.46` with boundedness `1`.
Use these results as prompt/contract evidence only; they do not authorize the
reasoning agent or a new experiment.

The optional course-facing second
role is staged in [Notebook 09](../notebooks/09_foundry_orchestration_workbench.ipynb):
it accepts only an analyst response and emits a proposal record that remains
`pending_human_review`. Notebook 08 has completed the one-row dataset-targeted
evaluation. Notebook 09 discovered zero proposal-drafter endpoints, created
version 1, a schema-repair version 2, and final explicit-contract version 3.
The final version was verified with a live readback and passed three redacted
boundary cases: valid handoff, incomplete handoff, and authority injection.

Notebook 09 is now complete for its local and exact low-cost cloud role. It
validates the promoted analyst response shape, constructs the richer reasoning
proposal required by the architecture, rejects five unsafe cases, creates or
reuses the no-tools proposal-drafter, and verifies the live version. Do not
invoke it without a separate redacted fixture invocation review.

The notebook contains source-visible Azure AI Projects SDK cells for the exact
second-agent desired state, read-only discovery, list-first create-or-reuse
behavior, drift refusal, and live readback verification. No model deployment,
runtime, registry, storage, connector, or tool resource was created. The
proposal-drafter endpoint itself is the one authorized no-tools prompt-agent
resource; its version 3 has been verified and invoked only against the three
redacted boundary cases recorded in Notebook 09. The next action is a larger
fixed evaluation set, not an unbounded production-like invocation.

## Delegation protocol

The orchestrator assigns one small task with named files, trusted inputs,
allowed actions, prohibited actions, verification, and a stop point. A
subagent may report facts or propose a patch; it cannot infer authority for
cloud actions, experiment expansion, policy edits, or a later notebook phase.
Do not edit Notebook 07 while another chat owns it; update only assigned
documentation and report conflicts to the owner.
