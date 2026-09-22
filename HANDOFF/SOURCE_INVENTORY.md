# Source inventory

This handoff includes a copy of the fixture in `HANDOFF/memoization-experiment/`.
The receiving agent should use that copy to understand and organize the work,
while preserving the original source location and revision as provenance.

## Included handoff fixture

`HANDOFF/memoization-experiment/`

| Material | Status |
|---|---|
| `profile_step8.py` | Local timing and trace-validation harness; checkpoint/resume is not implemented. |
| `kaggriculture_playground.ipynb` | Experimental matched-suite notebook. |
| `README.md` | Original fixture instructions, annotated for this handoff copy. |
| `results/` and `trace-cache/` | Not included in the copied handoff fixture; they remain disposable source-side artifacts. |

The copied harness still assumes the Kaggriculture policy package is available.
It is reference material until the receiving agent creates an explicit,
documented target-project binding; it is not a standalone executable in this
repository yet.

## Kaggriculture source workspace

`../kaggriculture/`

| Material | Location | Status |
|---|---|---|
| Project constraints | `AGENTS.md` | Read before changing policy or experiment architecture. |
| Agent architecture | `kaggriculture-agent-architecture.md` | Durable description of the local symbolic/probabilistic policy. |
| Carrot decision model | `carrot-decision-network.md` | Defines the named assumptions and policy parameters to tune. |
| Foundry refinement design | `foundry-refinement-architecture.md` | Current control-plane design and non-negotiable boundaries. |
| Experimental harness provenance | `memoization-experiment/profile_step8.py` | Original source for the included handoff copy. |
| Experimental notebook provenance | `memoization-experiment/kaggriculture_playground.ipynb` | Original source for the included handoff copy. |
| Fixture-instruction provenance | `memoization-experiment/README.md` | Original local run commands and scope. |
| Generated reports | `memoization-experiment/results/` | Disposable and ignored by Git. |
| Trace cache | `memoization-experiment/trace-cache/` | Disposable and ignored by Git. |

## Transfer rules

1. Do not edit the Kaggriculture policy, game rules, or Kaggle submission path
   while establishing this trainer project.
2. Promote source code from the included handoff copy separately from generated
   caches. Generated material is optional evidence, not a required dependency
   of the trainer.
3. Keep source provenance: record the source revision, copied paths, and any
   deliberate adaptations required because the fixture moves out of the target
   repository.
4. Keep all target-agent imports or subprocess paths explicit. Do not rely on
   an implicit current working directory or a generic Python module named
   `agents`.
5. Do not create Azure resources, credentials, API integrations, or external
   model calls as part of this transfer.

## Receiving-project state

This repository was empty before this handoff. The only material now present is
the handoff itself. It has no runtime, dependencies, cloud configuration, or
deployment target yet.
