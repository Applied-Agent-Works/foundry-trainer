# Carrot tuning system: architecture diagrams

These diagrams are a visual companion to the detailed
[continuity guide](../README.md), not an alternative specification. They show
which component is allowed to make which kind of decision. In particular, the
local evaluator is the score authority; Foundry-facing components interpret
evidence and propose bounded next experiments, but never overwrite local audit
status or edit Kaggriculture policy source.

## 1. System context: two loops, one human governance boundary

```mermaid
flowchart LR
    Human([Human owner])
    Spec[(Versioned experiment specification)]

    subgraph Local[Local deterministic evidence plane]
        Validate[Validate spec and explicit target binding]
        Baseline[(Immutable baseline cache)]
        Fast[Checkpoint replay and restored suffix]
        Audit[Clean full-suite audit]
        Packet[(Evidence packet)]
        Target[[Kaggriculture system under test]]

        Validate --> Baseline
        Validate --> Fast
        Baseline --> Fast
        Fast <--> Target
        Fast --> Audit
        Audit <--> Target
        Audit --> Packet
    end

    subgraph Outer[Outer evals and reasoning plane]
        Evals[Evaluate audit status, coverage, and paired results]
        Reasoner[Reasoning agent: explain and propose]
        Proposal[(Bounded next-experiment proposal)]

        Evals --> Reasoner --> Proposal
    end

    Human -->|approves bounded envelope| Spec
    Spec --> Validate
    Packet --> Evals
    Proposal -->|human reviews| Human
    Human -.->|only human applies a reviewed change| Target

    classDef authority fill:#d9ead3,stroke:#38761d,color:#000;
    classDef evidence fill:#cfe2f3,stroke:#1155cc,color:#000;
    classDef future fill:#fce5cd,stroke:#b45f06,color:#000;
    class Human authority;
    class Validate,Baseline,Fast,Audit,Packet,Target evidence;
    class Evals,Reasoner,Proposal future;
```

The dashed human-to-target edge is intentionally not an automation path. It
means that an actual source-policy change requires a separate human decision
after reviewing evidence.

## 2. Inner-loop sequence: one candidate against one matched game

```mermaid
sequenceDiagram
    autonumber
    participant R as Local inner-loop runner
    participant B as Explicit target binding
    participant C as Baseline cache
    participant K as Kaggriculture simulator
    participant A as Clean-audit runner
    participant P as Evidence packet

    R->>B: Verify revision and policy/engine hashes
    B-->>R: Bound target or fail closed
    R->>C: Load matching baseline for seed + seat
    C-->>R: Pre-decision observations, actions, checkpoints, outcome

    loop Each recorded decision, until first action mismatch
        R->>R: Evaluate candidate on cached observation
    end

    alt No action divergence
        R->>R: Reuse exact baseline outcome
        Note over R,C: No simulator suffix is required.
    else First action divergence at turn T
        R->>C: Read state immediately before turn T
        R->>K: Create fresh environment and restore state + step prefix
        loop Remaining suffix
            R->>K: Candidate action + deterministic opponent action
            K-->>R: Next state
        end
        K-->>R: Candidate suffix outcome
    end

    R->>A: Run clean full candidate game with same seed, seat, suite controls
    A-->>R: Independent full-run outcome
    alt Cached outcome equals audit outcome
        R->>P: Record result with audit_status = passed
    else Outcome mismatch
        R->>P: Record result with audit_status = failed
        Note over R,P: Do not classify candidate success or extend the bracket.
    end
```

The restore includes the simulator's completed step-prefix placeholders as
well as state. That detail prevents the engine from silently restarting its
internal step numbering after restoration.

## 3. Outer-loop interaction: evidence before reasoning

```mermaid
sequenceDiagram
    autonumber
    actor H as Human owner
    participant S as Spec repository
    participant L as Local evaluator
    participant E as Deterministic evals layer
    participant F as Foundry-facing reasoning agent

    H->>S: Approve bounded experiment spec
    S->>L: Provide immutable spec
    L-->>E: Evidence packet: outcomes, audits, divergence, coverage, provenance
    E->>E: Validate audit status and predeclared controls

    alt Audit failed or controls invalid
        E-->>H: Stop: repair local evidence path
    else Evidence valid
        E-->>F: Structured evidence + deterministic classification
        F->>F: Explain uncertainty and choose next bounded question
        F-->>H: Proposal, rationale, controls, success/failure criteria
        H->>S: Approve, reject, or revise next spec
    end
```

