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

Every result must retain target revision and hashes, opponent, seeds, seats,
steps, old/new values, divergence turns, suffix lengths, outcomes, and audit
status. Do not expand the candidate envelope or switch to Foundry work without
a new source-controlled contract and human review.
