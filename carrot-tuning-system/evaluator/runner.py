"""Deliberately incomplete orchestration boundary for local experiments.

The existing ``kaggriculture_eval`` package remains the proven simulation
engine. This module will eventually validate a declared experiment and call
those primitives; it must never become a second simulator or policy editor.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass, fields
import hashlib
import json
from numbers import Real
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


@dataclass(frozen=True)
class LocalRunRequest:
    """Explicit locations supplied to the local runner."""

    # The source-controlled JSON contract the future runner must read.
    spec_path: Path
    # An explicit sibling checkout prevents ambiguous imports of ``agents``.
    target_root: Path
    # Baseline caches are reused only from this explicit ignored local root.
    cache_root: Path
    # Generated evidence belongs in an ignored local directory, never in the spec.
    report_directory: Path


class ExperimentSpecValidationError(ValueError):
    """A declared experiment cannot safely proceed to later runner stages."""


class BaselineCachePreparationError(ExperimentSpecValidationError):
    """A required baseline cache cannot safely be reused by this run."""


class SpecReadError(ExperimentSpecValidationError):
    """The requested specification could not be read as JSON."""


class SchemaValidationSetupError(RuntimeError):
    """The checked-in schema cannot safely be used as a validator."""


@dataclass(frozen=True)
class SchemaValidationIssue:
    """One schema rule that the supplied JSON document violates."""

    path: str
    rule: str
    message: str


@dataclass(frozen=True)
class SchemaValidationResult:
    """Schema-validation facts; this record makes no authorization decision."""

    schema_path: Path
    schema_draft: str
    issues: tuple[SchemaValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return not self.issues


def read_spec(spec_path: Path) -> Any:
    """Read one source-controlled experiment JSON document.

    This deliberately distinguishes file/JSON failures from schema failures.
    It does not decide whether the parsed value is an experiment contract.
    """
    try:
        raw_specification = spec_path.read_text(encoding="utf-8")
    except OSError as error:
        raise SpecReadError(f"Could not read experiment specification: {spec_path}") from error

    try:
        return json.loads(raw_specification)
    except json.JSONDecodeError as error:
        raise SpecReadError(
            f"Experiment specification is not valid JSON: {spec_path}"
        ) from error


def validate_spec_schema(specification: Any, schema_path: Path) -> SchemaValidationResult:
    """Return every schema-v1 issue for an already-read specification.

    A broken schema is a setup failure and raises separately. A usable schema
    returns structured contract issues, so callers can present or enforce them
    without scraping printed validator diagnostics.
    """
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (OSError, json.JSONDecodeError, SchemaError) as error:
        raise SchemaValidationSetupError(f"Could not use schema: {schema_path}") from error

    validator = Draft202012Validator(schema)
    issues = tuple(
        SchemaValidationIssue(
            path=error.json_path,
            rule=str(error.validator),
            message=error.message,
        )
        for error in sorted(
            validator.iter_errors(specification),
            key=lambda error: (error.json_path, str(error.validator)),
        )
    )
    schema_draft = (
        schema.get("$schema", "not declared")
        if isinstance(schema, dict)
        else "not declared"
    )
    return SchemaValidationResult(schema_path, schema_draft, issues)


@dataclass(frozen=True)
class TargetFingerprintCheck:
    """One expected-versus-observed fact about the system under test."""

    label: str
    expected: str
    observed: str

    @property
    def matches(self) -> bool:
        return self.expected == self.observed


@dataclass(frozen=True)
class TargetFingerprintValidation:
    """Binding and fingerprint facts; this record makes no lifecycle decision."""

    target_root: Path
    binding: Any | None
    binding_error: str | None
    checks: tuple[TargetFingerprintCheck, ...]

    @property
    def is_match(self) -> bool:
        return self.binding_error is None and all(check.matches for check in self.checks)


def bind_and_validate_target(
    specification: dict[str, Any], target_root: Path
) -> TargetFingerprintValidation:
    """Bind one explicit checkout and return its fingerprint comparison facts.

    The parent evaluator owns the actual target binding. Passing an explicit
    path avoids ambient cwd or environment-variable selection. A binding
    failure remains structured data so a caller may present it before deciding
    how to enforce the stop.
    """
    try:
        from kaggriculture_eval.binding import bind_target
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Target validation needs the parent evaluator package. Run with "
            "PYTHONPATH=src:carrot-tuning-system or install the project package."
        ) from error

    try:
        binding = bind_target(target_root)
    except RuntimeError as error:
        return TargetFingerprintValidation(
            target_root=target_root.resolve(),
            binding=None,
            binding_error=str(error),
            checks=(),
        )

    expected = specification["target"]
    # Revision names committed history; hashes also catch relevant uncommitted
    # policy or engine edits at the same revision.
    checks = (
        TargetFingerprintCheck(
            "Git revision", expected["expected_revision"], binding.revision
        ),
        TargetFingerprintCheck(
            "Carrot policy SHA-256",
            expected["expected_shared_sha256"],
            binding.shared_sha256,
        ),
        TargetFingerprintCheck(
            "Game engine SHA-256",
            expected["expected_engine_sha256"],
            binding.engine_sha256,
        ),
    )
    return TargetFingerprintValidation(
        target_root=binding.root,
        binding=binding,
        binding_error=None,
        checks=checks,
    )


class TargetFingerprintMismatchError(ExperimentSpecValidationError):
    """The supplied Kaggriculture checkout is not the contract's target."""


@dataclass(frozen=True)
class LifecycleAuthorization:
    """The execution permission implied by a schema-valid lifecycle status."""

    declared_status: str
    is_authorized: bool
    reason: str
    human_decision_required: bool
    source_policy_mutation_authorized: bool
    candidate_expansion_authorized: bool


def authorize_lifecycle(specification: dict[str, Any]) -> LifecycleAuthorization:
    """Interpret lifecycle status without granting source-edit authority.

    Only the explicit ``approved`` status permits later local execution stages.
    A historical record remains an oracle, never automatic rerun permission.
    """
    status = specification["lifecycle_status"]
    governance = specification["governance"]
    reasons = {
        "approved": "The contract is explicitly approved for bounded local execution.",
        "historical_reproduction": (
            "Historical evidence is a regression oracle, not automatic rerun permission."
        ),
        "draft": "A draft contract has not received human approval.",
        "retired": "A retired contract must not be run again.",
    }
    return LifecycleAuthorization(
        declared_status=status,
        is_authorized=status == "approved",
        reason=reasons[status],
        human_decision_required=governance["human_decision_required"],
        source_policy_mutation_authorized=governance["source_policy_mutation_authorized"],
        candidate_expansion_authorized=governance["candidate_expansion_authorized"],
    )


class LifecycleAuthorizationError(ExperimentSpecValidationError):
    """The declared lifecycle does not permit simulator execution."""


@dataclass(frozen=True)
class ExecutionOperationAuthorization:
    """One operation-level decision derived from an already-valid contract."""

    operation: str
    declared_operations: tuple[str, ...]
    is_authorized: bool
    reason: str