The reasoning agent receives a structured evidence packet, not raw simulator
state or authority to alter results. The deterministic evals layer can block a
proposal when audits fail.

## 4. Core entities and their relationships

This is a conceptual entity diagram, not a database schema. It identifies
records that need stable identities and provenance once the mocked notebook is
replaced by the real inner-loop runner.

```mermaid
erDiagram
    EXPERIMENT_SPEC ||--|| TARGET_FINGERPRINT : expects
    EXPERIMENT_SPEC ||--|| MATCHED_SUITE : defines
    EXPERIMENT_SPEC ||--|{ CANDIDATE_OVERRIDE : bounds
    EXPERIMENT_SPEC ||--|| GOVERNANCE_RULES : carries
    MATCHED_SUITE ||--|{ MATCH_CASE : contains
    MATCH_CASE ||--|| BASELINE_CACHE : has
    BASELINE_CACHE ||--|{ DECISION_CHECKPOINT : stores
    CANDIDATE_OVERRIDE ||--|{ CANDIDATE_MATCH_RESULT : produces
    MATCH_CASE ||--|{ CANDIDATE_MATCH_RESULT : evaluates
    CANDIDATE_MATCH_RESULT ||--|| CLEAN_AUDIT : verifies
    EXPERIMENT_SPEC ||--|| EVIDENCE_PACKET : emits
    EVIDENCE_PACKET ||--|{ CANDIDATE_MATCH_RESULT : summarizes
    EVIDENCE_PACKET ||--|| EVALUATION_ASSESSMENT : receives
    EVALUATION_ASSESSMENT ||--o| REASONING_PROPOSAL : informs
    REASONING_PROPOSAL ||--o| EXPERIMENT_SPEC : proposes_next

    EXPERIMENT_SPEC {
        string experiment_id
        string lifecycle_status
        string decision_graph_id
        string parameter_name
    }
    TARGET_FINGERPRINT {
        string git_revision
        string shared_sha256
        string engine_sha256
    }
    MATCHED_SUITE {
        string opponent_id
        int steps
        int seed_count
        int seats
    }
    MATCH_CASE {
        int seed
        int decision_player
    }
    CANDIDATE_OVERRIDE {
        float old_value
        float new_value
    }
    DECISION_CHECKPOINT {
        int turn
        json state
        json observation
        json baseline_action
    }
    CANDIDATE_MATCH_RESULT {
        int first_divergence_turn
        int suffix_actions
        string mode
        string audit_status
    }
    CLEAN_AUDIT {
        json outcome
        float elapsed_seconds
    }
    EVIDENCE_PACKET {
        string packet_id
        string deterministic_status
    }
    EVALUATION_ASSESSMENT {
        string classification
        string limitations
    }
    REASONING_PROPOSAL {
        string hypothesis
        string proposed_envelope
    }
```

The key relationship is `CANDIDATE_MATCH_RESULT → CLEAN_AUDIT`: a fast result
is not standalone evidence. Its audit establishes whether it may be included
in an evidence packet at all.

## 5. Decision-graph interaction: carrots today, multiple graphs later

```mermaid
flowchart TB
    State[(Observed farm state)]
    Selector[Future action selector]
    Carrot[Carrot-investment graph]
    Other[Other decision graphs<br/>crop choice, market, land, hands, animals]
    Context[Contextual opportunity-value provider]
    Explanation[(Graph explanation and utility margin)]
    Action[Selected farmer + market action]
    Game[[Kaggriculture simulator]]
    Evidence[(Matched outcome and clean audit)]

    State --> Selector
    State --> Carrot
    State --> Other
    Other --> Context
    Context -->|provenanced opportunity value| Carrot
    Carrot --> Explanation
    Carrot -->|candidate action + local utility| Selector
    Other -->|candidate actions + local utilities| Selector
    Selector --> Action --> Game --> Evidence
    Evidence -.->|calibrates future experiments, not live source mutation| Context
```

Today, `seed_opportunity_value` is a static carrot parameter. Later, it can be
the typed input from `Context`, representing a credible competing use of seed,
tile, money, farmer time, or near-future action capacity. The carrot graph
continues to estimate carrot return; it should not quietly become the whole
farm planner.

## 6. Experiment lifecycle and immutability

