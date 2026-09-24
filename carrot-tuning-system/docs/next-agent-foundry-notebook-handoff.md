# Next-agent handoff: Evidence Analysis Foundry Component Build

## Immediate objective

Help the owner study the local FrontierWeekHack claims sample and use the
useful, safe patterns from it to set up
[07. Evidence Analysis Foundry Component Build](../notebooks/07_foundry_component_build.ipynb).
This is a documentation and notebook-design task first. It is **not** an
authorization to provision Azure resources, deploy a model, create a Foundry
agent, invoke a model, or run a smoke request.

The desired first remote component is one stateless, no-tools Foundry prompt
agent. It receives only a redacted, locally validated evidence brief and
returns a constrained descriptive response for human review. The local
evaluator remains the only authority for game outcomes, audits, evidence
packets, experiment envelopes, and target-policy changes.

## Required reading order

1. Read the full [project orientation](../README.md) and
   [current-state snapshot](./current-state-and-next-slice.md).
2. Read the full [Foundry transition handoff](./foundry-transition-handoff.md)
   and [provisioning decision record](./foundry-provisioning-decision-record.md).
3. Read the Foundry sections of the [question ledger](../QUESTION_LEDGER.md),
   especially “Foundry and automation.”
4. Inspect [06. Evidence analyst](../notebooks/06_evidence_analyst.ipynb) and
   [07. Evidence Analysis Foundry Component Build](../notebooks/07_foundry_component_build.ipynb).
5. Only then inspect the claims sample described below. The parent
   [Foundry setup guide](../../docs/foundry-project-setup-guide.md) is useful
   reference material, but this handoff and the decision record govern the
   current first slice where they differ.

## Current verified posture

- Foundry account: `foundry-trainer-resource`; project: `foundry-trainer`;
  region: East US 2.
- Its isolated resource group is `rg-foundry-trainer-eastus2`.
- Log Analytics and Application Insights are linked, tracing is intentionally
  limited to redacted fields for 30 days, and a $5 resource-group monthly
  budget alerts the owner at 50%, 80%, and 100%. A budget alert is not an
  automatic stop.
- The model deployment now exists and is verified `Succeeded`; no prompt agent,
  tool, connector, Knowledge index, model call, or model-generated trace exists.
- The first deployment is recorded as:
  `evidence-analyst-luna-v1`, `gpt-5.6-luna` version `2026-07-09`, `OpenAI`,
  `DataZoneStandard`, capacity unit `1` (1,000 TPM),
  `Microsoft.DefaultV2`, `NoAutoUpgrade`, no spillover. Its readback status is
  `Succeeded`.

The deployment readback is point-in-time evidence; capacity is time-sensitive
and must be read again before any future deployment change.

The [local competition reference](../references/foundry-competition/README.md)
records the official entry requirements. They do not require Python,
`azure-identity`, `DefaultAzureCredential`, or direct SDK authentication. Do
not expand the implementation merely to satisfy a presumed contest requirement;
use Azure Identity only if the owner explicitly chooses a Python-to-Foundry
operation that needs it.

## What notebook 07 already establishes

Notebook 07 is titled **Evidence Analysis Foundry Component Build**. Its top
handoff section mirrors this document in notebook form: the target component,
authority map, current posture, safe sequence, sample-repository boundary, and
immediate successor task are visible before any code. Its first component
records and locally validates the proposed deployment configuration, then
renders it as a hideable review card with an unchecked human-review task. It
has no Azure SDK call or apply function.

Component 2 now has its first pure design slice: notebook 07 defines a frozen
read-only discovery plan from the validated desired-state configuration. The
plan names the endpoint and the three intended observations—project identity /
reachability, existing model deployments, and existing prompt agents—while
explicitly allowing no environment change, cloud mutation, model invocation,
or stored cloud output. It does not inspect packages, construct credentials or
clients, or call Azure. Notebook 07 now also includes a separate hideable,
presentation-only descriptive renderer for this in-memory plan; its output is
empty until the notebook is intentionally run. The next agent may refine this
plan after review, but must not add a reader or cloud-result renderer until a
separate action is approved.

Notebook 07 also now stages component 2a: a local SDK prerequisite check and a
separate descriptive renderer. With explicit owner approval, the check read
only local metadata and found `azure-ai-projects 2.7.0` and
`azure-identity 1.25.3`, with both module specs available. It did not import an
Azure client, construct credentials, install packages, contact the network, or
authorize a cloud read. The actual result and its unchecked review task are
recorded in the notebook; the shared environment still has its previously
documented OpenAI/LiteLLM compatibility conflict.

Notebook 07 now also defines and executes the approved pure authenticated-read
request. It recorded the exact target and allowed observations, then read the
project successfully: zero model deployments and zero prompt agents. No Azure
mutation or model invocation occurred. The result and its unchecked review
task are stored in the notebook. The pure deployment-request
construction/validation/presentation slice is now also complete; its unchecked
approval task is the next boundary. No deployment has been attempted.

### Reset note: prior component-2 experiment

A prior delegated experiment installed Foundry SDK packages into the shared
`.venv` and reported a cloud read outside notebook 07. The notebook retained
no actual discovery output, so that report is not evidence for this workbench
and must not be relied on for a later decision. The component-2 notebook edits
have been removed. The shared environment is now outside its previous declared
dependency state: `pip check` reports that `litellm 1.93.2` requires
`openai<3.0.0` while the environment has `openai 3.19.2`. Do not repair,
downgrade, reinstall, or otherwise alter that environment as part of notebook
design. Treat environment recovery as a separate, explicitly approved task.