def authorize_execution_operation(
    specification: dict[str, Any], operation: str
) -> ExecutionOperationAuthorization:
    """Return a fail-closed operation decision without doing any work.

    Lifecycle approval permits bounded local execution in principle. This
    separate gate prevents an orchestrator from inferring *which* simulator or
    evidence operation is allowed from a prose purpose, contract identifier, or
    similarly shaped candidate envelope.
    """
    authorization = specification.get("execution_authorization")
    operations = (
        tuple(authorization["operations"])
        if isinstance(authorization, dict)
        and isinstance(authorization.get("operations"), list)
        else ()
    )
    if not operations:
        return ExecutionOperationAuthorization(
            operation=operation,
            declared_operations=(),
            is_authorized=False,
            reason=(
                "Contract has no machine-readable execution authorization; "
                "refusing to infer operation authority from prose."
            ),
        )
    return ExecutionOperationAuthorization(
        operation=operation,
        declared_operations=operations,
        is_authorized=operation in operations,
        reason=(
            "Operation is explicitly declared by the contract."
            if operation in operations
            else "Operation is not declared by the contract."
        ),
    )


class ExecutionOperationAuthorizationError(ExperimentSpecValidationError):
    """The approved lifecycle does not grant the requested operation."""


@dataclass(frozen=True)
class LocalControlCheck:
    """One declared local control compared with the bound target or contract."""

    label: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class LocalControlValidation:
    """Local envelope facts; this record neither runs a game nor changes source."""

    parameter_name: str
    declared_baseline: float
    target_default: float | None
    candidate_count: int
    checks: tuple[LocalControlCheck, ...]

    @property
    def is_valid(self) -> bool:
        return all(check.passed for check in self.checks)


def validate_local_controls(
    specification: dict[str, Any], binding: Any
) -> LocalControlValidation:
    """Check the bounded in-memory control envelope against the bound target.

    The binding was fingerprinted before this call, so the policy class below
    belongs to the explicit checkout. This function inspects that class and the
    declared controls only; it does not create a cache, run a simulator, or
    override the lifecycle gate.
    """
    parameter = specification["parameter"]
    suite = specification["suite"]
    evaluation = specification["evaluation"]
    governance = specification["governance"]
    parameter_name = parameter["name"]
    parameter_class = binding.shared.CarrotParameters
    parameter_fields = {field.name: field for field in fields(parameter_class)}
    parameter_exists = parameter_name in parameter_fields
    target_default = (
        parameter_fields[parameter_name].default if parameter_exists else None
    )
    candidate_values = parameter["candidate_values"]
    known_conveyor = hasattr(binding.shared, "carrot_conveyor_agent")

    checks = (
        LocalControlCheck(
            "Parameter namespace",
            specification["decision_graph"]["parameter_namespace"]
            == parameter_class.__name__,
            "declared "
            f"{specification['decision_graph']['parameter_namespace']}; "
            f"target {parameter_class.__name__}",
        ),
        LocalControlCheck(
            "Declared parameter exists",
            parameter_exists,
            parameter_name if parameter_exists else f"unknown field: {parameter_name}",
        ),
        LocalControlCheck(
            "Baseline matches target default",
            parameter_exists and parameter["baseline_value"] == target_default,
            f"declared {parameter['baseline_value']}; target {target_default}",
        ),
        LocalControlCheck(
            "Candidate envelope",
            bool(candidate_values)
            and len(candidate_values) == len(set(candidate_values))
            and all(value != parameter["baseline_value"] for value in candidate_values),
            f"{len(candidate_values)} predeclared values; none may equal the baseline",
        ),
        LocalControlCheck(
            "Mutation mode",
            parameter["mutation_mode"] == "in_memory_single_field_override",
            parameter["mutation_mode"],
        ),
        LocalControlCheck(
            "Deterministic known opponent",
            suite["opponent_deterministic"]
            and suite["opponent_id"]
            == "target.agents.carrot.shared.carrot_conveyor_agent"
            and known_conveyor,
            suite["opponent_id"],
        ),
        LocalControlCheck(
            "Complete matched suite",
            bool(suite["seeds"])
            and len(suite["seeds"]) == len(set(suite["seeds"]))
            and set(suite["seats"]) == {0, 1}
            and suite["steps"] > 0,
            f"{len(suite['seeds'])} seeds; seats {suite['seats']}; "
            f"{suite['steps']} steps",
        ),
        LocalControlCheck(
            "Checkpoint and audit policy",
            evaluation["checkpoint_policy"] == "before_every_decision"
            and evaluation["reuse_no_divergence_baseline"]
            and evaluation["clean_audit_required"]
            and evaluation["result_storage"] == "local_ignored_var_directory",
            "checkpoint replay with required clean audits and local ignored output",
        ),
        LocalControlCheck(
            "Governance locks",
            governance["human_decision_required"]
            and not governance["source_policy_mutation_authorized"]
            and not governance["candidate_expansion_authorized"],
            "human decision required; no source mutation or candidate expansion",
        ),
    )
    return LocalControlValidation(
        parameter_name=parameter_name,
        declared_baseline=parameter["baseline_value"],
        target_default=target_default,
        candidate_count=len(candidate_values),
        checks=checks,
    )


class LocalControlValidationError(ExperimentSpecValidationError):
    """The contract's declared local envelope is not safe to execute."""


@dataclass(frozen=True)
class BaselineCacheEntry:
    """One planned baseline cache; its path need not exist yet."""

    seed: int
    seat: int
    path: Path


@dataclass(frozen=True)
class BaselineCachePlan:
    """A deterministic description of baseline caches, not cache contents."""

    group_id: str
    cache_directory: Path
    entries: tuple[BaselineCacheEntry, ...]


@dataclass(frozen=True)
class BaselineCacheState:
    """Read-only presence facts for one planned baseline-cache group."""

    plan: BaselineCachePlan
    present_entries: tuple[BaselineCacheEntry, ...]
    missing_entries: tuple[BaselineCacheEntry, ...]

    @property
    def is_complete(self) -> bool:
        return not self.missing_entries


@dataclass(frozen=True)
class BaselineCachePayloadCheck:
    """One provenance or structural fact about a decoded baseline cache."""

    label: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class BaselineCachePayloadValidation:
    """Structural cache facts; this record does not restore a simulator state."""

    entry: BaselineCacheEntry
    checks: tuple[BaselineCachePayloadCheck, ...]

    @property
    def is_valid(self) -> bool:
        return all(check.passed for check in self.checks)


@dataclass(frozen=True)
class BaselineCacheReadResult:
    """Read and structural-validation facts for one planned gzip cache."""

    entry: BaselineCacheEntry
    file_was_present: bool
    read_error: str | None
    payload_validation: BaselineCachePayloadValidation | None

    @property
    def is_reusable_candidate(self) -> bool:
        return (
            self.file_was_present
            and self.read_error is None
            and self.payload_validation is not None
            and self.payload_validation.is_valid
        )


@dataclass(frozen=True)
class BaselineCacheAction:
    """One reuse-or-materialize-later decision with an auditable reason."""

    entry: BaselineCacheEntry
    decision: str
    reason: str


@dataclass(frozen=True)
class BaselineCachePreparationPlan:
    """A complete, non-executing disposition for one cache group."""

    cache_plan: BaselineCachePlan
    actions: tuple[BaselineCacheAction, ...]

    @property
    def reusable_actions(self) -> tuple[BaselineCacheAction, ...]:
        return tuple(action for action in self.actions if action.decision == "reuse")

    @property
    def materialize_actions(self) -> tuple[BaselineCacheAction, ...]:
        return tuple(
            action for action in self.actions if action.decision == "materialize"
        )


