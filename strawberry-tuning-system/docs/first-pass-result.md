# Strawberry Tuner first-pass result

The canonical reviewed run used the pinned Kaggriculture target, deterministic
Strawberry conveyor, seeds 42/43, both seats, 720 turns, and
`future_price_multiplier` values `0.05`, `0.8`, and `1.2` against baseline
`1.0`.

| Candidate | Mean reward | Paired delta | Divergences | Clean audits |
|---:|---:|---:|---:|---:|
| `0.05` | 3000.00 | -745.00 | 4 / 4 | 4 / 4 passed |
| `0.80` | 3745.00 | 0.00 | 0 / 4 | 4 / 4 passed |
| `1.20` | 3745.00 | 0.00 | 0 / 4 | 4 / 4 passed |

The low candidate crossed the observed plant/pass threshold; the moderate
candidates did not. This is a four-match infrastructure proof, not evidence
that the baseline is globally optimal.
