# Wheat Tuner continuity rules

Read [README.md](./README.md) and
[current-state-and-next-slice.md](./docs/current-state-and-next-slice.md) in
full before changing this project. Kaggriculture remains the system under
test. Do not edit its policy, game rules, submission entry point, or agent
architecture from this tuner.

The first pass is deliberately narrow: one wheat crop graph, one explicit
parameter, a fixed deterministic wheat conveyor, matched seeds and seats,
checkpoint/resume, and clean full-run audits. Candidate values are ephemeral
in-memory overrides. Generated caches and reports belong under ignored `var/`.

Every result must retain target revision and hashes, opponent, seeds, seats,
steps, old/new values, divergence turns, suffix lengths, outcomes, and audit
status. Do not expand the candidate envelope or switch to Foundry work without
a new source-controlled contract and human review.
