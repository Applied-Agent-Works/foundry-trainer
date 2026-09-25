"""Explicit adapter for the Kaggriculture WHEAT teaching policy."""

from .adapters import PolicyAdapter


WHEAT_ADAPTER = PolicyAdapter(
    adapter_id="wheat-v1",
    shared_relative_path="agents/wheat/shared.py",
    policy_id="target.agents.wheat.shared.wheat_decision_agent",
    opponent_id="target.agents.wheat.shared.wheat_conveyor_agent",
    policy_attribute="wheat_decision_agent",
    opponent_attribute="wheat_conveyor_agent",
    parameter_relative_path="agents/one_time_crop.py",
    parameter_type_attribute="PointPriceParameters",
    default_parameters_attribute="DEFAULT_POINT_PRICE_PARAMETERS",
    decision_mode="helper",
    opponent_mode="helper",
    crop_constant_attribute="WHEAT",
)

