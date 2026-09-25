# Wheat experiment records

`schema/` contains the Wheat Tuner contract. `approved/` contains bounded,
human-approved executable envelopes. Generated caches and reports belong under
the parent repository's ignored `var/wheat-tuning-system/` tree.

The first contract changes one named policy parameter and fixes the target,
deterministic opponent, seeds, seats, steps, checkpoint policy, and clean-audit
requirement. It does not authorize source mutation or candidate expansion.
