# Foundry development provisioning decision record

## Purpose and status

This is the source-controlled decision record for the smallest real Foundry
slice of the Carrot Tuning system. It records choices already made by the
owner, the controls those choices require, and the remaining infrastructure and
cost decisions.
It is **not** an Azure deployment request, an `azd` manifest, or permission to
create a model deployment, prompt agent, connection, credential, or storage
resource.

The local [evidence analyst boundary](../analyst/) remains the truth owner for
packet eligibility and output validation. Foundry will receive only its
redacted submitted evidence and return an explanation for review.

## Decisions made

| Decision | Selected development posture | Why |
|---|---|---|
| Foundry project and region | Existing `foundry-trainer` project in **East US 2** | The project already exists there and is the selected location for the first prompt-agent slice. |
| First agent form | **Prompt agent**, not a hosted/container agent | Keeps the first slice close to pay-per-token model use and avoids Container Registry and managed hosting runtime costs. |
| Model candidate | `gpt-5.6-luna`, `2026-07-09`, Data Zone Standard, 1,000 TPM | The analyst role is bounded explanation, not open-ended planning. The model is now deployed with the reviewed lifecycle controls. |
| Capacity fallback | Data Zone Standard (US), only if regional Standard is unavailable | Maintains a U.S. processing boundary without introducing provisioned throughput. Global Standard is not the first choice because the project owner selected an East US 2 posture. |
| Network | Public/basic development access, authenticated through Microsoft Entra ID | The first prompt agent has no tools, connectors, search, knowledge index, private data source, or target-checkout access. Private networking is deferred until a protected dependency justifies its cost and complexity. |
| Persistent dependencies | None beyond the existing Foundry project and model deployment | Do not provision Azure AI Search, Blob Storage, a Container Registry, private endpoints, a capability host, or external connectors for the first slice. |
| Authentication | Microsoft Entra ID; no application keys in source | This keeps callers identifiable and allows least-privilege access. |

## Trace and learning policy

Traces are retained because they are the evidence needed to improve the analyst
without guessing. They support prompt revision, regression-fixture creation,
human-review analysis, and a later deliberate decision about fine-tuning. They
do **not** automatically train a model or authorize a model change.

For the low-volume development phase, record 100% of analyst interactions for
**30 days**. A trace may contain only the following redacted fields:

- packet checksum, packet schema version, and analyst-contract version;
- redacted evidence brief supplied to the agent;
- instruction version, model/deployment identifier, request identifier, and
  timestamp;
- structured analyst response;
- deterministic output-gate result and refusal reason, if any;
- Foundry-evaluation fixture/version and judge results, once evaluations exist;
- later human review disposition: accepted, rejected, or changed.

The following must never enter a trace, evaluation fixture, prompt, or
telemetry field:

- raw simulator checkpoints, caches, traces, or complete per-turn state;
- Kaggriculture source files, arbitrary repository paths, credentials, keys,
  connection strings, tokens, or unredacted system configuration;
- unrestricted conversation history or any content outside the submitted
  redacted evidence boundary.

Only the owner initially receives trace-viewing access. Any later reader must
receive the minimum Foundry and Azure Monitor role required for that purpose.
Before increasing sampling, retention, trace fields, or viewers, inspect the
first batch's data volume and privacy characteristics and record the decision.

## Cost controls

The goal is to make model inference the meaningful variable cost. The selected
prompt-agent posture avoids a container-image registry and managed CPU/memory
runtime. Application Insights / Log Analytics
is still a possible secondary cost if trace ingestion or retention exceeds its
included allowance; trace volume must therefore be reviewed before any policy
expansion.

The owner selected a **$5 monthly ceiling** for this project. The dedicated
resource group now has a resource-group-scoped `foundry-trainer-monthly-5-usd`
Cost Management budget, beginning 2026-10-01 and recurring monthly through
2031-09-30. It emails `dorian.k@hotmail.com` on **actual** cost above 50%,
80%, and 100% of $5. The budget was read back from Azure after creation with
the expected scope, dates, amount, recipient, and enabled thresholds.

A budget alert does not itself stop resources, so the operational response to
a 100% alert is to pause new model invocations and investigate before
continuing. This budget controls the project group, not unrelated resources;
it does not create a model deployment or authorize an invocation.

## RBAC target state

