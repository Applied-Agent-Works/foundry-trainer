# Strawberry Tuner continuity rules

This project is a draft, local-only tuner scaffold for Kaggriculture's
`STRAWBERRY` teaching policy. Kaggriculture is the read-only system under
test. Do not edit its policy, engine, entry point, branches, or worktrees from
this project.

Use only `STRAWBERRY_ADAPTER` as the target seam. Preserve the explicit target
root, Git revision, complete source hashes, deterministic Strawberry conveyor,
fixed seeds and seats, checkpoint-before-every-decision policy, and clean
full-run audit requirement. Candidate parameters are ephemeral in-memory
values; they never authorize a target source edit.

The original contract under `experiments/draft/` remains deliberately
fail-closed. The separately reviewed contract under `experiments/approved/`
authorizes only the bounded first-pass runner; do not expand its candidates,
write a production runner, or add Foundry/cloud work without a separate human
review. Generated caches and reports belong under ignored
`var/strawberry-tuning-system/` paths.
