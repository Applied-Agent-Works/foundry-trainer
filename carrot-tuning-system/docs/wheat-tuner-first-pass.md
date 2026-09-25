# Wheat Tuner ownership handoff

The authoritative first-pass Wheat Tuner is maintained in the sibling
[`wheat-tuning-system/`](../../wheat-tuning-system/) project. It follows the
Carrot Tuner's checkpoint/resume and clean-audit pattern while binding
explicitly to Kaggriculture's wheat graph.

Start with its [README](../../wheat-tuning-system/README.md), then read the
[first-pass result](../../wheat-tuning-system/docs/first-pass-result.md) and
[current-state snapshot](../../wheat-tuning-system/docs/current-state-and-next-slice.md).

This redirect is intentional: there must be one source-controlled Wheat
contract and one runner, not a duplicate implementation hidden inside the
Carrot project.
