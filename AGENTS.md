# Repository-wide continuity rules

This repository contains a shared local evaluator and three bounded decision-
graph tuner projects: Carrot, Wheat, and Watermelon/Melon. The sibling
`kaggriculture` checkout is the system under test; do not edit its policy,
engine, submission entry point, or agent architecture from this repository.

Before changing a subsystem, read its local continuity instructions:

- [`carrot-tuning-system/AGENTS.md`](./carrot-tuning-system/AGENTS.md)
- [`wheat-tuning-system/AGENTS.md`](./wheat-tuning-system/AGENTS.md)
- [`watermelon-tuning-system/AGENTS.md`](./watermelon-tuning-system/AGENTS.md)

The shared evaluator is deterministic and local. Candidate values are
in-memory contract inputs; every fast result requires a matching clean audit;
target revision and source hashes must be recorded; and no source-policy
mutation or candidate expansion is automatic.

Foundry work belongs to the Carrot continuity boundary. Reviewed notebooks are
the authority for creating, updating, provisioning, and recording Azure or
Foundry resources; they are not the only place those already-created resources
may be used. Once a notebook has created or reused an exact resource and
recorded its readback, application code, services, and other reviewed
components may consume it through their approved runtime integration. Do not
substitute MCP, CLI, portal, or a standalone script for a missing or broken
resource-lifecycle notebook action. Treat package, virtual-environment,
lockfile, and cloud changes as separate reviewable boundaries. The Foundry
evidence analyst receives only redacted packets and cannot run the simulator,
edit policy source, or approve a new experiment.

The owner has granted a standing, low-cost build authority for Carrot Foundry
work. Read [`carrot-tuning-system/AGENTS.md`](./carrot-tuning-system/AGENTS.md)
for the exact allowed resource classes, cost envelope, and stop conditions.
Within that envelope, an agent must build and execute the reviewed notebook
cell rather than waiting for a redundant per-resource approval. This does not
apply to Wheat, Watermelon, the shared evaluator, Kaggriculture source, or a
new Azure infrastructure/security class.

## Mandatory iterative notebook authoring protocol

When a notebook is both an executable artifact and a teaching/design artifact,
use this exact shape. Do not silently substitute a script, a prose-only plan,
or a finished implementation.

### Notebook session

Begin with a Markdown orientation that states the objective, current starting
state, bounded autonomy envelope, inputs, non-goals, checklist, and decisions
that will remain for human review. Read the relevant continuity documents and
inspect the notebook's existing headings and stored outputs before editing.

### Every notebook section

Build one uniquely labelled bounded concept at a time:

1. Markdown description: purpose, inputs, output, predecessor, boundary, and
   remaining uncertainty.
2. Focused code block: the source of truth for that concept. Comments explain
   why an invariant, safety boundary, provenance check, or surprising choice
   exists; they do not narrate obvious syntax.
3. Separate presentation-only code block: a hideable, human-readable Markdown
   card that consumes only values already computed by the code block. It must
   not choose inputs, validate, mutate, call a service, or recommend an action.
4. Success and meaningful guard cases, followed by the next boundary or review
   task.

Run every executable cell in dependency order and retain its actual output.
Never leave a cell silently unrun, call it “intentionally not called,” or
hand-author a successful-looking output. Use a unique ordered heading; do not
reuse a subsection label or append an unstructured tail.

### Ambiguity and error handling

If a request could mean notebook editing, a pure local check, an environment
change, an authenticated cloud read, or a cloud mutation, list those choices
and ask the owner to select one—unless the local subsystem's standing authority
already names the exact action. Do not infer the broadest action from “do it”
or “run it.” A harmless implementation choice inside the stated envelope may
be documented as an assumption and flagged for later review; anything changing
scope, cost, security, data handling, contract, source policy, or external
state outside that envelope is a stop point.

When a cell errors, preserve the exact actionable error, classify the blocker,
make only the smallest in-scope fix, and rerun the same cell. A missing
dependency is a prerequisite, not permission to install it. A cloud failure is
not permission to retry, switch tools, or perform a side-channel equivalent.
If recovery changes scope or requires a new side effect, stop and flag the
decision instead. Finish with a visible unchecked review task for every
pending human decision and update the required continuity documents.

### Blocker transparency

If the requested outcome cannot be completed, say so immediately. Name the
exact blocker, distinguish completed work from a mock, plan, or partial result,
and do not imply that an unexecuted action succeeded. Do not silently replace
the requested action with a simulation, canned response, or weaker substitute;
offer that substitute only as an explicitly labeled fallback and leave the
original blocker visible. This rule applies to the primary agent and every
future or delegated agent.

When reviewing the whole repository, distinguish current readbacks from
historical receipts, preserve unrelated worktree changes, run the fast tests
and structural JSON/notebook checks, and report any active-agent ownership
conflict before editing implementation files.