| Principal | Initial minimum role | Scope and purpose |
|---|---|---|
| Owner / release approver | Foundry Owner while creating the first development slice | Create/manage the model deployment and prompt agent; later reduce if appropriate. |
| Development caller | Foundry User | Build/test against the project without broad Azure ownership. |
| Prompt-agent consumer | Foundry Agent Consumer | Invoke only; no change or deployment authority. |
| Trace viewer | Azure Monitor Reader plus required Foundry read access | Inspect the owner-approved, redacted development traces. |

Use Entra identities rather than static keys. Re-evaluate this mapping before
adding another person, service principal, or automated workflow.

## What this record does and does not prove

The selected posture makes the intended development workflow explainable,
bounded, and low-cost. It does not prove current model availability or quota,
create a deployment, or validate real model behavior. Capacity must be checked
immediately before deployment, and the local response gate remains mandatory
after every model response.

## Model-capacity preflight

On 2026-09-24, a read-only capacity and subscription-quota check confirmed
that the current `gpt-5.6-luna` catalog version is `2026-07-09`. In East US 2,
Regional Standard is not available for this model. The selected fallback,
**Data Zone Standard**, reports 333 available capacity units and the
subscription reports all 333 of its Data Zone Standard quota units unused.
Global Standard also reports 250 available/unused units, but remains a
secondary alternative because the owner selected the U.S. Data Zone boundary
when a regional deployment is unavailable. Provisioned options report zero
available capacity and remain out of scope for the $5 development posture.

This result is a point-in-time preflight, not a reservation: capacity and quota
can change before a deployment is requested. It did not create a deployment,
invoke a model, or spend inference tokens.

## Source-visible deployment configuration

The [Evidence Analysis Foundry Component Build](../notebooks/07_foundry_component_build.ipynb)
now records, applies, and verifies the first deployment:
`evidence-analyst-luna-v1` on `foundry-trainer-resource` / `foundry-trainer`,
using `gpt-5.6-luna` version `2026-07-09`, `DataZoneStandard`, and capacity
unit `1` (1,000 TPM). It also records `Microsoft.DefaultV2`, no spillover, and
`NoAutoUpgrade` so a model-version change cannot silently alter the evidence
chain. The configuration is an in-memory Python dataclass; the notebook records
the approved REST apply and the successful readback. It contains no secret.

This makes the deployment reproducible and reviewable in source. The apply was
authorized by the owner and read back as `Succeeded`; it did not create an
agent or invoke a model.

## Resource-group separation: completed and checked

On 2026-09-24, an empty dedicated resource group,
`rg-foundry-trainer-eastus2`, was created in the same subscription and East US
2. It has project, purpose, and $5-ceiling tags. No existing Foundry resource
was altered as part of that action.

Azure's `validateMoveResources` management-plane operation then accepted this
complete move set for the new group:

- the `foundry-trainer-resource` Azure AI Services / Foundry account (its
  `foundry-trainer` project is a child and moves with its parent);
- the `foundry-trainer-resource-logs` Log Analytics workspace;
- the `foundry-trainer-resource-appinsights` Application Insights component;
  and
- its Failure Anomalies smart-detector alert rule.

The owner then approved the move, which completed successfully as one
four-resource Azure operation. The Foundry account and the `foundry-trainer`
child project are now in `rg-foundry-trainer-eastus2`; the old account ID in
`agent-foundary` returns `ResourceNotFound`. The moved account remains an East
US 2 `AIServices` resource with public access enabled, and its project remains
in a succeeded provisioning state.

Post-move checks also confirm that the Log Analytics workspace remains in East
US 2 with its 30-day retention and that the smart-detector alert rule remains
enabled. The Application Insights component initially retained the workspace's
old resource-group ID; that pointer was repaired to the workspace's new ID and
then read back successfully. No telemetry data, model deployment, prompt
agent, tool, connector, Knowledge index, or budget was created by the move.

The move result is trustworthy because Azure's own validator accepted the exact
move set before execution, the move command reached a successful terminal
state, every expected resource is now present in the destination group, the
old account resource is absent, and the only discovered stale reference was
explicitly corrected and reread. The remaining uncertainty is application-level
trace ingestion, which has no agent invocation yet to produce a safe redacted
test trace.

## Next human-owned decision

Review the successful deployment readback in the Evidence Analysis Foundry
Component Build. The next separate review is the prompt-agent definition; no
model invocation, tool, connector, or Knowledge index is authorized yet.