```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Approved: Human approves exact envelope
    Draft --> Retired: Question superseded
    Approved --> Running: Local runner validates target + suite
    Running --> AuditFailed: Any clean audit mismatch
    Running --> Completed: All required audits pass
    AuditFailed --> Draft: Repair or create revised spec
    Completed --> HistoricalReproduction: Preserve contract + expectations
    HistoricalReproduction --> Approved: Human explicitly authorizes reproduction
    Completed --> [*]
    Retired --> [*]
```

An executed specification is never edited to create a new question. A changed
candidate envelope, suite, target revision, or acceptance rule gets a new
versioned specification. Historical records preserve the exact controls and
expected classification that a future runner must reproduce.

## 7. Foundry control plane: deployed analyst, planned judge and review

This is the source-controlled Foundry vertical slice. The no-tools Workflow /
Analyst path is deployed and has one accepted redacted smoke response; the
Evaluation/Judge, Review, and richer Trace analysis remain future or blocked
work. The important distinction is between an LLM used to *generate or judge
language* and deterministic components that retain mechanical authority.

```mermaid
flowchart LR
    Packet[(Immutable local evidence packet)]
    Assess[Local deterministic packet assessment]
    Stop[Refuse: insufficient or invalid evidence]

    subgraph Foundry[Microsoft Foundry control plane]
        Workflow[Versioned no-tools prompt agent]
        Analyst[Evidence analyst role]
        Gate[Deterministic governance checker]
        Review[Structured pending-review record]
        EvalSet[(Redacted fixed evaluation fixtures)]
        Judge[Foundry Evaluations: LLM-as-judge rubric]
        Trace[Application Insights / OpenTelemetry]

        Workflow --> Analyst --> Gate --> Review
        EvalSet --> Workflow
        Workflow --> Judge
        Workflow -.-> Trace
        Judge -.-> Trace
    end

    Human([Human owner])
    NextSpec[(New versioned experiment spec)]

    Packet --> Assess
    Assess -->|eligible, redacted packet| Workflow
    Assess -->|audit/coverage/provenance failure| Stop
    Gate -->|scope or authority failure| Stop
    Review -->|visible unchecked to-do| Human
    Human -->|approves or revises envelope| NextSpec

    classDef local fill:#cfe2f3,stroke:#1155cc,color:#000;
    classDef deterministic fill:#d9ead3,stroke:#38761d,color:#000;
    classDef deployed fill:#d0e0e3,stroke:#134f5c,color:#000;
    classDef planned fill:#fce5cd,stroke:#b45f06,color:#000;
    classDef human fill:#ead1dc,stroke:#741b47,color:#000;
    class Packet,Assess,Stop local;
    class Gate deterministic;
    class Workflow,Analyst deployed;
    class Review,EvalSet,Judge,Trace planned;
    class Human,NextSpec human;
```

The first deployment is one no-tools prompt agent, not a hidden multi-agent
workflow. The evidence analyst may restate only packet-cited facts; the
deterministic gate rejects invalid output regardless of how persuasive the
model response sounds. A planner or governance role can be added later only
through its own reviewed contract and approval; it is not implied by the first
analyst deployment.

Foundry Evaluations provides the LLM-as-judge layer for fixed test fixtures.
Its rubric should score whether an analyst response is grounded in the supplied
packet, honestly labels a one-seed smoke run as inconclusive, respects the
declared envelope, names a falsifiable success criterion, and preserves the
human-review requirement. It is not allowed to assign a game score, deem a
candidate mechanically audited, or approve a policy mutation.

Tracing records only redacted operational provenance—packet ID/hash, contract
and agent versions, role transition, decision status, and refusal reason. Raw
checkpoint state, the sibling checkout, credentials, and policy-writing tools
are outside the Foundry boundary.

## How to use these diagrams

- Start with diagrams 1 and 3 when returning after an interruption: they show
  the system's authority boundaries.
- Use diagram 2 when changing evaluator/caching code: it shows the audit
  invariant that must stay true.
- Use diagram 4 when designing the schema and evidence-packet JSON.
- Use diagram 5 before adding a second decision graph or contextual
  `seed_opportunity_value`.
- Use diagram 6 when deciding whether a new experiment is a draft, approved
  run, or historical record.
- Use diagram 7 when designing the prompt agent, evaluation fixtures, or
  review queue: it makes the LLM's limited role and the deterministic gates
  visible.
