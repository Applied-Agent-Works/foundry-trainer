"""Explicit adapter for the Kaggriculture TOMATO teaching policy."""

from .adapters import PolicyAdapter


TOMATO_ADAPTER = PolicyAdapter(
    adapter_id="tomato-v1",
    shared_relative_path="agents/tomato/shared.py",
    policy_id="target.agents.tomato.shared.tomato_decision_agent",
    opponent_id="target.agents.tomato.shared.tomato_conveyor_agent",
    policy_attribute="tomato_decision_agent",
    opponent_attribute="tomato_conveyor_agent",
    parameter_relative_path="agents/ongoing_crop.py",
    parameter_type_attribute="OngoingCropParameters",
    default_parameters_attribute="DEFAULT_ONGOING_PARAMETERS",
    decision_mode="helper",
    opponent_mode="helper",
    crop_constant_attribute="TOMATO",
)