@dataclass(frozen=True)
class BaselinePreparationSelection:
    """One fully gated baseline-preparation plan with at most one next action.

    This is deliberately a planning record. It establishes the exact action
    that a later, separately authorized materialization call could perform, but
    it does not invoke the simulator or create a cache.
    """

    specification: dict[str, Any]
    binding: Any
    lifecycle: LifecycleAuthorization
    operation: ExecutionOperationAuthorization
    controls: LocalControlValidation
    cache_plan: BaselineCachePlan
    cache_state: BaselineCacheState
    cache_preparation: BaselineCachePreparationPlan
    selected_action: BaselineCacheAction | None


@dataclass(frozen=True)
class BaselineMaterializationResult:
    """Facts returned only after one baseline cache has been written."""

    action: BaselineCacheAction
    cache_path: Path
    checkpoint_count: int
    outcome: dict[str, Any]


@dataclass(frozen=True)
class LocalRunPreflight:
    """All reviewed non-simulator facts required before candidate evaluation."""

    specification: dict[str, Any]
    binding: Any
    lifecycle: LifecycleAuthorization
    controls: LocalControlValidation
    cache_plan: BaselineCachePlan
    cache_preparation: BaselineCachePreparationPlan


@dataclass(frozen=True)
class LocalCandidateBatch:
    """Exact audited results for one approved candidate envelope.

    This is intentionally an intermediate execution record. It contains the
    per-match facts needed by a later evidence-packet stage, but it does not
    aggregate, write a packet, choose a candidate, or authorize a source edit.
    """

    preflight: LocalRunPreflight
    baseline_outcomes: dict[tuple[int, int], dict[str, Any]]
    audited_results: tuple[dict[str, Any], ...]


def plan_baseline_caches(
    specification: dict[str, Any], binding: Any, cache_root: Path
) -> BaselineCachePlan:
    """Derive cache identities and paths without writing or evaluating anything.

    The cache identity contains every fact whose change would make reuse unsafe.
    The returned paths are only a plan; no directory, cache, or simulator state
    is created by this function.
    """
    suite = specification["suite"]
    parameter = specification["parameter"]
    identity = {
        "cache_format": "baseline-match-v1",
        # A successor must name the baseline envelope it intends to reuse.
        # The fallback preserves pre-existing cache locations for contracts
        # created before that explicit reuse anchor existed.
        "experiment_id": specification.get(
            "baseline_cache_contract_id", specification["experiment_id"]
        ),
        "target_revision": binding.revision,
        "shared_sha256": binding.shared_sha256,
        "engine_sha256": binding.engine_sha256,
        "baseline_parameter": {
            parameter["name"]: parameter["baseline_value"],
        },
        "suite": {
            "opponent_id": suite["opponent_id"],
            "seeds": suite["seeds"],
            "seats": suite["seats"],
            "steps": suite["steps"],
        },
        "checkpoint_policy": specification["evaluation"]["checkpoint_policy"],
    }
    canonical_identity = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    group_id = hashlib.sha256(canonical_identity.encode("utf-8")).hexdigest()
    cache_directory = cache_root / "baseline-caches" / group_id
    entries = tuple(
        BaselineCacheEntry(
            seed=seed,
            seat=seat,
            path=cache_directory / f"seed-{seed}-seat-{seat}.json.gz",
        )
        for seed in suite["seeds"]
        for seat in suite["seats"]
    )
    return BaselineCachePlan(group_id, cache_directory, entries)


def inspect_baseline_cache_state(plan: BaselineCachePlan) -> BaselineCacheState:
    """Classify planned paths by presence without opening or creating them.

    A present file is only a cache candidate. Its gzip payload and its
    provenance require a later validation gate before the runner may reuse it.
    """
    present_entries = tuple(entry for entry in plan.entries if entry.path.is_file())
    missing_entries = tuple(entry for entry in plan.entries if not entry.path.is_file())
    return BaselineCacheState(plan, present_entries, missing_entries)


def validate_baseline_cache_payload(
    cache: dict[str, Any],
    entry: BaselineCacheEntry,
    specification: dict[str, Any],
    binding: Any,
) -> BaselineCachePayloadValidation:
    """Check decoded cache provenance and shape without restoring game state."""
    cache_binding = cache.get("binding")
    match = cache.get("match")
    turns = cache.get("turns")
    outcome = cache.get("outcome")
    expected_outcome_keys = {
        "decision_reward",
        "opponent_reward",
        "decision_status",
        "opponent_status",
    }
    checks = (
        BaselineCachePayloadCheck(
            "Cache schema and kind",
            cache.get("schema_version") == 1 and cache.get("kind") == "baseline-match",
            f"schema {cache.get('schema_version')}; kind {cache.get('kind')}",
        ),
        BaselineCachePayloadCheck(
            "Bound target fingerprint",
            isinstance(cache_binding, dict)
            and cache_binding.get("target_root") == str(binding.root)
            and cache_binding.get("target_revision") == binding.revision
            and cache_binding.get("shared_sha256") == binding.shared_sha256
            and cache_binding.get("engine_sha256") == binding.engine_sha256,
            "target root, revision, and both source hashes must match",
        ),
        BaselineCachePayloadCheck(
            "Planned match identity",
            isinstance(match, dict)
            and match.get("seed") == entry.seed
            and match.get("decision_player") == entry.seat
            and match.get("steps") == specification["suite"]["steps"]
            and match.get("opponent") == specification["suite"]["opponent_id"]
            and match.get("policy")
            == "target.agents.carrot.shared.carrot_decision_agent"
            and match.get("configuration")
            == {
                "episodeSteps": specification["suite"]["steps"],
                "seed": entry.seed,
            },
            f"seed {entry.seed}; seat {entry.seat}; {specification['suite']['steps']} steps",
        ),
        BaselineCachePayloadCheck(
            "Checkpoint-record shape",
            isinstance(turns, list)
            and bool(turns)
            and all(
                isinstance(turn, dict)
                and {"turn", "checkpoint_state", "observation", "baseline_action"}
                <= set(turn)
                for turn in turns
            ),
            "nonempty records with checkpoint, observation, and baseline action",
        ),
        BaselineCachePayloadCheck(
            "Outcome shape",
            isinstance(outcome, dict) and expected_outcome_keys <= set(outcome),
            "decision/opponent reward and status fields",
        ),
    )
    return BaselineCachePayloadValidation(entry, checks)


