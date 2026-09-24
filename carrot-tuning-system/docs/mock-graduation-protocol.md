# Mock graduation protocol

## Why this protocol exists

The system-model notebook is an executable explanation, not a shadow production
system. Its mocks made the target architecture readable before the local
evaluator and Foundry analyst existed. A mock is not “completed” because its
cell gains more code: it graduates only when a real replacement has the right
authority, provenance, tests, and stated limits. Until then it remains visibly
illustrative or deferred.

## Status vocabulary

| Status | Meaning | May affect a real run? |
|:---|:---|:---|
| `illustrative` | Teaches architecture or historical facts. | No. |
| `prototype` | Exercises one bounded prospective component. | Only under a separately approved side-effect envelope. |
| `promoted` | Reviewed reusable behavior exists in source with focused tests. | Only through its explicit source API. |
| `integrated` | A promoted component is wired into an approved path and its actual result is recorded. | Only within that authority. |
| `deferred` | A future interface lacks authoritative inputs or a valid question. | No. |

Never relabel a mock `promoted` or `integrated` based only on a similar source
function, a notebook output, or agent confidence.

## Graduation gate

Before implementing a replacement, write a short section or decision record
that identifies:

1. Exact input, output, allowed side effects, and prohibited authority.
2. Canonical inputs: a source-controlled schema/contract, immutable packet, or
   named external API—not a handwritten notebook constant.
3. Truth owner: local evaluator for game outcomes; Foundry analyst for bounded
   interpretation; human for execution envelopes and source-policy decisions.
4. One meaningful success case and one guard that stops before an external
   call, simulator action, durable write, or policy mutation.
5. The source module, public API, and simulator-free regression test.
6. The separate contract or deployment authority needed for integration.
7. The review record for any automated decision. Deferred review requires
   `review_status: pending_human_review` and an unchecked `- [ ]` task.

The sequence is: explain → prototype → exercise success and guard → explicit
review or phase-level authorization → source promotion → source test →
approved integration → record actual result. A renderer may summarize existing
facts but may not choose inputs, validate contracts, call services, or write
artifacts.

## Current system-model inventory

| Notebook concept | Status | Graduation path | Explicit non-goal |
|:---|:---|:---|:---|
| Bounded `ExperimentSpec` data model | `illustrative` | Schema v1 plus approved contracts and the source validator are its executable replacement. Keep the notebook model for teaching. | A second notebook execution contract. |
| `mock_inner_loop` historical snapshot | `illustrative` | The real local runner and immutable smoke packet already supply the execution path. A later read-only evidence adapter may display canonical facts without rerunning a simulator. | Treating ignored local data or stale output as a universal current result. |
| Deterministic `evaluate_packet` assessment | `illustrative` | Next local outer-evaluation component: validated packet in, typed deterministic assessment out, simulator-free. | Ranking candidates, prescribing source edits, or overriding failed audits. |
| `mock_reasoning_loop` | `illustrative` | First Foundry component: a stateless no-tools prompt analyst with schema-validated input and constrained JSON output. | Simulator, local filesystem, target-policy, packet-write, or unrestricted connector tools. |
| `mock_opportunity_value` formula | `deferred` | A later graph-adapter contract must supply contextual inputs with provenance, units, and calibration/audit evidence. | Promoting placeholder weights to policy values to make a mock look finished. |

## Deadline-oriented sequence

The Foundry submission deadline is earlier than the farming-agent deadline.
That means the contextual/multi-graph mock is not a submission blocker: it
stays `deferred` until the later agent iteration supplies authoritative inputs.
The submission should instead make the local-evidence → deterministic
assessment → constrained Foundry-analyst path clear and modifiable.

1. Preserve the completed local evaluator; do not widen its suite as a Foundry
   prerequisite.
2. Build and test the deterministic packet-to-assessment component locally.
3. Scaffold the modifiable Foundry analyst around the same packet/assessment
   contract, with no tools and no deployment yet.
4. Record and approve project, region, budget, retention, network, model, and
   RBAC decisions.
5. Provision one development environment, deploy the analyst, invoke a smoke
   packet, and run analyst-behavior evaluation.
6. Leave contextual/multi-graph work visibly deferred until a new approved
   graph contract supplies real inputs.

This produces a truthful vertical slice: local mechanics create evidence,
Foundry interprets bounded evidence, and humans retain envelope and policy
authority.
