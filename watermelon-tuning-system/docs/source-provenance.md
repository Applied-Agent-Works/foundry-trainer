# Watermelon source provenance

The source-controlled handoff was prepared in the sibling Kaggriculture
checkout at revision `6ace5fed9018fef45642b41ea11d0bd741a508a4`. The first
pass binds to the live explicit checkout supplied on the command line and
records the same facts in its report.

Relevant source hashes from the handoff are:

The machine-readable hash set is intentionally exact: these are the three
files that define the bound policy/helper and simulator target for this first
pass. Adding or changing one changes cache identity; a cache from another set
is not reusable.

| File | SHA-256 |
|---|---|
| `agents/melon/shared.py` | `0ffc8740341050b74f44a4418aa67bd4cfb0a5c026e209ae2d93898c0e9b33d4` |
| `agents/one_time_crop.py` | `2645298bf3348cd53f6025348104bfc2dac28655de822f5db27a73cb0c23c995` |
| `kaggriculture.py` | `bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e` |

The MELON facts are fixed game rules: seed replacement cost 80, planned
unfertilized yield 6, planned harvest age 10, and base market price 250. The
first tunable policy value is the point-estimate `future_price_multiplier`;
`pass_utility` and season horizon remain declared controls but are not changed
in this experiment.

The sibling checkout currently contains the MELON source files as untracked
working-tree material at this pinned revision. That is why both the Git
revision and SHA-256 hashes are recorded: revision alone does not identify
those files completely.

The generated receipt path for this provenance record is
`var/watermelon-tuning-system/canonical-20260924/report/melon-future-price-multiplier-smoke-v1.json`.
The path is ignored run output and must be regenerated in a fresh checkout.
