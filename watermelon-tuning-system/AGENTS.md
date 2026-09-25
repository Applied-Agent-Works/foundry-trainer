# Watermelon Tuner continuity rules

Read [README.md](./README.md) and
[current-state-and-next-slice.md](./docs/current-state-and-next-slice.md) in
full before changing this project. The target crop is Kaggriculture's
`MELON`; “watermelon” is the project name used for the tuner.

This is a local, bounded evaluator. Kaggriculture remains the system under
test. Do not edit its policy, game rules, submission entry point, or agent
architecture. Candidate values are ephemeral in-memory overrides and a human
must apply any later source change.

Keep the explicit target root, target revision, source hashes, simulator
configuration, opponent, seeds, seats, old/new values, divergence turns,
suffix lengths, outcomes, and audit status in every result. Generated caches
and reports belong under ignored `var/` paths. Never infer the target from the
current directory or a generic `agents` import.

The first pass is deliberately narrow: one parameter, a fixed deterministic
MELON conveyor opponent, a small matched seed/seat suite, checkpoint/resume,
and clean full-run audits. Do not expand into search, Foundry deployment, or
automatic policy mutation until the first-pass audit is green.

