# Tomato Tuner first-pass result

The canonical reviewed run used the pinned Kaggriculture target, deterministic
Tomato conveyor, seeds 42/43, both seats, 720 turns, and
`future_price_multiplier` values `0.05`, `0.8`, and `1.2` against baseline
`1.0`.

| Candidate | Mean reward | Paired delta | Divergences | Clean audits |
|---:|---:|---:|---:|---:|
| `0.05` | 3000.00 | -438.50 | 4 / 4 | 4 / 4 passed |
| `0.80` | 3438.50 | 0.00 | 0 / 4 | 4 / 4 passed |
| `1.20` | 3438.50 | 0.00 | 0 / 4 | 4 / 4 passed |

The low candidate crossed the observed plant/pass threshold; the moderate
candidates did not. This is a four-match infrastructure proof, not evidence
that the baseline is globally optimal.

The same approved envelope was re-pinned and rerun on 2026-09-26 against
Kaggriculture revision `3d8249e0de84002156500c6ee708d51925133169`. The fresh
receipt is under
`var/tomato-tuning-system/runs/20260926-ongoing-004808/report/` and all four
candidate-match audits passed.
