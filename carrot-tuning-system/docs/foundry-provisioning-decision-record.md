# Foundry development provisioning decision record

## Purpose and status

This is the source-controlled decision record for the smallest real Foundry
slice of the Carrot Tuning system. It records choices already made by the
owner, the controls those choices require, and the remaining infrastructure and
cost decisions.
It is not an `azd` manifest and does not authorize arbitrary Azure
infrastructure, identity, credential, or storage changes. Together with the
standing low-cost build authority in [Carrot's agent instructions](../AGENTS.md),
it does authorize reviewed notebook cells to create/reuse the named low-cost
model, no-tools prompt-agent, and fixed-fixture Foundry Evaluation resources
inside this project's existing envelope.

The local [evidence analyst boundary](../analyst/) remains the truth owner for
packet eligibility and output validation. Foundry will receive only its
redacted submitted evidence and return an explanation for review.

## Decisions made

| Decision | Selected development posture | Why |
|---|---|---|
| Foundry project and region | Existing `foundry-trainer` project in **East US 2** | The project already exists there and is the selected location for the first prompt-agent slice. |
| First agent form | **Prompt agent**, not a hosted/container agent | Keeps the first slice close to pay-per-token model use and avoids Container Registry and managed hosting runtime costs. |
| Active model deployment | `gpt-5.6-luna`, `2026-07-09`, Data Zone Standard, 6,000 TPM | The analyst role is bounded explanation, not open-ended planning. Notebook 07 read back the active deployment with reviewed lifecycle controls. |
| Capacity fallback | Data Zone Standard (US), only if regional Standard is unavailable | Maintains a U.S. processing boundary without introducing provisioned throughput. Global Standard is not the first choice because the project owner selected an East US 2 posture. |
| Network | Public/basic development access, authenticated through Microsoft Entra ID | The first prompt agent has no tools, connectors, search, knowledge index, private data source, or target-checkout access. Private networking is deferred until a protected dependency justifies its cost and complexity. |
| Persistent dependencies | Existing Foundry project/model deployment, redacted Application Insights connection, disabled Agent Insights monitor | Do not provision Azure AI Search, Blob Storage, a Container Registry, private endpoints, a capability host, or external connectors for the first slice. |
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
now records, applies, and verifies the active deployment:
`evidence-analyst-luna-v1` on `foundry-trainer-resource` / `foundry-trainer`,
using `gpt-5.6-luna` version `2026-07-09`, `DataZoneStandard`, and capacity
unit `6` (6,000 TPM). It also records `Microsoft.DefaultV2`, no spillover, and
`NoAutoUpgrade` so a model-version change cannot silently alter the evidence
chain. The configuration is an in-memory Python dataclass; the notebook records
the approved REST apply and the successful readback. It contains no secret.

This makes the deployment reproducible and reviewable in source. The apply was
authorized by the owner and read back as `Succeeded`. Notebook 07 also records
no-tools prompt agent `evidence-analyst` version 2 and one accepted fixed
redacted-fixture response. That response remains `pending_human_review`; it
does not authorize another invocation, a policy change, or a new experiment.

Notebook 09 now adds no-tools prompt agent `experiment-proposal-drafter`,
version 3, using the existing `evidence-analyst-luna-v1` deployment and the
source-controlled `proposal-drafter-v3` instructions. Discovery found no
existing endpoint, the list-first apply created the exact version, and an
idempotence rerun reused it. A live version readback verified the model and
instruction text. No model invocation occurred; the proposal-drafter endpoint
was the one additional Azure resource created under the existing low-cost
authority.

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
trace ingestion and Agent Insights analysis, even though ordinary redacted
agent invocation has been proven.

## Current telemetry boundary and next human-owned decision

Notebook 07 now records a disabled Agent Insights monitor, a project-managed
Application Insights connection, and relevant readback roles. Its bounded
on-demand analysis run failed with a Foundry `Forbidden` dependency error and
produced no insights. Review whether to investigate that exact RBAC/dependency
blocker or defer telemetry for the submission. Do not retry the run, alter
roles, or enable scheduled analysis without a new bounded owner decision.

The latest connection readback reports the service-accepted `ApiKey` connection
shape with local authentication enabled on the Application Insights resource;
the secret itself is not stored in source or notebook output. This is a
telemetry-resource posture to review separately from Entra authentication for
Foundry callers, not evidence that an application key was committed.

As a diagnostic comparison, Notebook 07 then followed the Microsoft claims
sample's tracing order with a disposable `carrot-sample-tracing-repro-v1`
agent. The redacted call succeeded and cleanup removed the temporary
conversation and agent version. This confirms that tracing bootstrap and
ordinary agent invocation work in this project; it does not clear the
separate Agent Insights service-side dependency blocker.

The newer Azure SDK sample was also reproduced in Notebook 07 with a
preview-enabled client, fictional spans, Azure Monitor Logs ingestion polling,
and a temporary monitor. Ingestion reached the expected counts, but the run
still returned the same `Forbidden` dependency error. Cleanup readback found
zero temporary resources. No further blind Agent Insights retry is justified.

The Agent Insights investigation is now closed as abandoned/deferred. The
deterministic evidence analyst and ordinary redacted tracing remain the
submission boundary; future quality work should use the staged Foundry
Evaluations/LLM-as-judge workbench instead of this preview analysis path.

## Separate judge-agent readback

Notebook 08 then created the required separation-of-concerns agent
`evidence-analyst-judge`, version 1, using the existing
`evidence-analyst-luna-v1` deployment. It has no tools, connectors, Knowledge
source, repository access, simulator access, or policy authority. One guarded
invocation sent only the redacted evidence brief and recorded Notebook 07
analyst response. Response
`resp_08209bffa392b90c006ab5ed1e70388195967de3a666869f9c` passed the
deterministic judge gate with overall score `1.0` and six dimension scores of
5. Its request hash was
`2b4eadb9ddf1f5d07b0884d51f8b4c1e5bedbec4851fbfff9e9d4915e2bbd1e5`;
review remains pending. This separate agent is now the active LLM-as-judge
path. The earlier direct evaluator run remains historical and must not be
rerun as the current architecture.

## Foundry Evaluation readback

The first small fixed-fixture evaluation is complete and remains within the
standing low-cost authority. Notebook 08 reused the exact evaluator and run
after its idempotent rerun: evaluator `evidence-analyst-language-v1`, run
`evalrun_19e057784a3448a0baed96708db3b6f7`, one dataset row, one passed item,
zero errors, and 2,994 total judge tokens. The aggregate score was `0.9`; the
dimension scores were grounding 4, citation discipline 4, limitation
preservation 5, boundedness 5, review boundary 5, and usefulness 4.

The actual inputs were the redacted Carrot packet and recorded Notebook 07
response. The run evaluated pre-existing output and did not invoke the agent
again. The result is still pending human review and does not authorize a
reasoning-agent deployment, a new experiment, or a source-policy change.

Notebook 08 then created/reused the distinct no-tools judge agent
`evidence-analyst-judge`, version 1, on the existing deployment and invoked it
once with the redacted brief/analyst-response pair. Response
`resp_08209bffa392b90c006ab5ed1e70388195967de3a666869f9c` passed the local
judge-response gate with overall score `1.0` and six dimension scores of 5.
The judge result remains `pending_human_review`; it is language-quality
evidence, not game or policy authority.

The boundary suite then rejected wrong packet binding and missing review status
before agent calls. It sent two schema-valid cases through the separate judge:
the valid response scored `1.0`, while the overclaiming response scored `0.46`
with boundedness `1` and limitation preservation `2`. No additional agent or
model deployment was created for these fixed cases.
