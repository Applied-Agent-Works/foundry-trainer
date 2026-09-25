# Watermelon Tuner first-pass result

The canonical approved local proof ran on 2026-09-24 against the explicitly bound
Kaggriculture checkout at revision
`6ace5fed9018fef45642b41ea11d0bd741a508a4`. The MELON policy hash was
`0ffc8740341050b74f44a4418aa67bd4cfb0a5c026e209ae2d93898c0e9b33d4`; the
helper hash was
`2645298bf3348cd53f6025348104bfc2dac28655de822f5db27a73cb0c23c995`; the
engine hash was `bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e`.

Canonical receipt:
[`melon-future-price-multiplier-smoke-v1.json`](../../var/watermelon-tuning-system/canonical-20260924/report/melon-future-price-multiplier-smoke-v1.json).

Controls were the approved deterministic MELON conveyor opponent, seeds 42 and
43, both seats, and 720 turns. The one changed field was
`future_price_multiplier`, with baseline 1.0. Four baseline matches were
materialized with a checkpoint before every decision.

| Candidate | Mean reward | Paired delta | Divergent matches | Suffix actions | Clean audits |
|---:|---:|---:|---:|---:|---:|
| 0.05 | 6047.00 | +41.00 | 4/4 | 2876 | 4/4 |
| 0.80 | 6006.00 | 0.00 | 0/4 | 0 | 4/4 |
| 1.20 | 6006.00 | 0.00 | 0/4 | 0 | 4/4 |

The baseline mean reward was 6006.00. The low candidate diverged at turn 0 in
every match and required a full 719-action suffix; its clean rerun matched the
restored result exactly. The two moderate candidates never changed an action,
so their outcomes were reused from the baseline and independently confirmed by
clean reruns.

This is a mechanical proof, not a promotion recommendation. Four matched
games are intentionally too small to establish a robust melon policy choice.
The +41 result is a hypothesis for a later held-out suite, not evidence of a
global improvement. The canonical generated JSON report and gzip caches are
disposable under ignored `var/watermelon-tuning-system/`; this document
preserves the source revision, complete hash set, controls, and aggregate facts
needed to understand the run. Earlier `first-pass/`, `first-pass-v2/`, and
`repair-pass-20260924/` receipts are historical/superseded copies.

## Issue found and fixed

The first attempt exposed a real integration defect: the shared checkpoint
engine's clean-rerun branch still called `carrot_decision_agent` after the
target binding had correctly loaded MELON. The generalized target binding now
routes both fast suffixes and clean audits through the explicit crop adapter.
The full local test suite passes after that fix.

The follow-up abstraction pass moved crop-specific names out of the base
binding into explicit adapter modules. The Watermelon rerun now records the
MELON shared-policy hash, the one-time-crop helper hash, and the engine hash in
the report. Its aggregate results remained identical, and its clean audits
still passed.

The explicitly simulator-marked regression tests were then run with:

```bash
../kaggriculture/.venv/bin/python -m pytest -o addopts='' -m simulator -q
```

Recorded result: `2 passed, 43 deselected` in 4.98 seconds. The deselected
tests are the simulator-free tests excluded by the explicit `-m simulator`
selection; they remain covered by the normal fast suite.

## Next decision

Review the adapter seam and approve a larger held-out seed suite before treating
the 0.05 result as anything more than a demonstration that the melon policy's
plant threshold can be crossed.
