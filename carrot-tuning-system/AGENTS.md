# Future-agent continuity requirements

Read [README.md](./README.md) and the
[current-state snapshot](./docs/current-state-and-next-slice.md) in full before
working in this directory.

## Canonical notebook session and section contract

Every explanatory or cloud-component notebook in this project follows one
unambiguous pattern. The opening Markdown cell states the objective, current
state, autonomy envelope, non-goals, checklist, and later human decisions.
Each unique section then contains, in order: a Markdown description of its
purpose/inputs/output/boundary; one focused source-of-truth code cell with
comments only for non-obvious invariants and safety choices; a separate
hideable presentation-only Markdown card; and success/guard evidence. Every
code cell runs in dependency order and retains its real output. No cell may be
silently unrun or replaced by a side-channel action, and no subsection label
may be reused.

If a request is ambiguous between editing, a local check, an environment
change, a cloud read, or a cloud mutation, restate those choices and stop for
the owner's selection. If a cell fails, preserve its exact actionable error,
classify it, make the smallest in-scope fix, and rerun that same cell. Missing
packages are prerequisites, not installation permission; cloud errors are not
retry or fallback permission. Any scope, contract, cost, security, data,
source-policy, or external-state change becomes a visible unchecked human
decision and is recorded in the continuity documents.

For Foundry, Azure, prompt-agent, model, deployment, external-connection, or
analyst work, also read the [Foundry transition handoff](./docs/foundry-transition-handoff.md)
and the [next-agent Foundry notebook handoff](./docs/next-agent-foundry-notebook-handoff.md)
in full before changing source or using a cloud-facing tool. Do not treat local
Azure CLI authentication or installed tooling as permission to provision,
deploy, create an agent, or invoke a model.

### Notebook-only Foundry phase

When a task is limited to designing, documenting, or staging a Foundry notebook
component, do not invoke a generic Foundry setup/deployment workflow or any
dependency-bootstrap script. Installing, upgrading, removing, or repairing a
package; creating or switching a virtual environment; and changing a lockfile
are environment mutations, even when the package would later support a
read-only cloud operation. They require their own explicit approval and a
source-visible compatibility plan.

Treat a missing dependency as a recorded prerequisite, not a problem to solve
automatically. If the owner says “do that now” near a boundary, restate the
candidate actions—edit framework, run a pure local check, change environment,
or make an authenticated cloud read—and obtain a choice before acting. A cloud
read must run through the reviewed notebook cell and retain a redacted actual
output; do not perform it in a side channel and leave the notebook unexecuted.

## Notebook as the Azure action authority

For this project, the reviewed notebook is the authoritative action surface
for every Azure operation. Approved reads, creates, updates, deployments,
agent operations, and invocations must be represented by notebook cells and
their actual outputs must be recorded there. Do not fall back to Foundry MCP,
Azure CLI, a standalone SDK script, or a portal action when a notebook cell is
missing or broken. Repair the notebook cell, review its exact target and
side-effect boundary, then run that cell. A command used during diagnosis is
not a substitute for notebook evidence and must not be presented as if the
notebook performed it.

An explicit owner request to create an Azure resource is sufficient authority
for that exact creation when the notebook documents the target, expected side
effect, cost/data implications, and readback check, and the executable cell is
idempotent. The cell must list/read first, reuse an exact existing resource,
and refuse drift rather than duplicate or overwrite anything. Do not demand a
second approval merely because the requested creation is a cloud mutation;
stop only when the request is ambiguous, expands scope, changes policy, or the
notebook guard cannot establish the safe reuse/create boundary.

Every executable notebook cell must be run in dependency order. A cell must
never be silently deferred, left “intentionally not called,” or replaced by a
side-channel action. If its prerequisites, approval, authentication, or
readback state are not available, the cell must still execute and raise a
descriptive, understandable, fail-closed error that names exactly what was
blocked and what the owner must do to fix it. The error is part of the notebook
evidence; after the fix, rerun the same cell.

Notebook cells must also be idempotent: pure definitions and renderers
recreate the same result; read-only cloud cells may be rerun safely; create/apply
cells list or read before creating, reuse an exact existing resource, and refuse
drift rather than overwrite it. Historical receipts supplement executable
guarded action cells; they do not replace them. For inherently non-repeatable
operations such as a model message, the cell must execute a guard that reuses
the recorded result rather than sending another message. Preserve precondition
snapshots so a later live read does not make an already-approved plan fail
merely because the approved action succeeded.

