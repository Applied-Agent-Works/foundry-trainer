# Watermelon experiment records

`schema/` contains the versioned JSON contract. `approved/` contains bounded
human-approved executable envelopes. Generated baseline caches and reports
belong under the repository's ignored `var/` tree and are never the source of
truth.

Each contract changes one named policy parameter, preserves target provenance,
and states the fixed deterministic opponent, seeds, seats, and checkpoint/audit
rules. Historical results, if added later, should be immutable records in a
separate `historical/` directory and must not be treated as automatic run
authorization.