## FrontierWeekHack claims sample: use and limits

The sample repository is [FrontierWeekHack](/home/experiments/Learning/microsoft/FrontierWeekHack).
Start with:

- [challenge setup README](/home/experiments/Learning/microsoft/FrontierWeekHack/claims/challenge-0-setup/README.md)
- [agent construction example](/home/experiments/Learning/microsoft/FrontierWeekHack/claims/challenge-1-build/agents.py)
- [agent build README](/home/experiments/Learning/microsoft/FrontierWeekHack/claims/challenge-1-build/README.md)
- [deployment example](/home/experiments/Learning/microsoft/FrontierWeekHack/claims/challenge-4-deploy/deploy.py)

It is a **read-only design and SDK-pattern sample**. It may help identify:

- Foundry client construction and identity handling;
- deliberate create/list/readback/verification patterns;
- the distinction between project wiring, model deployment, agent definition,
  invocation, traces, and evaluations; and
- the kind of source-visible setup the course may expect.

It must not be copied as authority. Its tool-using claims agents, action
recommendations, connections, sample credentials, cleanup behavior, and any
run/deploy command are outside this project’s first envelope. Do not modify or
execute the sample repository, copy `.env` values, use its connection strings,
or create its agents.

## Non-negotiable boundaries

- No simulator, source checkout, filesystem path, packet writer, source edit,
  web search, connector, tool, or Knowledge index is available to the first
  prompt agent.
- The model is not a scorer, audit oracle, experiment approver, or policy
  editor.
- Every future automated decision must include
  `review_status: pending_human_review` and a visible unchecked Markdown
  `- [ ]` review task until the owner records a disposition.
- Keep Markdown explanation, focused implementation, and presentation-only
  rendering distinct. Renderer cells may format computed facts only; they must
  carry `hide-input` and `jupyter.source_hidden: true` metadata.
- A model deployment, prompt-agent creation, and fixture invocation are three
  independent approval boundaries. Success at one does not authorize the next.
- Package installation, upgrade/removal, lockfile edit, virtual-environment
  creation/switching, and dependency bootstrap are also side effects. They are
  not included in a request to “set up,” “inspect,” or “design” a notebook.
- When an instruction such as “do that now” could mean framework editing, a
  pure local check, environment change, or cloud read, stop and ask which one
  is authorized. Do not choose the most expansive interpretation.
- Never include secrets, credentials, connection strings, raw simulator state,
  repository contents, or unredacted configuration in a prompt, trace,
  notebook output, fixture, or documentation example.

## Orchestrator and subagent discipline

The owner has designated the context-holding agent as the orchestrator. If the
work is delegated, the orchestrator must first make this handoff and the
repository instructions coherent. Delegate only small, independent tasks such
as “inspect these sample files and report a safe SDK-pattern mapping” or “add
one local notebook framework section.”

Every subagent brief must name: the exact files it owns; trusted inputs; actions
it may perform; actions it must not perform; the required verification; and the
stop point. A subagent may report facts and propose a patch, but cannot infer
permission to broaden scope, perform cloud actions, change target policy,
execute a simulator, or move to a later notebook component. The orchestrator
checks its result against these governing documents before any integration.

## First bounded work package

Work with the owner through the claims sample and then set up the next
non-mutating notebook 07 section. The expected sequence is:

1. Briefly map the sample’s relevant SDK patterns to this project and name the
   sample features that must not transfer.
2. Add explanatory Markdown for notebook 07 component 2: read-only project,
   SDK, deployment, and prompt-agent discovery.
3. Add only the smallest focused code framework needed for that discovery. It
   may validate local configuration, but it must not inspect installed packages,
   construct a credential/client, call Azure, or change the environment until
   the owner selects and approves that exact next action.
4. Add a separate presentation-only renderer only after the discovery output
   shape is known. Do not invent output first.
5. Parse the notebook JSON and update the continuity documents with exactly
   what changed and what did not run.

Stop before a side-effecting cell. For an apply cell, first show the exact
target, model/agent configuration, expected side effect, readback check,
cost/data implications, and the specific unchecked approval it needs.

## Documentation duties

For substantive changes, update [README.md](../README.md),
[current-state-and-next-slice.md](./current-state-and-next-slice.md), and the
relevant Foundry entry in [QUESTION_LEDGER.md](../QUESTION_LEDGER.md). Preserve
the distinction between actual evidence, local validation, cloud readback, and
proposal. If a policy or notebook convention becomes reusable, update the
relevant skills rather than leaving it only in project prose.

## Suggested opening request

> Read `docs/next-agent-foundry-notebook-handoff.md` completely. Inspect the
> FrontierWeekHack claims sample read-only and explain which client/setup
> patterns map safely to the Carrot Tuning evidence analyst. Then set up the
> next non-mutating component of `notebooks/07_foundry_component_build.ipynb`.
> Do not run notebook code, Azure, a Foundry setup skill, dependency bootstrap,
> `pip`/`uv`/environment commands, deploy a model, create an agent, invoke a
> model, use sample credentials, or modify the sample repository without a
> fresh explicit owner approval. If “do that now” is ambiguous, list the
> possible actions and ask me to choose.
