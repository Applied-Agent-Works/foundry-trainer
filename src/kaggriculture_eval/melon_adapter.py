"""Explicit adapter for the Kaggriculture MELON teaching policy."""

from .adapters import PolicyAdapter


MELON_ADAPTER = PolicyAdapter(
    adapter_id="melon-v1",
    shared_relative_path="agents/melon/shared.py",
    policy_id="target.agents.melon.shared.melon_decision_agent",
    opponent_id="target.agents.melon.shared.melon_conveyor_agent",
    policy_attribute="melon_decision_agent",
    opponent_attribute="melon_conveyor_agent",
    parameter_relative_path="agents/one_time_crop.py",
    parameter_type_attribute="PointPriceParameters",
    default_parameters_attribute="DEFAULT_POINT_PRICE_PARAMETERS",
    decision_mode="helper",
    opponent_mode="helper",
    crop_constant_attribute="MELON",
)

