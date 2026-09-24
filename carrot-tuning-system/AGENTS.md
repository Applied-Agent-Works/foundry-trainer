# Future-agent continuity requirements

Read [README.md](./README.md) and the
[current-state snapshot](./docs/current-state-and-next-slice.md) in full before
working in this directory.

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
