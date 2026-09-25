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

Foundry work belongs to the Carrot continuity boundary. The reviewed notebook
is the Azure action authority: do not substitute MCP, CLI, portal, or a
standalone script for a missing or broken notebook action. Treat package,
virtual-environment, lockfile, and cloud changes as separate reviewable
boundaries. The Foundry evidence analyst receives only redacted packets and
cannot run the simulator, edit policy source, or approve a new experiment.

When reviewing the whole repository, distinguish current readbacks from
historical receipts, preserve unrelated worktree changes, run the fast tests
and structural JSON/notebook checks, and report any active-agent ownership
conflict before editing implementation files.