### Cloud diagnostics are bounded actions, not an implicit repair campaign

Label a cloud section as exactly one of: read-only discovery, request
construction, resource creation/update, role assignment, security/authentication
configuration, model invocation, or diagnostic reproduction. A cell may not
bundle two action classes under “setup,” “tracing,” or “diagnosis.” A new
connection, shared resource, role assignment, local-authentication change,
temporary agent/monitor, or synthetic trace is a separate external change with
its own preceding Markdown boundary and owner authorization.

After an unexpected cloud error, preserve it and stop. Rerun only when the
same reviewed cell needs a local-only correction or documented
eventual-consistency wait; do not add roles, relax authentication, change a
connection, create a temporary resource, or alter the request. A diagnostic
follow-up must state one falsifiable hypothesis, its minimum test, its
cost/data/security impact, cleanup/readback, and the owner authority covering
it. A vendor sample is a pattern source, not standing authority for a
reproduction.

Least privilege is a review boundary, not a loop over likely roles. Before a
role or authentication change, show the exact principal, role, scope, reason
existing access is insufficient, and narrower alternative considered.
`Privileged Monitoring Data Reader`, a connection-string/API-key connection,
and enabling local authentication are sensitive exceptions: name them plainly,
leave an unchecked review task, and never describe that state as Entra-only.
Stored presentation output must not disclose connection strings, principal IDs,
subscription IDs, or other unnecessary infrastructure identifiers.

For a substantive governance, experiment-authority, automation-review, or
human-decision question, consult the relevant entries in the
[question-and-answer ledger](./QUESTION_LEDGER.md). Read the whole ledger when
the task changes a standing governance rule; otherwise read the pertinent
section rather than loading it indiscriminately.

This project owner needs detailed continuity documentation, especially after
technical interruptions. Do not replace reasoning with a terse status summary.
For substantive work, document the objective, controls, evidence, uncertainty,
why the result is trustworthy, and the next human-owned decision. Preserve the
local-only, bounded-inner-loop / evidence-driven-outer-loop, and
no-automatic-policy-mutation boundaries stated in the README.

## Orchestration and delegation policy

When the owner identifies an agent as the orchestrator, that agent owns
continuity and task decomposition. Before delegating, make the repository
instructions and handoff material internally consistent; a subagent must not
have to infer authority from stale prose or chat history. Give subagents one
small bounded task with named files, permitted actions, prohibited actions,
inputs they may trust, a concrete verification step, and an explicit stop
point. Keep them constrained enough that they cannot broaden scope, make an
external change, reinterpret policy, or silently continue into the next task.

The orchestrator remains responsible for reconciling results with the current
architecture and documentation. A subagent report is evidence for review, not
authority to deploy, invoke, alter source policy, expand an experiment, or
override a human-review boundary.

## Continuity synchronization after cloud work

When a notebook records a material cloud result, reconcile the current-state
statements in `README.md`, `docs/current-state-and-next-slice.md`,
`docs/foundry-transition-handoff.md`, `docs/next-agent-foundry-notebook-handoff.md`,
`QUESTION_LEDGER.md`, and the provisioning decision record before beginning a
new component. Label old reads, rollbacks, and failed attempts as historical;
do not leave them phrased as live inventory. The latest stored notebook
readback is the local source of truth unless a later recorded readback
supersedes it.

Do not edit a notebook or source file owned by another active chat merely to
make it tidier. During concurrent work, review its stored evidence and update
only the documentation or instructions explicitly assigned to this chat; tell
the owner about any source-of-truth conflict.

Before adding a notebook component, inspect its existing heading outline and
checklist. Use one unique, ordered section label per bounded action; do not
append a second cell under a reused subsection name. When a component expands,
add a short boundary note and update its checklist rather than allowing an
unstructured tail of telemetry, diagnostics, or retries to obscure the next
human decision.

Before calling a cloud notebook component complete, reconcile its opening
checklist with the executed evidence, verify its ordered section labels are
unique, and make its final card separate the working product path, historical
diagnostic work, unresolved blockers, and deferred follow-up. A later optional
investigation must not obscure the original component's result.
