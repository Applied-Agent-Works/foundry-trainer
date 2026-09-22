# Counterfactual timing contract

Every counterfactual result must include an **equivalent direct baseline**:
the unchanged policy, same target revision, seed, seat, configuration,
opponent, and direct simulator executor as the candidate's clean audit.

Do not compare a counterfactual result to a profiling harness that uses
`Environment.run`, timed-agent wrappers, cProfile, JSON trace copying, charts,
or compressed trace writes. Those are useful measurements, but they are not
the cost of an equivalent simulated match.

For each candidate report these separately:

| Field | Meaning |
|---|---|
| `equivalent_baseline_direct_seconds` | Full direct run of the unchanged policy. |
| `candidate_clean_seconds` | Full direct run of the changed policy. |
| `candidate_replay_seconds` | Policy-only replay through the unchanged prefix. |
| `candidate_suffix_seconds` | Restored simulator suffix after first divergence. |
| `candidate_cached_total_seconds` | Replay plus suffix; compare this to the clean candidate run. |
| `checkpoint_capture_seconds` | One-time baseline-cache construction; never treat as suffix-simulation time. |

The outcome for the equivalent direct baseline must equal the stored checkpoint
baseline outcome. The cached candidate outcome must equal its clean candidate
audit outcome. A deterministic opponent is required for that exact equality;
a stochastic opponent needs recorded action replay and must be labelled
`frozen-trajectory` rather than a fresh-match audit.

Interpretation:

- An early divergence should be about the cost of a direct full run, plus a
  small replay/restore overhead.
- A late divergence saves only the simulator work in the skipped prefix.
- A candidate does not make individual Kaggriculture turns faster; it merely
  avoids rerunning proven-identical turns.
