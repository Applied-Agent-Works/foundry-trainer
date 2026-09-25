"""Explicit adapter for the Kaggriculture STRAWBERRY teaching policy."""

from .adapters import PolicyAdapter


STRAWBERRY_ADAPTER = PolicyAdapter(
    adapter_id="strawberry-v1",
    shared_relative_path="agents/strawberry/shared.py",
    policy_id="target.agents.strawberry.shared.strawberry_decision_agent",
    opponent_id="target.agents.strawberry.shared.strawberry_conveyor_agent",
    policy_attribute="strawberry_decision_agent",
    opponent_attribute="strawberry_conveyor_agent",
    parameter_relative_path="agents/ongoing_crop.py",
    parameter_type_attribute="OngoingCropParameters",
    default_parameters_attribute="DEFAULT_ONGOING_PARAMETERS",
    decision_mode="helper",
    opponent_mode="helper",
    crop_constant_attribute="STRAWBERRY",
)
