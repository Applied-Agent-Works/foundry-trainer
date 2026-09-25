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

## Notebook authoring contract

When adding a notebook, begin with Markdown describing the objective, current
state, bounded autonomy, non-goals, checklist, and pending human decisions.
Build each unique section as: description Markdown; focused commented source
code; a separate hideable presentation-only Markdown card; and success/guard
evidence. Execute every code cell in dependency order and retain actual
outputs. Never leave a cell unrun, reuse a section label, fabricate output, or
replace notebook work with a side-channel command.

If wording is ambiguous between editing, a pure local check, an environment
change, or an external action, state the choices and stop. On an error, retain
the exact actionable failure, make only the smallest in-scope correction, and
rerun the same cell. Do not install missing packages or retry external work
without separate approval. Flag scope, contract, source, cost, or policy
decisions with an unchecked review task.
