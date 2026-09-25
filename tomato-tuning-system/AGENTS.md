# Tomato Tuner continuity rules

This project is a draft, local-only tuner scaffold for Kaggriculture's
`TOMATO` teaching policy. Kaggriculture is the read-only system under test.
Do not edit its policy, engine, entry point, branches, or worktrees from this
project.

Use only `TOMATO_ADAPTER` as the target seam. Preserve the explicit target
root, Git revision, complete source hashes, deterministic Tomato conveyor,
fixed seeds and seats, checkpoint-before-every-decision policy, and clean
full-run audit requirement. Candidate parameters are ephemeral in-memory
values; they never authorize a target source edit.

The checked-in `draft/` contract remains fail-closed. A human-approved copy now
lives under `experiments/approved/` and is executable only through the bounded
local first-pass script. Do not expand its candidates, add automatic policy
mutation, or add Foundry/cloud work. Generated caches and reports belong under
ignored `var/tomato-tuning-system/` paths.