def read_and_validate_baseline_cache(
    entry: BaselineCacheEntry, specification: dict[str, Any], binding: Any
) -> BaselineCacheReadResult:
    """Read one present gzip cache and validate it without restoring game state."""
    if not entry.path.is_file():
        return BaselineCacheReadResult(entry, False, None, None)

    from kaggriculture_eval.checkpoint import read_baseline

    try:
        cache = read_baseline(entry.path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return BaselineCacheReadResult(entry, True, str(error), None)

    payload_validation = validate_baseline_cache_payload(
        cache, entry, specification, binding
    )
    return BaselineCacheReadResult(entry, True, None, payload_validation)


def read_validated_baseline_outcome(
    entry: BaselineCacheEntry, specification: dict[str, Any], binding: Any
) -> dict[str, Any]:
    """Return an outcome only after revalidating its exact reusable cache.

    This is deliberately a second execution-boundary check. A cache that was
    valid during a prior preflight can still be replaced before the batch runs.
    """
    cache_read = read_and_validate_baseline_cache(entry, specification, binding)
    if not cache_read.is_reusable_candidate:
        raise BaselineCachePreparationError(
            "Candidate evaluation is blocked because a baseline cache changed or "
            f"became invalid: seed {entry.seed}, seat {entry.seat}"
        )
    from kaggriculture_eval.checkpoint import read_baseline

    return read_baseline(entry.path)["outcome"]


def plan_baseline_cache_preparation(
    state: BaselineCacheState, read_results: tuple[BaselineCacheReadResult, ...]
) -> BaselineCachePreparationPlan:
    """Choose reuse or later materialization without executing either path."""
    results_by_path = {result.entry.path: result for result in read_results}
    present_paths = {entry.path for entry in state.present_entries}
    actions: list[BaselineCacheAction] = []
    for entry in state.plan.entries:
        if entry.path not in present_paths:
            actions.append(
                BaselineCacheAction(entry, "materialize", "cache file is missing")
            )
            continue

        result = results_by_path.get(entry.path)
        if result is None:
            actions.append(
                BaselineCacheAction(
                    entry, "materialize", "present cache was not read and validated"
                )
            )
        elif result.is_reusable_candidate:
            actions.append(
                BaselineCacheAction(
                    entry, "reuse", "gzip decoded and structural checks passed"
                )
            )
        elif result.read_error is not None:
            actions.append(
                BaselineCacheAction(
                    entry, "materialize", f"cache could not be read: {result.read_error}"
                )
            )
        else:
            actions.append(
                BaselineCacheAction(
                    entry, "materialize", "decoded cache failed structural validation"
                )
            )
    return BaselineCachePreparationPlan(state.plan, tuple(actions))


def materialize_selected_baseline(
    action: BaselineCacheAction, specification: dict[str, Any], binding: Any
) -> BaselineMaterializationResult:
    """Run and persist exactly one approved missing baseline cache.

    This function has deliberate simulator and filesystem side effects. The
    caller must have already enforced lifecycle and cache-preparation gates.
    """
    if action.decision != "materialize":
        raise ValueError("only a materialize action may create a baseline cache")
    # A valid cache must be reused, never silently replaced by a new baseline.
    if action.entry.path.exists():
        raise FileExistsError(
            f"refusing to overwrite existing cache: {action.entry.path}"
        )

    # Import only at execution time: all planning and review remains simulator-free.
    from kaggriculture_eval.checkpoint import baseline_match, write_baseline

    suite = specification["suite"]
    # The selected entry supplies the only seed/seat pair this invocation may run.
    cache = baseline_match(
        binding,
        seed=action.entry.seed,
        seat=action.entry.seat,
        steps=suite["steps"],
        opponent=binding.shared.carrot_conveyor_agent,
        opponent_id=suite["opponent_id"],
    )
    write_baseline(cache, action.entry.path)
    return BaselineMaterializationResult(
        action=action,
        cache_path=action.entry.path,
        checkpoint_count=len(cache["turns"]),
        outcome=cache["outcome"],
    )


@dataclass(frozen=True)
class EvidenceMatchRecord:
    """One audited candidate/match fact retained in a local evidence packet."""

    candidate_value: float
    seed: int
    seat: int
    fast_mode: str
    first_divergence_turn: int | None
    suffix_actions: int
    baseline_decision_reward: float
    candidate_decision_reward: float
    paired_decision_delta: float
    opponent_reward: float
    replay_elapsed_seconds: float
    suffix_elapsed_seconds: float
    clean_actions_run: int
    clean_elapsed_seconds: float
    audit_status: str


@dataclass(frozen=True)
class EvidenceAggregate:
    """A descriptive paired summary, deliberately not a recommendation."""

    candidate_value: float
    match_count: int
    all_audits_passed: bool
    mean_candidate_decision_reward: float
    mean_paired_decision_delta: float
    divergent_match_count: int
    total_suffix_actions: int


@dataclass(frozen=True)
class LocalSmokeEvidencePacket:
    """Serializable evidence for one complete, already-audited smoke envelope."""

    packet_schema_version: int
    experiment_id: str
    target_revision: str
    target_shared_sha256: str
    target_engine_sha256: str
    parameter_name: str
    baseline_value: float
    suite_seeds: tuple[int, ...]
    suite_seats: tuple[int, ...]
    suite_steps: int
    per_match: tuple[EvidenceMatchRecord, ...]
    aggregates: tuple[EvidenceAggregate, ...]
    all_audits_passed: bool
    interpretation_status: str
    source_policy_mutation_authorized: bool

    def as_jsonable(self) -> dict[str, Any]:
        """Return data for the reviewed local writer; this method has no side effects."""
        return asdict(self)


@dataclass(frozen=True)
class EvidencePacketWriteResult:
    """Facts about one newly created local evidence file."""

    path: Path
    byte_count: int
    sha256: str


@dataclass(frozen=True)
class EvidencePacketRepeatInspection:
    """Read-only facts about a proposed packet destination on a repeat call."""

    path: Path
    status: str
    expected_sha256: str
    observed_sha256: str | None
    expected_byte_count: int
    observed_byte_count: int | None
    detail: str


@dataclass(frozen=True)
class LocalCompletedRun:
    """One batch whose evidence packet was newly written and recorded.

    The batch remains available for callers that need the audited per-match
    facts, while the packet and write receipt make the durable boundary
    explicit. This record does not interpret the packet or authorize policy
    mutation.
    """

    batch: LocalCandidateBatch
    evidence_packet: LocalSmokeEvidencePacket
    packet_write: EvidencePacketWriteResult


def build_local_smoke_evidence_packet(
    specification: dict[str, Any],
    binding: Any,
    audited_results: tuple[dict[str, Any], ...],
    baseline_outcomes: dict[tuple[int, int], dict[str, Any]],
) -> LocalSmokeEvidencePacket:
    """Validate exact audited coverage and assemble descriptive smoke evidence.

    This is a pure transformation. It does not read a cache, run a simulator,
    write a file, interpret the aggregate, or authorize a policy change.
    """
    parameter = specification["parameter"]
    suite = specification["suite"]
    declared_values = tuple(float(value) for value in parameter["candidate_values"])
    expected_matches = {
        (candidate_value, seed, seat)
        for candidate_value in declared_values
        for seed in suite["seeds"]
        for seat in suite["seats"]
    }
    observed_matches = {
        (
            float(result["candidate"]["new_value"]),
            result["match"]["seed"],
            result["match"]["decision_player"],
        )
        for result in audited_results
    }
    # Exact coverage rejects missing, duplicated, and out-of-envelope results.
    if len(audited_results) != len(observed_matches) or observed_matches != expected_matches:
        raise ValueError("audited results do not exactly cover the approved smoke envelope")

    records = []
    for result in audited_results:
        candidate = result["candidate"]
        match = result["match"]
        clean_audit = result.get("clean_audit")
        match_key = (match["seed"], match["decision_player"])

        # Evidence requires the independent full-run oracle, not only the fast path.
        if result.get("audit_status") != "passed" or clean_audit is None:
            raise ValueError(f"result {match_key} is not a passing clean audit")
        if clean_audit["outcome"] != result["outcome"]:
            raise ValueError(f"fast and clean outcomes differ for {match_key}")
        if candidate["name"] != parameter["name"] or candidate["old_value"] != parameter["baseline_value"]:
            raise ValueError(f"result {match_key} does not use the declared parameter baseline")
        if result["candidate_source_revision"] != binding.revision:
            raise ValueError(f"candidate target revision differs for {match_key}")
        if match_key not in baseline_outcomes:
            raise ValueError(f"missing baseline outcome for {match_key}")

        is_reused = result["mode"] == "reused-baseline"
        is_suffix = result["mode"] == "restored-suffix"
        if not (is_reused or is_suffix):
            raise ValueError(f"unknown fast-path mode for {match_key}: {result['mode']}")
        if is_reused and (result["first_divergence_turn"] is not None or result["suffix_actions"] != 0):
            raise ValueError(f"reused baseline has inconsistent divergence facts for {match_key}")
        if is_suffix and (result["first_divergence_turn"] is None or result["suffix_actions"] <= 0):
            raise ValueError(f"restored suffix has inconsistent divergence facts for {match_key}")

        baseline = baseline_outcomes[match_key]
        outcome = result["outcome"]
        records.append(EvidenceMatchRecord(
            candidate_value=float(candidate["new_value"]),
            seed=match["seed"],
            seat=match["decision_player"],
            fast_mode=result["mode"],
            first_divergence_turn=result["first_divergence_turn"],
            suffix_actions=result["suffix_actions"],
            baseline_decision_reward=float(baseline["decision_reward"]),
            candidate_decision_reward=float(outcome["decision_reward"]),
            paired_decision_delta=float(outcome["decision_reward"] - baseline["decision_reward"]),
            opponent_reward=float(outcome["opponent_reward"]),
            replay_elapsed_seconds=float(result["replay_elapsed_seconds"]),
            suffix_elapsed_seconds=float(result["suffix_elapsed_seconds"]),
            clean_actions_run=clean_audit["actions_run"],
            clean_elapsed_seconds=float(clean_audit["elapsed_seconds"]),
            audit_status=result["audit_status"],
        ))

    ordered_records = tuple(sorted(records, key=lambda record: (
        declared_values.index(record.candidate_value), record.seed, record.seat
    )))
    aggregates = tuple(
        EvidenceAggregate(
            candidate_value=value,
            match_count=len(candidate_records := tuple(
                record for record in ordered_records if record.candidate_value == value
            )),
            all_audits_passed=all(record.audit_status == "passed" for record in candidate_records),
            mean_candidate_decision_reward=sum(
                record.candidate_decision_reward for record in candidate_records
            ) / len(candidate_records),
            mean_paired_decision_delta=sum(
                record.paired_decision_delta for record in candidate_records
            ) / len(candidate_records),
            divergent_match_count=sum(
                record.first_divergence_turn is not None for record in candidate_records
            ),
            total_suffix_actions=sum(record.suffix_actions for record in candidate_records),
        )
        for value in declared_values
    )
    return LocalSmokeEvidencePacket(
        packet_schema_version=1,
        experiment_id=specification["experiment_id"],
        target_revision=binding.revision,
        target_shared_sha256=binding.shared_sha256,
        target_engine_sha256=binding.engine_sha256,
        parameter_name=parameter["name"],
        baseline_value=float(parameter["baseline_value"]),
        suite_seeds=tuple(suite["seeds"]),
        suite_seats=tuple(suite["seats"]),
        suite_steps=suite["steps"],
        per_match=ordered_records,
        aggregates=aggregates,
        all_audits_passed=all(record.audit_status == "passed" for record in ordered_records),
        interpretation_status="descriptive-smoke-only; human interpretation required",
        source_policy_mutation_authorized=specification["governance"]["source_policy_mutation_authorized"],
    )


def write_local_smoke_evidence_packet(
    packet: LocalSmokeEvidencePacket, report_directory: Path
) -> EvidencePacketWriteResult:
    """Write one immutable local packet, refusing incomplete evidence or overwrite.

    The caller supplies a local ignored report directory. The writer creates
    only its ``evidence-packets`` child directory and a new JSON file; it never
    runs Kaggriculture, changes policy source, or replaces earlier evidence.
    """
    if not packet.per_match or not packet.all_audits_passed:
        raise ValueError("only a non-empty packet with all clean audits passed may be written")
    if any(record.audit_status != "passed" for record in packet.per_match):
        raise ValueError("packet contains a non-passing per-match audit")
    if any(not aggregate.all_audits_passed for aggregate in packet.aggregates):
        raise ValueError("packet contains an aggregate with a failed audit")
    if packet.source_policy_mutation_authorized:
        raise ValueError("evidence packet must not grant source-policy mutation authority")

    destination = report_directory / "evidence-packets" / f"{packet.experiment_id}.json"
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite existing evidence packet: {destination}")

    encoded = _canonical_packet_bytes(packet)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation preserves the packet as an immutable evidence artifact.
    with destination.open("x", encoding="utf-8") as stream:
        stream.write(encoded.decode("utf-8"))
    return EvidencePacketWriteResult(
        path=destination,
        byte_count=len(encoded),
        sha256=hashlib.sha256(encoded).hexdigest(),
    )


def _canonical_packet_bytes(packet: LocalSmokeEvidencePacket) -> bytes:
    """Return the reviewed JSON representation used by writer and inspection."""
    return (json.dumps(packet.as_jsonable(), indent=2, sort_keys=True) + "\n").encode("utf-8")


def inspect_local_smoke_evidence_packet_repeat(
    packet: LocalSmokeEvidencePacket, report_directory: Path
) -> EvidencePacketRepeatInspection:
    """Describe a packet destination without reusing, replacing, or writing it.

    An exact existing packet proves only that the same canonical bytes are
    already present. It is deliberately not returned as a successful rerun or
    an implicit reuse decision. A caller must surface the status for review;
    the exclusive writer remains the only creation path and will still refuse
    every existing destination.
    """
    destination = report_directory / "evidence-packets" / f"{packet.experiment_id}.json"
    expected = _canonical_packet_bytes(packet)
    expected_sha256 = hashlib.sha256(expected).hexdigest()
    if not destination.exists():
        return EvidencePacketRepeatInspection(
            path=destination,
            status="missing",
            expected_sha256=expected_sha256,
            observed_sha256=None,
            expected_byte_count=len(expected),
            observed_byte_count=None,
            detail="No existing packet; an exclusive first write may be attempted.",
        )
    try:
        observed = destination.read_bytes()
    except OSError as error:
        return EvidencePacketRepeatInspection(
            path=destination,
            status="unreadable",
            expected_sha256=expected_sha256,
            observed_sha256=None,
            expected_byte_count=len(expected),
            observed_byte_count=None,
            detail=f"Existing packet could not be read: {error}",
        )
    observed_sha256 = hashlib.sha256(observed).hexdigest()
    exact_match = observed == expected
    return EvidencePacketRepeatInspection(
        path=destination,
        status="exact_match" if exact_match else "conflict",
        expected_sha256=expected_sha256,
        observed_sha256=observed_sha256,
        expected_byte_count=len(expected),
        observed_byte_count=len(observed),
        detail=(
            "Existing canonical bytes match; human review is required before any follow-up."
            if exact_match
            else "Existing bytes differ; stop without overwrite or reuse."
        ),
    )


def complete_local_candidate_batch(
    batch: LocalCandidateBatch, report_directory: Path
) -> LocalCompletedRun:
    """Persist one exact, already-audited batch as immutable local evidence.

    This is deliberately a completion seam, not a second evaluator. It uses
    only the batch's established preflight, baseline outcomes, and clean-audit
    results. Packet validation runs before the writer, so incomplete or
    mismatched evidence cannot create a file. The writer then creates one
    contract-named packet exclusively and refuses a pre-existing destination.

    It does not read a specification, bind a target, materialize a cache, run
    Kaggriculture, interpret aggregate results, or alter source policy.
    """
    packet = build_local_smoke_evidence_packet(
        batch.preflight.specification,
        batch.preflight.binding,
        batch.audited_results,
        batch.baseline_outcomes,
    )
    # The only side effect is delegated to the reviewed exclusive writer.
    packet_write = write_local_smoke_evidence_packet(packet, report_directory)
    return LocalCompletedRun(
        batch=batch,
        evidence_packet=packet,
        packet_write=packet_write,
    )


class CandidateAuditMismatchError(RuntimeError):
    """A fast candidate result disagreed with its required clean rerun."""


def select_declared_candidate_override(
    specification: dict[str, Any], candidate_value: Real
) -> dict[str, float]:
    """Return one declared in-memory override without reading a cache or running a game."""
    # Python considers True a number; it is still not a meaningful policy value.
    if isinstance(candidate_value, bool) or not isinstance(candidate_value, Real):
        raise ValueError("candidate value must be a real number")

    parameter = specification["parameter"]
    declared_values = tuple(parameter["candidate_values"])
    resolved_value = float(candidate_value)
    # This is the envelope gate: no cache or simulator work precedes it.
    if resolved_value not in declared_values:
        raise ValueError(
            f"candidate {resolved_value} is not declared; allowed values: {declared_values}"
        )
    return {parameter["name"]: resolved_value}


def _validate_declared_candidate_match(
    specification: dict[str, Any], seed: int, seat: int
) -> None:
    """Reject an entry outside the approved matched suite before evaluation."""
    suite = specification["suite"]
    if seed not in suite["seeds"] or seat not in suite["seats"]:
        raise ValueError(
            f"baseline entry {(seed, seat)} is outside the approved suite"
        )


def evaluate_declared_candidate_from_cache(
    specification: dict[str, Any],
    binding: Any,
    entry: BaselineCacheEntry,
    override: dict[str, float],
) -> dict[str, Any]:
    """Return one unaudited fast result from an exact, validated baseline cache."""
    if len(override) != 1:
        raise ValueError("a candidate override must contain exactly one field")
    name, value = next(iter(override.items()))
    if select_declared_candidate_override(specification, value) != override:
        raise ValueError("candidate override does not match the approved parameter")
    _validate_declared_candidate_match(specification, entry.seed, entry.seat)

    # A present path is not sufficient: target/match provenance must pass before reuse.
    cache_read = read_and_validate_baseline_cache(entry, specification, binding)
    if not cache_read.is_reusable_candidate:
        raise ValueError("candidate evaluation requires a reusable validated baseline cache")

    # Imports stay at the actual execution boundary; selection and validation remain lightweight.
    from kaggriculture_eval.checkpoint import evaluate_cached, read_baseline

    cache = read_baseline(entry.path)
    result = evaluate_cached(
        binding,
        cache,
        override,
        opponent=binding.shared.carrot_conveyor_agent,
    )
    if result.get("audit_status") != "not-run":
        raise AssertionError("fast candidate evaluation must remain unaudited")
    return result


def audit_declared_candidate_result(
    specification: dict[str, Any], binding: Any, fast_result: dict[str, Any], override: dict[str, float]
) -> dict[str, Any]:
    """Require one matching clean rerun and fail closed if it disagrees with the fast result."""
    if fast_result.get("audit_status") != "not-run":
        raise ValueError("a clean audit requires an unaudited fast result")
    if len(override) != 1:
        raise ValueError("a candidate override must contain exactly one field")
    name, value = next(iter(override.items()))
    if select_declared_candidate_override(specification, value) != override:
        raise ValueError("clean audit override does not match the declared candidate")

    expected_candidate = {
        "name": name,
        "old_value": specification["parameter"]["baseline_value"],
        "new_value": float(value),
    }
    if fast_result.get("candidate") != expected_candidate:
        raise ValueError("fast result does not correspond to the declared audit override")

    match = fast_result["match"]
    _validate_declared_candidate_match(
        specification, match["seed"], match["decision_player"]
    )
    if match["steps"] != specification["suite"]["steps"]:
        raise ValueError("fast result steps differ from the approved suite")
    if fast_result.get("candidate_source_revision") != binding.revision:
        raise ValueError("fast result target revision differs from the approved binding")

    from kaggriculture_eval.checkpoint import audit_cached

    audited = audit_cached(
        binding,
        deepcopy(fast_result),
        override,
        opponent=binding.shared.carrot_conveyor_agent,
    )
    if audited.get("audit_status") != "passed":
        raise CandidateAuditMismatchError(
            f"clean audit failed for {(match['seed'], match['decision_player'])}: {audited}"
        )
    return audited


def evaluate_and_audit_declared_candidate(
    specification: dict[str, Any], binding: Any, entry: BaselineCacheEntry, candidate_value: Real
) -> dict[str, Any]:
    """Run exactly one declared candidate/match pair and require its clean audit."""
    override = select_declared_candidate_override(specification, candidate_value)
    fast_result = evaluate_declared_candidate_from_cache(
        specification, binding, entry, override
    )
    return audit_declared_candidate_result(specification, binding, fast_result, override)


class LocalInnerLoopAdapter:
    """Coordinate a bounded local experiment after its implementation is reviewed.

    It can currently read and schema-validate a specification, then bind and
    fingerprint the explicitly supplied target, enforce lifecycle authorization,
    validate the local envelope, plan and inspect deterministic cache paths,
    validate and read cache payloads, record fail-closed preparation decisions,
    expose the reviewed one-entry materializer, bounded candidate evaluation
    and clean-audit helpers, and a reviewed evidence-packet writer. Its
    orchestrating ``run`` method does not invoke simulator or evidence-writing
    stages yet.
    """

    @staticmethod
    def schema_path() -> Path:
        """Locate the versioned contract beside this reusable adapter package."""
        return Path(__file__).resolve().parents[1] / "experiments/schema/experiment-spec-v1.schema.json"

    def read_and_validate_spec(self, spec_path: Path) -> dict[str, Any]:
        """Orchestrate the reviewed read and schema-validation functions."""
        specification = read_spec(spec_path)
        validation = validate_spec_schema(specification, self.schema_path())
        if not validation.is_valid:
            details = "; ".join(
                f"{issue.path}: {issue.message}" for issue in validation.issues
            )
            raise ExperimentSpecValidationError(
                f"Experiment specification does not satisfy schema v1: {details}"
            )

        if not isinstance(specification, dict):
            # Schema v1's root type already guards this. The assertion narrows
            # the reusable orchestrator's return type for later stages.
            raise AssertionError("A schema-valid experiment specification must be an object.")
        return specification

    def bind_and_validate_target(
        self, specification: dict[str, Any], target_root: Path
    ) -> Any:
        """Enforce the reviewed target comparison before later runner stages."""
        validation = bind_and_validate_target(specification, target_root)
        if validation.binding_error is not None:
            raise TargetFingerprintMismatchError(
                f"Could not bind the declared Kaggriculture target: {target_root}; "
                f"{validation.binding_error}"
            )
        mismatches = [
            f"{check.label}: expected {check.expected}, observed {check.observed}"
            for check in validation.checks
            if not check.matches
        ]
        if mismatches:
            raise TargetFingerprintMismatchError(
                "Target fingerprint differs from the experiment contract: "
                + "; ".join(mismatches)
            )
        if validation.binding is None:
            raise AssertionError("A matching target fingerprint requires a binding object.")
        return validation.binding

    def authorize_lifecycle(self, specification: dict[str, Any]) -> LifecycleAuthorization:
        """Enforce the reviewed lifecycle result before simulation can begin."""
        authorization = authorize_lifecycle(specification)
        if not authorization.is_authorized:
            raise LifecycleAuthorizationError(
                f"Lifecycle '{authorization.declared_status}' is not authorized: "
                f"{authorization.reason}"
            )
        return authorization

    def authorize_execution_operation(
        self, specification: dict[str, Any], operation: str
    ) -> ExecutionOperationAuthorization:
        """Enforce explicit operation authority before an orchestration side effect."""
        authorization = authorize_execution_operation(specification, operation)
        if not authorization.is_authorized:
            raise ExecutionOperationAuthorizationError(
                f"Operation '{operation}' is not authorized: {authorization.reason}"
            )
        return authorization

    def validate_local_controls(
        self, specification: dict[str, Any], binding: Any
    ) -> LocalControlValidation:
        """Enforce the reviewed local controls before baseline creation."""
        validation = validate_local_controls(specification, binding)
        failures = [
            f"{check.label}: {check.detail}"
            for check in validation.checks
            if not check.passed
        ]
        if failures:
            raise LocalControlValidationError(
                "Local experiment controls are invalid: " + "; ".join(failures)
            )
        return validation

    def plan_baseline_caches(
        self, specification: dict[str, Any], binding: Any, cache_root: Path
    ) -> BaselineCachePlan:
        """Plan cache paths after all reviewed pre-simulation gates pass."""
        return plan_baseline_caches(specification, binding, cache_root)

    def inspect_baseline_cache_state(
        self, plan: BaselineCachePlan
    ) -> BaselineCacheState:
        """Inspect planned cache paths without trusting or materializing them."""
        return inspect_baseline_cache_state(plan)

    def validate_baseline_cache_payload(
        self,
        cache: dict[str, Any],
        entry: BaselineCacheEntry,
        specification: dict[str, Any],
        binding: Any,
    ) -> BaselineCachePayloadValidation:
        """Validate decoded cache data before any reuse decision."""
        return validate_baseline_cache_payload(cache, entry, specification, binding)

    def read_and_validate_baseline_cache(
        self, entry: BaselineCacheEntry, specification: dict[str, Any], binding: Any
    ) -> BaselineCacheReadResult:
        """Read and structurally validate a cache without making a reuse decision."""
        return read_and_validate_baseline_cache(entry, specification, binding)

    def read_validated_baseline_outcome(
        self, entry: BaselineCacheEntry, specification: dict[str, Any], binding: Any
    ) -> dict[str, Any]:
        """Revalidate one cache at execution time and return its baseline outcome."""
        return read_validated_baseline_outcome(entry, specification, binding)

    def plan_baseline_cache_preparation(
        self,
        state: BaselineCacheState,
        read_results: tuple[BaselineCacheReadResult, ...],
    ) -> BaselineCachePreparationPlan:
        """Record reuse/materialize-later decisions without materializing caches."""
        return plan_baseline_cache_preparation(state, read_results)

    def plan_baseline_preparation(
        self, request: LocalRunRequest
    ) -> BaselinePreparationSelection:
        """Select at most one missing baseline action without materializing it.

        The request must name a schema-valid, explicitly approved contract that
        authorizes only the baseline-cache-preparation operation. Every present
        cache is decoded and structurally checked. A present but invalid cache
        is a diagnostic stop—not permission to replace evidence. Missing caches
        are considered in the contract's deterministic seed/seat order, and
        only the first is selected for a later materialization boundary.
        """
        specification = self.read_and_validate_spec(request.spec_path)
        binding = self.bind_and_validate_target(specification, request.target_root)
        lifecycle = self.authorize_lifecycle(specification)
        operation = self.authorize_execution_operation(
            specification, "baseline_cache_preparation"
        )
        controls = self.validate_local_controls(specification, binding)
        cache_plan = self.plan_baseline_caches(
            specification, binding, request.cache_root
        )
        cache_state = self.inspect_baseline_cache_state(cache_plan)
        read_results = tuple(
            self.read_and_validate_baseline_cache(entry, specification, binding)
            for entry in cache_state.present_entries
        )

        invalid_existing = tuple(
            result for result in read_results if not result.is_reusable_candidate
        )
        if invalid_existing:
            details = "; ".join(
                f"seed {result.entry.seed}, seat {result.entry.seat}: "
                f"{result.read_error or 'structural validation failed'}"
                for result in invalid_existing
            )
            raise BaselineCachePreparationError(
                "Baseline preparation refuses to replace a present invalid cache: "
                + details
            )

        preparation = self.plan_baseline_cache_preparation(cache_state, read_results)
        # Cache planning follows the contract's seed/seat order, not outcomes.
        selected_action = next(iter(preparation.materialize_actions), None)
        return BaselinePreparationSelection(
            specification=specification,
            binding=binding,
            lifecycle=lifecycle,
            operation=operation,
            controls=controls,
            cache_plan=cache_plan,
            cache_state=cache_state,
            cache_preparation=preparation,
            selected_action=selected_action,
        )

    def materialize_selected_baseline(
        self, action: BaselineCacheAction, specification: dict[str, Any], binding: Any
    ) -> BaselineMaterializationResult:
        """Materialize one selected action once orchestration is reviewed."""
        return materialize_selected_baseline(action, specification, binding)

    def select_declared_candidate_override(
        self, specification: dict[str, Any], candidate_value: Real
    ) -> dict[str, float]:
        """Select one approved in-memory candidate without evaluation."""
        return select_declared_candidate_override(specification, candidate_value)

    def evaluate_and_audit_declared_candidate(
        self,
        specification: dict[str, Any],
        binding: Any,
        entry: BaselineCacheEntry,
        candidate_value: Real,
    ) -> dict[str, Any]:
        """Evaluate exactly one approved match and require its clean audit."""
        return evaluate_and_audit_declared_candidate(
            specification, binding, entry, candidate_value
        )

    def build_local_smoke_evidence_packet(
        self,
        specification: dict[str, Any],
        binding: Any,
        audited_results: tuple[dict[str, Any], ...],
        baseline_outcomes: dict[tuple[int, int], dict[str, Any]],
    ) -> LocalSmokeEvidencePacket:
        """Build a reviewed packet from already-audited, bounded match facts."""
        return build_local_smoke_evidence_packet(
            specification, binding, audited_results, baseline_outcomes
        )

    def write_local_smoke_evidence_packet(
        self, packet: LocalSmokeEvidencePacket, report_directory: Path
    ) -> EvidencePacketWriteResult:
        """Write one reviewed immutable local packet once orchestration reaches it."""
        return write_local_smoke_evidence_packet(packet, report_directory)

    def inspect_local_smoke_evidence_packet_repeat(
        self, packet: LocalSmokeEvidencePacket, report_directory: Path
    ) -> EvidencePacketRepeatInspection:
        """Inspect a repeat destination without making it a reuse decision."""
        return inspect_local_smoke_evidence_packet_repeat(packet, report_directory)

    def complete_local_candidate_batch(
        self, batch: LocalCandidateBatch, report_directory: Path
    ) -> LocalCompletedRun:
        """Complete an already-audited batch without rerunning the evaluator."""
        return complete_local_candidate_batch(batch, report_directory)

    def run(self, request: LocalRunRequest) -> LocalCandidateBatch:
        """Run the exact approved candidate/seat batch with a clean audit each.

        Implementation sequence:

        1. Read the JSON specification at ``request.spec_path``.
        2. Validate it against schema v1.
        3. Bind explicitly to ``request.target_root`` and compare revision/hashes.
        4. Reject a lifecycle that does not authorize local execution.
        5. Validate the declared parameter, suite, and one-field candidate envelope.
        6. Plan and inspect the deterministic baseline-cache paths.
        7. Read and validate any present cache payload before reuse.
        8. Re-read each reusable cache immediately before execution and retain
           its baseline outcome for a later evidence-packet stage.
        9. For every declared candidate and planned seed/seat entry, run one
           fast checkpoint result and its matching clean audit.

        A missing, unreadable, or structurally invalid cache raises before a
        candidate helper can be reached. A candidate-evaluation or audit error
        stops the batch immediately: no later candidate, aggregate, packet, or
        policy decision is attempted here. The returned batch is intentionally
        not evidence-packet writing or interpretation.

        Each step needs its own tests and review. Do not skip directly to a
        simulator call, unbounded candidate generation, or a policy source edit.
        """
        specification = self.read_and_validate_spec(request.spec_path)
        binding = self.bind_and_validate_target(specification, request.target_root)
        lifecycle = self.authorize_lifecycle(specification)
        controls = self.validate_local_controls(specification, binding)
        cache_plan = self.plan_baseline_caches(
            specification, binding, request.cache_root
        )
        cache_state = self.inspect_baseline_cache_state(cache_plan)
        read_results = tuple(
            self.read_and_validate_baseline_cache(entry, specification, binding)
            for entry in cache_state.present_entries
        )
        preparation = self.plan_baseline_cache_preparation(cache_state, read_results)
        if preparation.materialize_actions:
            details = "; ".join(
                f"seed {action.entry.seed}, seat {action.entry.seat}: {action.reason}"
                for action in preparation.materialize_actions
            )
            raise BaselineCachePreparationError(
                "Candidate evaluation is blocked because every required baseline cache "
                f"must be reusable: {details}"
            )
        preflight = LocalRunPreflight(
            specification=specification,
            binding=binding,
            lifecycle=lifecycle,
            controls=controls,
            cache_plan=cache_plan,
            cache_preparation=preparation,
        )

        # Re-read at the execution boundary. A cache that changed after the
        # preflight is not silently trusted just because it passed earlier.
        baseline_outcomes: dict[tuple[int, int], dict[str, Any]] = {}
        for entry in cache_plan.entries:
            baseline_outcomes[(entry.seed, entry.seat)] = (
                self.read_validated_baseline_outcome(entry, specification, binding)
            )

        audited_results: list[dict[str, Any]] = []
        for candidate_value in specification["parameter"]["candidate_values"]:
            for entry in cache_plan.entries:
                # This reviewed order is the entire approved envelope. No search,
                # retry, or result-dependent expansion is possible in this loop.
                audited_results.append(
                    self.evaluate_and_audit_declared_candidate(
                        specification, binding, entry, candidate_value
                    )
                )
        return LocalCandidateBatch(
            preflight=preflight,
            baseline_outcomes=baseline_outcomes,
            audited_results=tuple(audited_results),
        )


def build_cli_parser() -> argparse.ArgumentParser:
    """Build the deliberately small CLI; no command can invoke the simulator."""
    parser = argparse.ArgumentParser(
        description=(
            "Inspect bounded Carrot Tuning contracts without running the simulator. "
            "There is intentionally no broad run or materialize command."
        )
    )
    commands = parser.add_subparsers(dest="command", required=True)

    preflight = commands.add_parser(
        "preflight", help="Read/schema-check a contract and optionally validate its target."
    )
    preflight.add_argument(
        "spec_path",
        type=Path,
        help="Path to the source-controlled experiment JSON specification.",
    )
    preflight.add_argument(
        "--target-root",
        type=Path,
        help="Optionally bind and fingerprint this Kaggriculture checkout after schema validation.",
    )

    baseline_plan = commands.add_parser(
        "baseline-plan",
        help="Fully gate and select at most one baseline action; never materialize it.",
    )
    baseline_plan.add_argument(
        "spec_path",
        type=Path,
        help="Path to the source-controlled baseline-preparation specification.",
    )
    baseline_plan.add_argument(
        "--target-root",
        type=Path,
        required=True,
        help="Explicit Kaggriculture checkout to bind and fingerprint.",
    )
    baseline_plan.add_argument(
        "--cache-root",
        type=Path,
        required=True,
        help="Ignored local run root whose baseline-caches child is inspected only.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Expose only named, reviewed read-only evaluator boundaries.

    ``preflight`` reads and validates a contract, with optional target/control
    checks. ``baseline-plan`` additionally performs all baseline-preparation
    gates and selects at most one missing action. Neither command imports the
    simulator, creates a cache, evaluates a candidate, writes a packet, or
    changes source. Those side effects intentionally have no CLI mode yet.
    """
    parser = build_cli_parser()
    arguments = parser.parse_args(argv)

    adapter = LocalInnerLoopAdapter()
    try:
        specification = adapter.read_and_validate_spec(arguments.spec_path)
    except ExperimentSpecValidationError as error:
        print(f"Schema validation failed: {error}")
        return 1

    print(
        "Schema validation passed: "
        f"{specification['experiment_id']} (schema v{specification['schema_version']})"
    )
    if arguments.command == "baseline-plan":
        request = LocalRunRequest(
            spec_path=arguments.spec_path,
            target_root=arguments.target_root,
            cache_root=arguments.cache_root,
            # The planner never consults this field. It remains explicit because
            # the shared request model is also used by later source boundaries.
            report_directory=Path("unused-by-baseline-plan"),
        )
        try:
            selection = adapter.plan_baseline_preparation(request)
        except ExperimentSpecValidationError as error:
            print(f"Baseline-preparation plan refused: {error}")
            return 1
        action = selection.selected_action
        if action is None:
            print("Baseline-preparation plan passed: every required cache is reusable.")
        else:
            print(
                "Baseline-preparation plan passed: selected one missing action "
                f"(seed {action.entry.seed}, seat {action.entry.seat})."
            )
        print("Stopped after planning; no cache was created and no simulator was invoked.")
        return 0

    binding = None
    if arguments.target_root is not None:
        try:
            binding = adapter.bind_and_validate_target(specification, arguments.target_root)
        except TargetFingerprintMismatchError as error:
            print(f"Target fingerprint validation failed: {error}")
            return 1
        print(f"Target fingerprint passed: {binding.root}")
    try:
        authorization = adapter.authorize_lifecycle(specification)
    except LifecycleAuthorizationError as error:
        print(f"Lifecycle authorization failed: {error}")
        return 1
    print(f"Lifecycle authorization passed: {authorization.declared_status}")
    if binding is not None:
        try:
            adapter.validate_local_controls(specification, binding)
        except LocalControlValidationError as error:
            print(f"Local-control validation failed: {error}")
            return 1
        print("Local-control validation passed.")
        print("Stopped after local-control validation; baseline-cache creation and simulation are absent.")
    else:
        print("Stopped after lifecycle authorization; target and local-control validation were not requested.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
