# Wheat source provenance

The Wheat Tuner binds to the sibling Kaggriculture checkout at revision
`6ace5fed9018fef45642b41ea11d0bd741a508a4`. The first pass records the same
facts in its JSON report and refuses a cache or contract whose fingerprints do
not match.

| File | SHA-256 |
|---|---|
| `agents/wheat/shared.py` | `ca0a9c25e5a582c9284f84e87bc24ad0e00929a65fe326a0de698ce123b615cd` |
| `agents/one_time_crop.py` | `2645298bf3348cd53f6025348104bfc2dac28655de822f5db27a73cb0c23c995` |
| `kaggriculture.py` | `bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e` |

The wheat source files are currently uncommitted working-tree material at the
pinned Git revision. Git revision alone therefore does not identify the target
policy; the shared-policy and engine hashes are required. The tuner did not
modify that checkout.

The fixed crop facts come from the source handoff: seed replacement cost 10,
planned unfertilized yield 4, planned harvest day 4, and base price 25. The
first tunable policy input is the provisional point-estimate
`future_price_multiplier`; animal-feed value, fertilizer, and multi-crop
selection are outside this first graph.

The canonical receipt for this provenance record is
`var/wheat-tuning-system/canonical-20260924/report/wheat-future-price-multiplier-smoke-v1.json`.
